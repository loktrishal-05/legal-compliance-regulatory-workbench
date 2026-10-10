"""Scoped native/opt-in OCR extraction and exact immutable source resolver; caller commits."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentVersion
from app.db.models.legal_extraction import LegalExtraction, LegalSourceSpan
from app.schemas.legal_extraction import NativeArtifact
from app.services.audit import append_event
from app.services.legal_intake import EXTENSIONS, IntakeIntegrityError, _verify_original, inspect
from app.services.legal_policy import LegalAccessDenied, authorize_document

PARSER_POLICY = "legal-native-v1"
MAX_OUTPUT_BYTES = 8 * 1024 * 1024


class ExtractionBlocked(ValueError):
    """Current version is not eligible for extraction; quarantine is never released here."""


class ParserFailed(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class ExtractionResult:
    extraction_id: UUID
    status: str
    span_ids: tuple[UUID, ...]
    warnings: tuple[str, ...]


def run_parser(data: bytes, fmt: str, *, ocr: bool = False) -> dict:
    if sys.platform != "linux":
        raise ParserFailed("parser_runtime_unsupported")
    worker = Path(__file__).with_name("legal_parser_worker.py")
    # No inherited secrets/private .env, read-only input snapshot, fixed executable and format allowlist.
    if fmt not in EXTENSIONS:
        raise ParserFailed("unsupported_parser_format")
    if ocr and fmt != "pdf":
        raise ParserFailed("ocr_requires_pdf")
    with tempfile.TemporaryDirectory(prefix="legal-parser-") as cwd, tempfile.TemporaryFile() as output:
        try:
            completed = subprocess.run([sys.executable, "-I", "-B", str(worker), fmt] + (["--ocr"] if ocr else []), input=data,
                stdout=output, stderr=subprocess.DEVNULL, timeout=30 if ocr else 10, cwd=cwd,
                env={"LANG": "C.UTF-8", "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"})
        except subprocess.TimeoutExpired:
            raise ParserFailed("parser_timeout") from None
        except OSError:
            raise ParserFailed("parser_unavailable") from None
        if completed.returncode:
            raise ParserFailed("parser_failed")
        output.seek(0)
        encoded = output.read(MAX_OUTPUT_BYTES + 1)
        if len(encoded) > MAX_OUTPUT_BYTES:
            raise ParserFailed("parser_output_limit")
        try:
            result = NativeArtifact.model_validate_json(encoded)
            if result.source_sha256 != hashlib.sha256(data).hexdigest():
                raise ValueError("source hash mismatch")
            previous = 0
            for span in result.spans:
                if not previous <= span.start < span.end <= len(result.text):
                    raise ValueError("invalid source offset")
                previous = span.end
            if result.status == "ready" and (not result.spans or result.warnings):
                raise ValueError("unverified ready artifact")
            return result.model_dump()
        except (ValueError, UnicodeError):
            raise ParserFailed("parser_output_invalid") from None


def _result(db, artifact):
    ids = tuple(db.scalars(select(LegalSourceSpan.id).where(LegalSourceSpan.extraction_id == artifact.id)
                          .order_by(LegalSourceSpan.start)))
    return ExtractionResult(artifact.id, artifact.status, ids, tuple(artifact.warnings))


def _audit(db, ctx, version, event_type, **payload):
    append_event(db, event_type=event_type, actor_id=ctx.actor_id, actor_kind="user", payload={
        "organization_id": str(ctx.organization_id), "workspace_id": str(ctx.workspace_id),
        "document_id": str(version.document_id), "version_id": str(version.id),
        "source_sha256": version.source_sha256, "policy_version": PARSER_POLICY, **payload})


def process(db: Session, *, actor_id: UUID, workspace_id: UUID, document_id: UUID, version_id: UUID,
            current_terms_version: str, data_root: Path, ocr: bool = False) -> ExtractionResult:
    ctx = authorize_document(db, actor_id, workspace_id, document_id,
                             current_terms_version=current_terms_version, operation="propose")
    version = db.scalar(select(DocumentVersion).where(DocumentVersion.id == version_id,
        DocumentVersion.document_id == document_id, DocumentVersion.workspace_id == workspace_id,
        DocumentVersion.organization_id == ctx.organization_id).with_for_update()
        .execution_options(populate_existing=True))
    if version is None:
        raise LegalAccessDenied()
    if version.status == "quarantined" or version.ingestion_metadata.get("quarantine_reasons"):
        raise ExtractionBlocked("document_quarantined")
    policy = "legal-ocr-v1" if ocr else PARSER_POLICY
    existing = db.scalar(select(LegalExtraction).where(LegalExtraction.version_id == version_id,
                                                     LegalExtraction.policy_version == policy))
    eligible = {"received", "failed", "needs_verification", "ready"} if ocr else {"received", "failed"}
    if (existing is None and version.status not in eligible) or not version.ingestion_metadata.get("intake_policy"):
        raise ExtractionBlocked("document_not_received")
    document = db.get(Document, document_id)
    fmt = version.ingestion_metadata.get("format")
    if fmt not in EXTENSIONS:
        raise IntakeIntegrityError("unknown original format")
    if ocr and fmt != "pdf":
        raise ExtractionBlocked("ocr_requires_pdf")
    relative = PurePosixPath("legal", "originals", str(ctx.organization_id), str(workspace_id),
                            f"{version.source_sha256}{EXTENSIONS[fmt]}")
    if document.source_path != relative.as_posix() or document.checksum != version.source_sha256:
        raise IntakeIntegrityError("original lineage mismatch")
    data = _verify_original(Path(data_root, *relative.parts), version.source_sha256)
    inspection = inspect(data, document.filename)
    if inspection.fmt != fmt or inspection.quarantine_reasons:
        raise ExtractionBlocked("source_requires_quarantine")
    if existing is not None:
        return _result(db, existing)
    try:
        parsed = run_parser(data, fmt, ocr=True) if ocr else run_parser(data, fmt)
    except ParserFailed as error:
        authorize_document(db, actor_id, workspace_id, document_id,
                           current_terms_version=current_terms_version, operation="propose")
        version.status = document.ingestion_status = "failed"
        _audit(db, ctx, version, "LEGAL_EXTRACTION_FAILED", code=error.code, policy_version=policy)
        raise
    # Re-read current grants after expensive work; a revoked actor never persists or receives its text.
    authorize_document(db, actor_id, workspace_id, document_id,
                       current_terms_version=current_terms_version, operation="propose")
    artifact_id = uuid4()
    digest = hashlib.sha256(json.dumps(parsed, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    artifact = LegalExtraction(id=artifact_id, organization_id=ctx.organization_id, workspace_id=workspace_id,
        document_id=document_id, version_id=version_id, source_sha256=version.source_sha256,
        policy_version=policy, extractor=parsed["extractor"], status=parsed["status"], text=parsed["text"],
        artifact_sha256=digest, warnings=parsed["warnings"], actor_id=actor_id)
    db.add(artifact)
    db.flush()
    for item in parsed["spans"]:
        db.add(LegalSourceSpan(id=uuid4(), organization_id=ctx.organization_id, workspace_id=workspace_id,
                              extraction_id=artifact_id, **item))
    version.status = document.ingestion_status = parsed["status"]
    _audit(db, ctx, version, "LEGAL_DOCUMENT_EXTRACTED", extraction_id=str(artifact_id),
           policy_version=policy,
           artifact_sha256=digest, extractor=parsed["extractor"], status=parsed["status"],
           span_count=len(parsed["spans"]), warnings=parsed["warnings"])
    db.flush()
    return _result(db, artifact)


def resolve_span(db: Session, *, actor_id: UUID, workspace_id: UUID, document_id: UUID,
                 version_id: UUID, span_id: UUID, current_terms_version: str) -> dict:
    ctx = authorize_document(db, actor_id, workspace_id, document_id, current_terms_version=current_terms_version)
    row = db.execute(select(LegalSourceSpan, LegalExtraction).join(LegalExtraction,
        LegalExtraction.id == LegalSourceSpan.extraction_id).where(LegalSourceSpan.id == span_id,
            LegalExtraction.workspace_id == workspace_id, LegalExtraction.organization_id == ctx.organization_id,
            LegalExtraction.document_id == document_id, LegalExtraction.version_id == version_id)).one_or_none()
    if row is None:
        raise LegalAccessDenied()
    span, artifact = row
    if not 0 <= span.start < span.end <= len(artifact.text):
        raise IntakeIntegrityError("stored source offsets invalid")
    return {"span_id": span.id, "extraction_id": artifact.id, "document_id": artifact.document_id,
        "version_id": artifact.version_id, "source_sha256": artifact.source_sha256,
        "artifact_sha256": artifact.artifact_sha256, "quote": artifact.text[span.start:span.end],
        "start": span.start, "end": span.end, "locator": span.locator,
        "status": artifact.status, "warnings": artifact.warnings}
