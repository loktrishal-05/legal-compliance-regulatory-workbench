"""Session/terms protected legal metadata and secure intake; never a provisioning endpoint."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.models import Document, User
from app.db.models.legal_scope import LegalDocumentScope, Workspace
from app.db.session import get_db
from app.schemas.legal_scope import IntakeResponse, LegalDocumentMetadata, WorkspaceMetadata
from app.schemas.legal_extraction import ExtractionResponse, SourceSpanResponse
from app.services import legal_intake
from app.services import legal_extraction
from app.services.legal_malware import configured_scanner
from app.services import legal_correction
from app.schemas.legal_correction import CorrectionRequest, CorrectionDecisionRequest, CorrectionResponse
from app.services.audit import append_event
from app.services.legal_policy import LegalAccessDenied, authorize_document, authorize_workspace
from app.services import legal_events, legal_jobs, legal_search
from app.db.models import DocumentVersion
from app.db.models.legal_extraction import LegalSourceSpan
from fastapi import Response
from app.schemas.legal_jobs import JobRequest, JobResponse, RegionTranscriptionRequest, RegionTranscriptionResponse

router = APIRouter(prefix="/v1/workspaces", tags=["legal scope"])


def unavailable(db: Session, actor_id: UUID, workspace_id: UUID, document_id: UUID | None = None,
                operation: str = "read"):
    # Requested IDs only, no source metadata/body or inferred tenant identity.
    append_event(db, event_type="SECURITY_POLICY_DENIED", actor_id=actor_id, actor_kind="user",
        payload={"policy_version": "legal-scope-v1", "requested_workspace_id": str(workspace_id),
                 "requested_document_id": str(document_id) if document_id else None, "operation": operation})
    db.commit()
    raise HTTPException(404, detail={"code": "legal_resource_unavailable"})


@router.get("")
def my_workspaces(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """The caller's own currently authorized workspaces (picker). Never lists other members or tenants."""
    from app.db.models.legal_scope import WorkspaceMembership
    items = []
    for workspace_id in db.scalars(select(WorkspaceMembership.workspace_id).where(
            WorkspaceMembership.user_id == user.id, WorkspaceMembership.is_active.is_(True))):
        try:
            context = authorize_workspace(db, user.id, workspace_id, current_terms_version=settings.current_terms_version)
        except LegalAccessDenied:
            continue
        name = db.scalar(select(Workspace.name).where(Workspace.id == workspace_id))
        items.append({"workspace_id": workspace_id, "organization_id": context.organization_id, "name": name,
                      "role": context.role})
    return {"items": sorted(items, key=lambda item: (item["name"] or "", str(item["workspace_id"])))}


@router.get("/{workspace_id}", response_model=WorkspaceMetadata)
def workspace_metadata(workspace_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        context = authorize_workspace(db, user.id, workspace_id, current_terms_version=settings.current_terms_version)
    except LegalAccessDenied:
        unavailable(db, user.id, workspace_id)
    row = db.execute(select(Workspace.id, Workspace.organization_id, Workspace.name)
                     .where(Workspace.id == context.workspace_id)).one()
    return WorkspaceMetadata(**row._mapping, role=context.role)


@router.get("/{workspace_id}/documents/{document_id}", response_model=LegalDocumentMetadata)
def document_metadata(workspace_id: UUID, document_id: UUID, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    try:
        authorize_document(db, user.id, workspace_id, document_id, current_terms_version=settings.current_terms_version)
    except LegalAccessDenied:
        unavailable(db, user.id, workspace_id, document_id)
    row = db.execute(select(
        Document.id, Document.filename, Document.document_type, Document.ingestion_status,
        LegalDocumentScope.workspace_id, LegalDocumentScope.matter_id, LegalDocumentScope.classification,
        LegalDocumentScope.legal_hold,
    ).join(LegalDocumentScope, LegalDocumentScope.document_id == Document.id)
        .where(Document.id == document_id, LegalDocumentScope.workspace_id == workspace_id)).one()
    return LegalDocumentMetadata(**row._mapping)


@router.post("/{workspace_id}/documents", response_model=IntakeResponse, status_code=201)
async def upload_document(workspace_id: UUID, request: Request,
                          filename: str = Query(..., min_length=1, max_length=255),
                          document_type: str = Query(..., min_length=2, max_length=50),
                          classification: str = Query(..., max_length=20),
                          matter_id: UUID | None = None,
                          db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Raw request body is the file. Bounded read; bytes decide the format, not the client."""
    declared = request.headers.get("content-length")
    if declared and (not declared.isdigit() or int(declared) > legal_intake.MAX_BYTES):
        raise HTTPException(413, detail={"code": "too_large"})
    body = bytearray()
    async for chunk in request.stream():
        body += chunk
        if len(body) > legal_intake.MAX_BYTES:
            raise HTTPException(413, detail={"code": "too_large"})

    def run():
        try:
            result = legal_intake.receive(
                db, actor_id=user.id, workspace_id=workspace_id, filename=filename, document_type=document_type,
                classification=classification, data=bytes(body), matter_id=matter_id,
                current_terms_version=settings.current_terms_version, data_root=settings.data_root,
                scanner=configured_scanner(settings))
        except LegalAccessDenied:
            unavailable(db, user.id, workspace_id, operation="intake")
        except legal_intake.IntakeRejected as rejected:
            db.commit()  # keep the rejection audit event
            raise HTTPException(422, detail={"code": rejected.code})
        except legal_intake.IntakeConflict:
            raise HTTPException(409, detail={"code": "duplicate_in_workspace"})
        db.commit()
        return IntakeResponse(document_id=result.document_id, version_id=result.version_id, status=result.status,
                              duplicate=result.duplicate, quarantine_reasons=list(result.quarantine_reasons))
    return await run_in_threadpool(run)


@router.post("/{workspace_id}/documents/{document_id}/versions/{version_id}/extractions",
             response_model=ExtractionResponse, status_code=201)
def extract_document(workspace_id: UUID, document_id: UUID, version_id: UUID,
                     ocr: bool = False,
                     db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        if ocr and not settings.legal_ocr_enabled:
            authorize_document(db, user.id, workspace_id, document_id,
                               current_terms_version=settings.current_terms_version, operation="propose")
            raise legal_extraction.ExtractionBlocked("ocr_not_configured")
        result = legal_extraction.process(db, actor_id=user.id, workspace_id=workspace_id,
            document_id=document_id, version_id=version_id, current_terms_version=settings.current_terms_version,
            data_root=settings.data_root, ocr=ocr)
    except LegalAccessDenied:
        db.rollback()
        unavailable(db, user.id, workspace_id, document_id, operation="extract")
    except legal_extraction.ExtractionBlocked as error:
        raise HTTPException(409, detail={"code": str(error)})
    except legal_extraction.ParserFailed as error:
        db.commit()  # failure state and mandatory failure audit share the caller's transaction
        raise HTTPException(422, detail={"code": error.code})
    except legal_intake.IntakeIntegrityError:
        raise HTTPException(409, detail={"code": "source_integrity_failed"})
    db.commit()
    return ExtractionResponse(extraction_id=result.extraction_id, status=result.status,
                              span_ids=list(result.span_ids), warnings=list(result.warnings))


@router.get("/{workspace_id}/documents/{document_id}/versions/{version_id}/spans/{span_id}",
            response_model=SourceSpanResponse)
def source_span(workspace_id: UUID, document_id: UUID, version_id: UUID, span_id: UUID,
                db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return legal_extraction.resolve_span(db, actor_id=user.id, workspace_id=workspace_id,
            document_id=document_id, version_id=version_id, span_id=span_id,
            current_terms_version=settings.current_terms_version)
    except LegalAccessDenied:
        unavailable(db, user.id, workspace_id, document_id, operation="source_span")
    except legal_intake.IntakeIntegrityError:
        raise HTTPException(409, detail={"code": "source_integrity_failed"})


def correction_command(db, user, workspace_id, document_id, call):
    try:
        result = call()
    except LegalAccessDenied:
        db.rollback()
        unavailable(db, user.id, workspace_id, document_id, operation="correction")
    except (legal_correction.CorrectionConflict, legal_extraction.ExtractionBlocked) as error:
        db.rollback()
        raise HTTPException(409, detail={"code": str(error)})
    except legal_intake.IntakeIntegrityError:
        db.rollback()
        raise HTTPException(409, detail={"code": "source_integrity_failed"})
    db.commit()
    return result


@router.post("/{workspace_id}/documents/{document_id}/versions/{version_id}/spans/{span_id}/corrections",
             response_model=CorrectionResponse, status_code=201)
def propose_correction(workspace_id: UUID, document_id: UUID, version_id: UUID, span_id: UUID,
                       request: CorrectionRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return correction_command(db, user, workspace_id, document_id, lambda: legal_correction.propose(db,
        actor_id=user.id, workspace_id=workspace_id, document_id=document_id, version_id=version_id, span_id=span_id,
        request=request, current_terms_version=settings.current_terms_version))


@router.post("/{workspace_id}/documents/{document_id}/versions/{version_id}/corrections/{correction_id}/decisions",
             response_model=CorrectionResponse, status_code=201)
def decide_correction(workspace_id: UUID, document_id: UUID, version_id: UUID, correction_id: UUID,
                      request: CorrectionDecisionRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return correction_command(db, user, workspace_id, document_id, lambda: legal_correction.decide(db,
        actor_id=user.id, workspace_id=workspace_id, document_id=document_id, version_id=version_id,
        correction_id=correction_id, request=request, current_terms_version=settings.current_terms_version))


@router.get("/{workspace_id}/documents/{document_id}/versions/{version_id}/corrections/{correction_id}",
            response_model=CorrectionResponse)
def read_correction(workspace_id: UUID, document_id: UUID, version_id: UUID, correction_id: UUID,
                    db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return correction_command(db, user, workspace_id, document_id, lambda: legal_correction.get(db,
        actor_id=user.id, workspace_id=workspace_id, document_id=document_id, version_id=version_id,
        correction_id=correction_id, current_terms_version=settings.current_terms_version))


def job_response(job) -> JobResponse:
    return JobResponse(job_id=job.id, document_id=job.document_id, version_id=job.version_id, operation=job.operation,
        profile=job.profile, state=job.state, attempts=job.attempts, max_attempts=job.max_attempts,
        failure_code=job.failure_code, extraction_id=job.extraction_id, next_retry_at=job.next_retry_at,
        created_at=job.created_at, finished_at=job.finished_at)


def job_command(db, user, workspace_id, document_id, call, operation):
    try:
        result = call()
    except LegalAccessDenied:
        db.rollback()
        unavailable(db, user.id, workspace_id, document_id, operation=operation)
    except (legal_jobs.JobConflict, legal_extraction.ExtractionBlocked) as error:
        db.rollback()
        raise HTTPException(409, detail={"code": str(error)})
    except legal_jobs.JobQuotaExceeded as error:
        db.rollback()
        raise HTTPException(429, detail={"code": str(error)})
    db.commit()
    return result


@router.post("/{workspace_id}/documents/{document_id}/versions/{version_id}/jobs", response_model=JobResponse,
             status_code=202)
def submit_job(workspace_id: UUID, document_id: UUID, version_id: UUID, request: JobRequest,
               db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    def call():
        if request.operation == "ocr" and not settings.legal_ocr_enabled:
            authorize_document(db, user.id, workspace_id, document_id,
                               current_terms_version=settings.current_terms_version, operation="propose")
            raise legal_extraction.ExtractionBlocked("ocr_not_configured")
        return job_response(legal_jobs.submit(db, actor_id=user.id, workspace_id=workspace_id, document_id=document_id,
            version_id=version_id, operation=request.operation, idempotency_key=request.idempotency_key,
            current_terms_version=settings.current_terms_version))
    return job_command(db, user, workspace_id, document_id, call, "job_submit")


@router.get("/{workspace_id}/jobs/{job_id}", response_model=JobResponse)
def read_job(workspace_id: UUID, job_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return job_command(db, user, workspace_id, None, lambda: job_response(legal_jobs.get(db, actor_id=user.id,
        workspace_id=workspace_id, job_id=job_id, current_terms_version=settings.current_terms_version)), "job_read")


@router.post("/{workspace_id}/documents/{document_id}/versions/{version_id}/region-transcriptions",
             response_model=RegionTranscriptionResponse, status_code=201)
def transcribe_region(workspace_id: UUID, document_id: UUID, version_id: UUID, request: RegionTranscriptionRequest,
                      db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    def call():
        row = legal_jobs.transcribe_region(db, actor_id=user.id, workspace_id=workspace_id, document_id=document_id,
            version_id=version_id, extraction_id=request.extraction_id, page=request.page, bbox=request.bbox,
            text=request.text, rationale=request.rationale, idempotency_key=request.idempotency_key,
            current_terms_version=settings.current_terms_version)
        return RegionTranscriptionResponse(transcription_id=row.id, extraction_id=row.extraction_id, page=row.page,
            bbox=row.bbox, text=row.text, transcription_sha256=row.transcription_sha256)
    return job_command(db, user, workspace_id, document_id, call, "region_transcription")


@router.get("/{workspace_id}/documents/{document_id}/versions/{version_id}/projection")
def corrected_projection(workspace_id: UUID, document_id: UUID, version_id: UUID, extraction_id: UUID | None = None,
                         db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Labelled corrected-text projection; never the original artifact and never replaces it."""
    return job_command(db, user, workspace_id, document_id, lambda: legal_jobs.projection(db, actor_id=user.id,
        workspace_id=workspace_id, document_id=document_id, version_id=version_id,
        current_terms_version=settings.current_terms_version, extraction_id=extraction_id), "projection")

def read_command(db, user, workspace_id, document_id, call, operation):
    try:
        return call()
    except LegalAccessDenied:
        db.rollback()
        unavailable(db, user.id, workspace_id, document_id, operation=operation)
    except legal_intake.IntakeIntegrityError:
        raise HTTPException(409, detail={"code": "source_integrity_failed"})
    except legal_extraction.ExtractionBlocked as error:
        raise HTTPException(409, detail={"code": str(error)})


def _context(db, user, workspace_id):
    return authorize_workspace(db, user.id, workspace_id, current_terms_version=settings.current_terms_version)


@router.get("/{workspace_id}/documents")
def list_documents(workspace_id: UUID, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0, le=100000),
                   matter_id: UUID | None = None, classification: str | None = Query(None, max_length=20),
                   status: str | None = Query(None, max_length=30), filename: str | None = Query(None, max_length=255),
                   db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Only currently readable documents; no totals (has_more is a page hint, not a count)."""
    def call():
        items = legal_search.list_documents(db, _context(db, user, workspace_id), limit=limit + 1, offset=offset,
            matter_id=matter_id, classification=classification, status=status, filename=filename,
            current_terms_version=settings.current_terms_version)
        return {"items": items[:limit], "has_more": len(items) > limit, "limit": limit, "offset": offset}
    return read_command(db, user, workspace_id, None, call, "document_list")


@router.get("/{workspace_id}/documents/{document_id}/versions")
def list_versions(workspace_id: UUID, document_id: UUID, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    def call():
        ctx = authorize_document(db, user.id, workspace_id, document_id,
                                 current_terms_version=settings.current_terms_version)
        rows = db.scalars(select(DocumentVersion).where(DocumentVersion.document_id == document_id,
            DocumentVersion.workspace_id == workspace_id, DocumentVersion.organization_id == ctx.organization_id)
            .order_by(DocumentVersion.created_at, DocumentVersion.id))
        return {"items": [{"version_id": v.id, "status": v.status, "source_sha256": v.source_sha256,
                           "format": v.ingestion_metadata.get("format"), "created_at": v.created_at,
                           "quarantine_reasons": v.ingestion_metadata.get("quarantine_reasons") or []} for v in rows]}
    return read_command(db, user, workspace_id, document_id, call, "version_list")


@router.get("/{workspace_id}/documents/{document_id}/versions/{version_id}/spans")
def list_spans(workspace_id: UUID, document_id: UUID, version_id: UUID, extraction_id: UUID | None = None,
               limit: int = Query(200, ge=1, le=2000), offset: int = Query(0, ge=0),
               db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    def call():
        ctx = authorize_document(db, user.id, workspace_id, document_id,
                                 current_terms_version=settings.current_terms_version)
        artifact = legal_jobs._extraction(db, ctx, document_id, version_id, extraction_id)
        spans = db.scalars(select(LegalSourceSpan).where(LegalSourceSpan.extraction_id == artifact.id)
                           .order_by(LegalSourceSpan.start).limit(limit + 1).offset(offset)).all()
        return {"extraction_id": artifact.id, "status": artifact.status, "source_sha256": artifact.source_sha256,
                "artifact_sha256": artifact.artifact_sha256, "warnings": artifact.warnings,
                "items": [{"span_id": sp.id, "start": sp.start, "end": sp.end, "locator": sp.locator,
                           "quote": artifact.text[sp.start:sp.end]} for sp in spans[:limit]],
                "has_more": len(spans) > limit}
    return read_command(db, user, workspace_id, document_id, call, "span_list")


MEDIA_TYPES = {"pdf": "application/pdf", "txt": "text/plain; charset=utf-8",
               "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


@router.get("/{workspace_id}/documents/{document_id}/versions/{version_id}/original")
def download_original(workspace_id: UUID, document_id: UUID, version_id: UUID, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    """Hash-verified original bytes as an attachment; quarantined bytes are never released here."""
    def call():
        return legal_jobs.original(db, actor_id=user.id, workspace_id=workspace_id, document_id=document_id,
            version_id=version_id, current_terms_version=settings.current_terms_version, data_root=settings.data_root)
    data, fmt, name, sha = read_command(db, user, workspace_id, document_id, call, "original_download")
    db.commit()
    return Response(content=data, media_type=MEDIA_TYPES[fmt], headers={
        "Content-Disposition": f"attachment; filename=\"{name}\"", "X-Content-Type-Options": "nosniff",
        "X-Source-SHA256": sha, "Cache-Control": "no-store"})


@router.get("/{workspace_id}/search")
def search(workspace_id: UUID, q: str = Query(..., min_length=1, max_length=200), limit: int = Query(20, ge=1, le=50),
           db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Authorized full-text span search; results only (no totals). Quote = exact stored span text."""
    return read_command(db, user, workspace_id, None, lambda: {"items": legal_search.search_spans(
        db, _context(db, user, workspace_id), q, limit, current_terms_version=settings.current_terms_version),
        "mode": "postgres_fulltext" if db.get_bind().dialect.name == "postgresql" else "substring"}, "search")
