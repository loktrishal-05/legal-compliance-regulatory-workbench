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
from xml.parsers import expat
import zipfile
import zlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentVersion
from app.db.models.legal_scope import DocumentAccess, LegalDocumentScope, Matter, MatterAccess
from app.services.audit import append_event
from app.services.legal_policy import (
    CLASSIFICATIONS, ROLE_OPERATIONS, LegalAccessDenied, authorize_document, authorize_workspace,
)

INTAKE_POLICY = "legal-intake-v3"
MAX_BYTES = 25 * 1024 * 1024  # ponytail: fixed cap; make it a setting when a deployment needs another
DOCX_MAX_ENTRIES = 2000
DOCX_MAX_UNCOMPRESSED = 100 * 1024 * 1024
DOCX_MAX_RATIO = 100
DOCX_MAX_XML_BYTES = 16 * 1024 * 1024
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
    names = {i.filename for i in infos}
    if len({i.filename.casefold() for i in infos}) != len(infos):
        archive.close()
        raise IntakeRejected("ambiguous_archive")
    if len(infos) > DOCX_MAX_ENTRIES or sum(i.file_size for i in infos) > DOCX_MAX_UNCOMPRESSED:
        raise IntakeRejected("archive_limits")
    reasons = []
    for info in infos:
        parts = info.filename.split("/")
        if info.filename.startswith("/") or "\\" in info.filename or ".." in parts or ":" in parts[0]:
            raise IntakeRejected("unsafe_archive_path")
        if info.flag_bits & 0x1:
            raise IntakeRejected("encrypted_archive")
        if info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
            raise IntakeRejected("unsupported_archive_compression")
        if info.file_size and (not info.compress_size or info.file_size / info.compress_size > DOCX_MAX_RATIO):
            raise IntakeRejected("archive_limits")
        lower = info.filename.lower()
        if lower.endswith("vbaproject.bin"):
            raise IntakeRejected("macro_content")
        if lower.endswith(NESTED) or "/embeddings/" in lower:
            reasons.append("embedded_object")
    if not {"[Content_Types].xml", "word/document.xml"} <= names:
        raise IntakeRejected("malformed_docx")
    try:
        if archive.testzip() is not None:
            raise IntakeRejected("malformed_docx")
        for info in infos:
            if info.filename.lower().endswith((".xml", ".rels")):
                _inspect_xml(archive, info, reasons)
    except (zipfile.BadZipFile, OSError, EOFError, RuntimeError, NotImplementedError, zlib.error, expat.ExpatError):
        raise IntakeRejected("malformed_docx") from None
    finally:
        archive.close()
    return reasons


def _inspect_xml(archive: zipfile.ZipFile, info: zipfile.ZipInfo, reasons: list[str]) -> None:
    """Stream bounded XML; never resolve DTD/entities or interpret relationship text lexically."""
    if info.file_size > DOCX_MAX_XML_BYTES:
        raise IntakeRejected("archive_limits")
    parser = expat.ParserCreate()

    def reject_dtd(*args):
        raise IntakeRejected("malformed_docx")

    def element(name, attributes):
        if attributes.get("TargetMode", "").casefold() == "external":
            reasons.append("external_reference")
        content_type = attributes.get("ContentType", "").lower()
        if "macroenabled" in content_type or "vbaproject" in content_type:
            raise IntakeRejected("macro_content")

    parser.StartDoctypeDeclHandler = reject_dtd
    parser.EntityDeclHandler = reject_dtd
    parser.ExternalEntityRefHandler = reject_dtd
    parser.StartElementHandler = element
    with archive.open(info) as handle:
        total = 0
        while chunk := handle.read(64 * 1024):
            total += len(chunk)
            if total > DOCX_MAX_XML_BYTES:
                raise IntakeRejected("archive_limits")
            parser.Parse(chunk, False)
        parser.Parse(b"", True)


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
    if hashlib.sha256(data).hexdigest() != sha:
        raise IntakeIntegrityError("original bytes do not match their hash")
    relative = PurePosixPath("legal", "originals", str(organization_id), str(workspace_id), f"{sha}{EXTENSIONS[fmt]}")
    path = Path(data_root, *relative.parts)
    if path.exists() or path.is_symlink():
        _verify_original(path, sha)
        return relative.as_posix()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{sha}.{uuid4().hex}.tmp")
    try:
        with open(temporary, "xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, stat.S_IRUSR | stat.S_IRGRP)
        try:
            os.link(temporary, path)  # atomic create-only publication; never replace an original
        except FileExistsError:
            _verify_original(path, sha)
    finally:
        temporary.unlink(missing_ok=True)
    return relative.as_posix()


def _verify_original(path: Path, sha: str) -> bytes:
    try:
        if not stat.S_ISREG(path.lstat().st_mode):
            raise IntakeIntegrityError("stored original is not a regular file")
        with open(path, "rb") as handle:
            data = handle.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES or hashlib.sha256(data).hexdigest() != sha:
            raise IntakeIntegrityError("stored original does not match its hash")
        return data  # callers parse this exact verified snapshot, never a second file read
    except OSError:
        raise IntakeIntegrityError("stored original unavailable") from None


def _audit(db, event_type, ctx, **payload):
    append_event(db, event_type=event_type, actor_id=ctx.actor_id, actor_kind="user",
                 payload={"policy_version": INTAKE_POLICY, "organization_id": str(ctx.organization_id),
                          "workspace_id": str(ctx.workspace_id),
                          **{k: str(v) if isinstance(v, UUID) else v for k, v in payload.items()}})


def _authorize_intake(db, actor_id, workspace_id, classification, matter_id, current_terms_version):
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version)
    if "propose" not in ROLE_OPERATIONS[ctx.role]:
        raise LegalAccessDenied()
    if classification not in CLASSIFICATIONS or CLASSIFICATIONS[classification] > CLASSIFICATIONS[ctx.clearance]:
        raise LegalAccessDenied()
    if matter_id is not None:
        matter = db.get(Matter, matter_id)
        grant = db.get(MatterAccess, (matter_id, actor_id))
        if (matter is None or matter.workspace_id != workspace_id or not matter.is_active
                or grant is None or not grant.is_active):
            raise LegalAccessDenied()
    return ctx


def receive(db: Session, *, actor_id: UUID, workspace_id: UUID, filename: str, document_type: str,
            classification: str, data: bytes, current_terms_version: str, data_root: Path,
            matter_id: UUID | None = None, scanner: Scanner | None = None) -> IntakeResult:
    ctx = _authorize_intake(db, actor_id, workspace_id, classification, matter_id, current_terms_version)
    if not DOCUMENT_TYPE.match(document_type):
        raise IntakeRejected("invalid_document_type")
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
        document = db.get(Document, existing.document_id)
        relative = PurePosixPath("legal", "originals", str(ctx.organization_id), str(workspace_id),
                                f"{sha}{EXTENSIONS[inspection.fmt]}")
        if document.source_path != relative.as_posix() or document.checksum != sha:
            raise IntakeIntegrityError("original lineage does not match its version")
        _verify_original(Path(data_root, *relative.parts), sha)
        return IntakeResult(existing.document_id, existing.id, existing.status, True,
                            tuple(existing.ingestion_metadata.get("quarantine_reasons", ())))
    reasons = list(inspection.quarantine_reasons)
    if scanner is None:
        reasons.append("malware_scanner_not_configured")
        scan_outcome = "not_configured"
    else:
        try:
            clean, finding = scanner(data)
            if type(clean) is not bool or not isinstance(finding, str):
                clean, finding = False, "unavailable"
        except Exception:  # scanner boundary: preserve bytes in quarantine, never log raw errors
            clean, finding = False, "unavailable"
        scan_outcome = "clean" if clean else "unavailable" if finding == "unavailable" else "detected"
        if not clean:
            reasons.append(f"malware_scan:{scan_outcome}")
        db.expire_all()
        ctx = _authorize_intake(db, actor_id, workspace_id, classification, matter_id, current_terms_version)
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
                                                   "malware_scan": {"outcome": scan_outcome,
                                                       "policy": getattr(scanner, "policy_version", "injected-scanner")
                                                           if scanner else "not_configured"},
                                                   "received_by": str(actor_id)})
    db.add(version)
    db.add(DocumentAccess(organization_id=ctx.organization_id, workspace_id=workspace_id,
                          document_id=document.id, user_id=actor_id, operation="read"))  # uploader read only
    db.flush()
    _audit(db, "LEGAL_DOCUMENT_RECEIVED", ctx, document_id=document.id, version_id=version.id, source_sha256=sha,
           size_bytes=len(data), format=inspection.fmt, status=status, quarantine_reasons=reasons,
           malware_scan=version.ingestion_metadata["malware_scan"],
           matter_id=matter_id, uploader_grant="read")
    return IntakeResult(document.id, version.id, status, False, tuple(reasons))
