"""Secure legal document intake (Phase E1): validate, quarantine, preserve original, scope, audit.

Formats are detected from bytes, never trusted from the client. Rejected input is audited and not
stored. Accepted bytes are written once, content-addressed per workspace, read-only, and re-verified
by hash on reuse. Anything suspicious, or any upload without a configured malware scanner, stays
`quarantined` and is never parsed. Clean uploads are `received` and wait for extraction (E2).
The caller commits: state rows and audit events share one transaction.
"""
from dataclasses import dataclass
import hashlib
import io
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Callable
from uuid import UUID, uuid4
import zipfile

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentVersion
from app.db.models.legal_scope import DocumentAccess, LegalDocumentScope, Matter, MatterAccess
from app.services.audit import append_event
from app.services.legal_policy import (
    CLASSIFICATIONS, ROLE_OPERATIONS, LegalAccessDenied, authorize_document, authorize_workspace,
)

INTAKE_POLICY = "legal-intake-v1"
MAX_BYTES = 25 * 1024 * 1024  # ponytail: fixed cap; make it a setting when a deployment needs another
DOCX_MAX_ENTRIES = 2000
DOCX_MAX_UNCOMPRESSED = 100 * 1024 * 1024
DOCX_MAX_RATIO = 100
EXTENSIONS = {"pdf": ".pdf", "docx": ".docx", "txt": ".txt"}
PDF_ACTIVE = (b"/JavaScript", b"/JS", b"/Launch", b"/EmbeddedFile", b"/OpenAction", b"/AA", b"/RichMedia", b"/XFA")
NESTED = (".zip", ".docx", ".docm", ".xlsx", ".xlsm", ".pptx", ".jar", ".7z", ".rar", ".exe", ".dll", ".bin")
DOCUMENT_TYPE = re.compile(r"^[a-z][a-z0-9_]{1,49}$")
Scanner = Callable[[bytes], tuple[bool, str]]  # (clean, finding) from a configured malware scanner


class IntakeRejected(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class IntakeConflict(LookupError):
    """Same bytes already exist in this workspace in a document the actor cannot read."""


class IntakeIntegrityError(RuntimeError):
    """A stored original no longer matches its content address."""


@dataclass(frozen=True)
class Inspection:
    fmt: str
    quarantine_reasons: tuple[str, ...]


@dataclass(frozen=True)
class IntakeResult:
    document_id: UUID
    version_id: UUID
    status: str
    duplicate: bool
    quarantine_reasons: tuple[str, ...]


def safe_filename(filename: str) -> str:
    name = PurePosixPath(filename.replace("\\", "/")).name
    name = "".join(ch for ch in name if ch.isprintable()).strip()[:255]
    if not name or name in {".", ".."}:
        raise IntakeRejected("invalid_filename")
    return name


def _inspect_docx(data: bytes) -> list[str]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise IntakeRejected("malformed_docx") from None
    infos = archive.infolist()
    if len(infos) > DOCX_MAX_ENTRIES or sum(i.file_size for i in infos) > DOCX_MAX_UNCOMPRESSED:
        raise IntakeRejected("archive_limits")
    reasons = []
    for info in infos:
        parts = info.filename.split("/")
        if info.filename.startswith("/") or "\\" in info.filename or ".." in parts or ":" in parts[0]:
            raise IntakeRejected("unsafe_archive_path")
        if info.flag_bits & 0x1:
            raise IntakeRejected("encrypted_archive")
        if info.file_size and (not info.compress_size or info.file_size / info.compress_size > DOCX_MAX_RATIO):
            raise IntakeRejected("archive_limits")
        lower = info.filename.lower()
        if lower.endswith("vbaproject.bin"):
            raise IntakeRejected("macro_content")
        if lower.endswith(NESTED) or "/embeddings/" in lower:
            reasons.append("embedded_object")
    names = {i.filename for i in infos}
    if not {"[Content_Types].xml", "word/document.xml"} <= names:
        raise IntakeRejected("malformed_docx")
    try:
        if archive.testzip() is not None:
            raise IntakeRejected("malformed_docx")
        if any(b'TargetMode="External"' in archive.read(n) for n in names if n.endswith(".rels")):
            reasons.append("external_reference")
    except (zipfile.BadZipFile, OSError, EOFError, RuntimeError):
        raise IntakeRejected("malformed_docx") from None
    return reasons


def inspect(data: bytes, filename: str) -> Inspection:
    """Detect format from bytes; reject unsafe input, list reasons that require quarantine."""
    if not data:
        raise IntakeRejected("empty")
    if len(data) > MAX_BYTES:
        raise IntakeRejected("too_large")
    reasons = []
    if data.startswith(b"%PDF-"):
        fmt = "pdf"
        if b"%%EOF" not in data[-1024:]:
            raise IntakeRejected("malformed_pdf")
        reasons += [f"pdf_active_content:{m.decode()[1:]}" for m in PDF_ACTIVE if m in data]
        if b"/Encrypt" in data:
            reasons.append("encrypted_pdf")
        if b"PK\x03\x04" in data:
            reasons.append("embedded_archive")
    elif data.startswith(b"PK\x03\x04"):
        fmt = "docx"
        reasons += _inspect_docx(data)
    else:
        fmt = "txt"
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise IntakeRejected("unsupported_type") from None
        if any(ord(ch) < 32 and ch not in "\t\n\r\f" for ch in text):
            raise IntakeRejected("binary_content")
    if not safe_filename(filename).lower().endswith(EXTENSIONS[fmt]):
        raise IntakeRejected("type_mismatch")
    return Inspection(fmt, tuple(dict.fromkeys(reasons)))


def store_original(data_root: Path, organization_id: UUID, workspace_id: UUID, sha: str, fmt: str,
                   data: bytes) -> str:
    """Write-once content-addressed original; returns a data_root-relative POSIX path."""
    relative = PurePosixPath("legal", "originals", str(organization_id), str(workspace_id), f"{sha}{EXTENSIONS[fmt]}")
    path = Path(data_root, *relative.parts)
    if path.exists():
        if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            raise IntakeIntegrityError("stored original does not match its hash")
        return relative.as_posix()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{sha}.{uuid4().hex}.tmp")
    with open(temporary, "xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temporary, stat.S_IRUSR | stat.S_IRGRP)
    os.replace(temporary, path)
    return relative.as_posix()


def _audit(db, event_type, ctx, **payload):
    append_event(db, event_type=event_type, actor_id=ctx.actor_id, actor_kind="user",
                 payload={"policy_version": INTAKE_POLICY, "organization_id": str(ctx.organization_id),
                          "workspace_id": str(ctx.workspace_id),
                          **{k: str(v) if isinstance(v, UUID) else v for k, v in payload.items()}})


def receive(db: Session, *, actor_id: UUID, workspace_id: UUID, filename: str, document_type: str,
            classification: str, data: bytes, current_terms_version: str, data_root: Path,
            matter_id: UUID | None = None, scanner: Scanner | None = None) -> IntakeResult:
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version)
    if "propose" not in ROLE_OPERATIONS[ctx.role]:
        raise LegalAccessDenied()
    if classification not in CLASSIFICATIONS or CLASSIFICATIONS[classification] > CLASSIFICATIONS[ctx.clearance]:
        raise LegalAccessDenied()
    if not DOCUMENT_TYPE.match(document_type):
        raise IntakeRejected("invalid_document_type")
    if matter_id is not None:
        matter = db.get(Matter, matter_id)
        grant = db.get(MatterAccess, (matter_id, actor_id))
        if (matter is None or matter.workspace_id != workspace_id or not matter.is_active
                or grant is None or not grant.is_active):
            raise LegalAccessDenied()
    sha = hashlib.sha256(data).hexdigest()
    try:
        inspection = inspect(data, filename)
    except IntakeRejected as rejected:
        _audit(db, "LEGAL_INTAKE_REJECTED", ctx, code=rejected.code, size_bytes=len(data), source_sha256=sha)
        raise
    existing = db.scalar(select(DocumentVersion).where(
        DocumentVersion.organization_id == ctx.organization_id, DocumentVersion.workspace_id == workspace_id,
        DocumentVersion.source_sha256 == sha))
    if existing is not None:  # idempotent within the workspace; never across tenants
        try:
            authorize_document(db, actor_id, workspace_id, existing.document_id,
                               current_terms_version=current_terms_version)
        except LegalAccessDenied:
            raise IntakeConflict("duplicate_in_workspace") from None
        return IntakeResult(existing.document_id, existing.id, existing.status, True,
                            tuple(existing.ingestion_metadata.get("quarantine_reasons", ())))
    reasons = list(inspection.quarantine_reasons)
    if scanner is None:
        reasons.append("malware_scanner_not_configured")
    else:
        clean, finding = scanner(data)
        if not clean:
            reasons.append(f"malware_scan:{finding}")
    status = "quarantined" if reasons else "received"
    source_path = store_original(data_root, ctx.organization_id, workspace_id, sha, inspection.fmt, data)
    document = Document(id=uuid4(), filename=safe_filename(filename), document_type=document_type,
                        source_path=source_path, classification=classification, checksum=sha,
                        ingestion_status=status)
    db.add(document)
    db.flush()
    db.add(LegalDocumentScope(document_id=document.id, organization_id=ctx.organization_id,
                              workspace_id=workspace_id, matter_id=matter_id, classification=classification))
    db.flush()
    version = DocumentVersion(id=uuid4(), document_id=document.id, source_sha256=sha, status=status, chunk_count=0,
                              organization_id=ctx.organization_id, workspace_id=workspace_id, warnings=reasons,
                              ingestion_metadata={"intake_policy": INTAKE_POLICY, "format": inspection.fmt,
                                                  "size_bytes": len(data), "quarantine_reasons": reasons,
                                                  "received_by": str(actor_id)})
    db.add(version)
    db.add(DocumentAccess(organization_id=ctx.organization_id, workspace_id=workspace_id,
                          document_id=document.id, user_id=actor_id, operation="read"))  # uploader read only
    db.flush()
    _audit(db, "LEGAL_DOCUMENT_RECEIVED", ctx, document_id=document.id, version_id=version.id, source_sha256=sha,
           size_bytes=len(data), format=inspection.fmt, status=status, quarantine_reasons=reasons,
           matter_id=matter_id, uploader_grant="read")
    return IntakeResult(document.id, version.id, status, False, tuple(reasons))
