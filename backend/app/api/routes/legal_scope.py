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
from app.services import legal_jobs
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
