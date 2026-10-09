"""Durable legal document jobs, worker tick, blank-region transcription and corrected-text projection.

The queue row is authoritative (no in-memory tasks). Workers claim with FOR UPDATE SKIP LOCKED and a
lease; extraction runs as the ORIGINAL actor through legal_extraction.process, which re-authorizes,
re-verifies the stored original hash and is idempotent per version/policy. Artifact, job state and the
legal.document.extracted outbox event commit together, so a crash before commit leaves a reclaimable lease.
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import DocumentVersion
from app.db.models.legal_correction import LegalCorrection, LegalCorrectionDecision
from app.db.models.legal_extraction import LegalExtraction, LegalSourceSpan
from app.db.models.legal_jobs import LegalJob, LegalRegionTranscription
from app.services import legal_events, legal_extraction, legal_review, legal_scheduler
from app.services.legal_intake import IntakeIntegrityError
from app.services.legal_policy import LegalAccessDenied, authorize_document

MAX_ACTIVE_JOBS_PER_WORKSPACE = 20  # ponytail: fixed backpressure cap; make it a setting per deployment tier
LEASE = timedelta(minutes=10)
PROFILES = {"extract": legal_extraction.PARSER_POLICY, "ocr": "legal-ocr-v1"}


class JobConflict(ValueError):
    pass


class JobQuotaExceeded(RuntimeError):
    pass


def _now():
    return datetime.now(timezone.utc)


def _terms():
    from app.core.config import settings
    return settings.current_terms_version


def submit(db: Session, *, actor_id: UUID, workspace_id: UUID, document_id: UUID, version_id: UUID,
           operation: str, idempotency_key: str, current_terms_version: str) -> LegalJob:
    if operation not in PROFILES or not 1 <= len(idempotency_key or "") <= 200:
        raise JobConflict("job_request_invalid")
    ctx = authorize_document(db, actor_id, workspace_id, document_id, current_terms_version=current_terms_version,
                             operation="propose")
    version = db.scalar(select(DocumentVersion).where(DocumentVersion.id == version_id,
        DocumentVersion.document_id == document_id, DocumentVersion.workspace_id == workspace_id,
        DocumentVersion.organization_id == ctx.organization_id))
    if version is None:
        raise LegalAccessDenied()
    existing = db.scalar(select(LegalJob).where(LegalJob.workspace_id == workspace_id, LegalJob.actor_id == actor_id,
                                                LegalJob.idempotency_key == idempotency_key))
    if existing:
        if (existing.version_id, existing.operation) != (version_id, operation):
            raise JobConflict("job_retry_conflict")
        return existing
    if version.status == "quarantined" or version.ingestion_metadata.get("quarantine_reasons"):
        raise legal_extraction.ExtractionBlocked("document_quarantined")
    active = db.scalar(select(LegalJob).where(LegalJob.version_id == version_id, LegalJob.operation == operation,
                                              LegalJob.state.in_(("queued", "running"))))
    if active:
        return active  # one active job per version/operation; duplicate submits join it
    count = db.scalar(select(func.count()).select_from(LegalJob).where(LegalJob.workspace_id == workspace_id,
                                                                     LegalJob.state.in_(("queued", "running"))))
    if count >= MAX_ACTIVE_JOBS_PER_WORKSPACE:
        raise JobQuotaExceeded("workspace_job_quota")
    job = LegalJob(id=uuid4(), organization_id=ctx.organization_id, workspace_id=workspace_id, document_id=document_id,
        version_id=version_id, source_sha256=version.source_sha256, actor_id=actor_id, operation=operation,
        profile=PROFILES[operation], idempotency_key=idempotency_key, state="queued", attempts=0, max_attempts=3)
    db.add(job)
    try:
        with db.begin_nested():
            db.flush()
    except IntegrityError:
        raise JobConflict("job_retry_conflict")
    legal_events.audit_activity(db, ctx, "job_submitted", job_id=str(job.id), document_id=str(document_id),
                                version_id=str(version_id), operation=operation, source_sha256=version.source_sha256)
    return job


def get(db: Session, *, actor_id: UUID, workspace_id: UUID, job_id: UUID, current_terms_version: str) -> LegalJob:
    job = db.scalar(select(LegalJob).where(LegalJob.id == job_id, LegalJob.workspace_id == workspace_id))
    if job is None:
        raise LegalAccessDenied()
    authorize_document(db, actor_id, workspace_id, job.document_id, current_terms_version=current_terms_version)
    return job


def claim(db: Session, *, worker_id: str, now: datetime | None = None) -> LegalJob | None:
    """Claim one due job (queued and due, or running with an expired lease). Commits the lease."""
    now = now or _now()
    while True:
        job = db.scalar(select(LegalJob).where(or_(
            and_(LegalJob.state == "queued", or_(LegalJob.next_retry_at.is_(None), LegalJob.next_retry_at <= now)),
            and_(LegalJob.state == "running", LegalJob.lease_expires_at <= now)))
            .order_by(LegalJob.created_at, LegalJob.id).limit(1).with_for_update(skip_locked=True))
        if job is None:
            db.rollback()
            return None
        if job.attempts < job.max_attempts:
            break
        # Crashed while running its final attempt: visible dead letter, never silently dropped.
        job.state, job.failure_code, job.finished_at = "dead_letter", job.failure_code or "lease_expired", now
        job.lease_owner = job.lease_expires_at = None
        db.commit()
    job.state, job.attempts, job.lease_owner, job.lease_expires_at = "running", job.attempts + 1, worker_id, now + LEASE
    db.commit()
    return job


def _finish(db, job_id, now, *, state, code=None, extraction_id=None, retry=False):
    job = db.scalar(select(LegalJob).where(LegalJob.id == job_id).with_for_update()
                    .execution_options(populate_existing=True))
    job.lease_owner = job.lease_expires_at = None
    job.failure_code = code
    if retry and job.attempts < job.max_attempts:
        job.state, job.next_retry_at = "queued", now + timedelta(seconds=30 * 2 ** job.attempts)
    else:
        job.state = "dead_letter" if retry else state
        job.extraction_id, job.finished_at = extraction_id, now
    return job


def execute(db: Session, job: LegalJob, *, data_root: Path, current_terms_version: str,
            now: datetime | None = None) -> LegalJob:
    now = now or _now()
    job_id, workspace_id, actor_id = job.id, job.workspace_id, job.actor_id
    try:
        version = db.get(DocumentVersion, job.version_id)
        if version is None or version.source_sha256 != job.source_sha256:
            raise IntakeIntegrityError("job source hash mismatch")
        result = legal_extraction.process(db, actor_id=actor_id, workspace_id=workspace_id,
            document_id=job.document_id, version_id=job.version_id, current_terms_version=current_terms_version,
            data_root=data_root, ocr=job.operation == "ocr")
        legal_events.emit(db, workspace_id=workspace_id, event_type="legal.document.extracted",
            payload={"job_id": str(job_id), "document_id": str(job.document_id), "version_id": str(job.version_id),
                     "extraction_id": str(result.extraction_id), "source_sha256": job.source_sha256,
                     "status": result.status, "actor_id": str(actor_id)},
            idempotency_key=f"extracted:{result.extraction_id}")
        done = _finish(db, job_id, now, state="succeeded", extraction_id=result.extraction_id)
        db.commit()
        return done
    except legal_extraction.ParserFailed as error:
        db.commit()  # failed version state + mandatory failure audit, exactly as the HTTP route keeps them
        done = _finish(db, job_id, now, state="failed", code=error.code, retry=True)
    except LegalAccessDenied:
        db.rollback()  # revoked while queued/running: nothing is persisted or released
        done = _finish(db, job_id, now, state="failed", code="actor_not_authorized")
    except legal_extraction.ExtractionBlocked as error:
        db.rollback()
        done = _finish(db, job_id, now, state="failed", code=str(error))
    except IntakeIntegrityError:
        db.rollback()
        done = _finish(db, job_id, now, state="failed", code="source_integrity_failed")
    except Exception as error:  # transient: bounded retry, then dead letter; only the class name is kept
        db.rollback()
        done = _finish(db, job_id, now, state="failed", code=type(error).__name__[:80], retry=True)
    db.commit()
    return done


def run_once(db: Session, *, worker_id: str, data_root: Path, current_terms_version: str,
             now: datetime | None = None, job_limit: int = 10) -> dict:
    """One worker tick: document jobs, then outbox dispatch, then due scheduler scans."""
    processed = 0
    while processed < job_limit:
        job = claim(db, worker_id=worker_id, now=now)
        if job is None:
            break
        execute(db, job, data_root=data_root, current_terms_version=current_terms_version, now=now)
        processed += 1
    events = legal_events.dispatch_due(db, worker_id=worker_id, now=now)
    scans = legal_scheduler.run_due(db, now)
    return {"jobs": processed, "events": events, "scans": scans}


# --- FR-011: blank-region manual transcription and corrected-text projection -------------------------

def _region_authorize(db, ctx, transcription_id):
    extraction_id = db.scalar(select(LegalRegionTranscription.extraction_id).where(
        LegalRegionTranscription.id == transcription_id, LegalRegionTranscription.workspace_id == ctx.workspace_id))
    document_id = extraction_id and db.scalar(select(LegalExtraction.document_id)
                                              .where(LegalExtraction.id == extraction_id))
    if document_id is None:
        raise LegalAccessDenied()
    authorize_document(db, ctx.actor_id, ctx.workspace_id, document_id, current_terms_version=_terms())


legal_review.register_target("region_transcription", authorize=_region_authorize)


def _extraction(db, ctx, document_id, version_id, extraction_id=None):
    query = select(LegalExtraction).where(LegalExtraction.workspace_id == ctx.workspace_id,
        LegalExtraction.organization_id == ctx.organization_id, LegalExtraction.document_id == document_id,
        LegalExtraction.version_id == version_id)
    if extraction_id:
        query = query.where(LegalExtraction.id == extraction_id)
    row = db.scalar(query.order_by(LegalExtraction.created_at.desc(), LegalExtraction.id).limit(1))
    if row is None:
        raise LegalAccessDenied()
    return row


def transcribe_region(db: Session, *, actor_id: UUID, workspace_id: UUID, document_id: UUID, version_id: UUID,
                      extraction_id: UUID, page: int, bbox: list[float], text: str, rationale: str,
                      idempotency_key: str, current_terms_version: str) -> LegalRegionTranscription:
    """Anchors manual text to an original page/region even when no extracted span exists. Never edits source."""
    ctx = authorize_document(db, actor_id, workspace_id, document_id, current_terms_version=current_terms_version,
                             operation="propose")
    artifact = _extraction(db, ctx, document_id, version_id, extraction_id)
    if not (len(bbox) == 4 and 0 <= bbox[0] < bbox[2] and 0 <= bbox[1] < bbox[3]) or not 1 <= page <= 10000:
        raise JobConflict("region_invalid")
    digest = hashlib.sha256(json.dumps({"extraction_id": str(artifact.id), "page": page, "bbox": bbox,
        "text": text, "rationale": rationale}, sort_keys=True).encode()).hexdigest()
    existing = db.scalar(select(LegalRegionTranscription).where(LegalRegionTranscription.workspace_id == workspace_id,
        LegalRegionTranscription.actor_id == actor_id, LegalRegionTranscription.idempotency_key == idempotency_key))
    if existing:
        if existing.transcription_sha256 != digest:
            raise JobConflict("transcription_retry_conflict")
        return existing
    row = LegalRegionTranscription(id=uuid4(), organization_id=ctx.organization_id, workspace_id=workspace_id,
        extraction_id=artifact.id, page=page, bbox=bbox, text=text, rationale=rationale, actor_id=actor_id,
        idempotency_key=idempotency_key, transcription_sha256=digest)
    db.add(row)
    db.flush()
    legal_events.audit_activity(db, ctx, "region_transcription_proposed", transcription_id=str(row.id),
        extraction_id=str(artifact.id), page=page, transcription_sha256=digest)
    return row


def projection(db: Session, *, actor_id: UUID, workspace_id: UUID, document_id: UUID, version_id: UUID,
               current_terms_version: str, extraction_id: UUID | None = None) -> dict:
    """Original text plus approved transcription overlays, each segment labelled; the original stays untouched."""
    ctx = authorize_document(db, actor_id, workspace_id, document_id, current_terms_version=current_terms_version)
    artifact = _extraction(db, ctx, document_id, version_id, extraction_id)
    spans = list(db.scalars(select(LegalSourceSpan).where(LegalSourceSpan.extraction_id == artifact.id)
                            .order_by(LegalSourceSpan.start)))
    approved = {}
    for correction in db.scalars(select(LegalCorrection).join(LegalCorrectionDecision,
            LegalCorrectionDecision.correction_id == LegalCorrection.id).where(
            LegalCorrection.extraction_id == artifact.id, LegalCorrectionDecision.outcome == "approved")
            .order_by(LegalCorrectionDecision.created_at, LegalCorrection.id)):
        approved[correction.span_id] = correction  # latest approved correction per span wins
    segments, cursor = [], 0
    for span in spans:
        if span.start > cursor:
            segments.append({"kind": "original", "text": artifact.text[cursor:span.start]})
        original = artifact.text[span.start:span.end]
        correction = approved.get(span.id)
        segments.append({"kind": "approved_correction" if correction else "original", "span_id": str(span.id),
            "text": correction.corrected_text if correction else original, "original_text": original,
            "correction_id": str(correction.id) if correction else None, "locator": span.locator})
        cursor = span.end
    if cursor < len(artifact.text):
        segments.append({"kind": "original", "text": artifact.text[cursor:]})
    regions = []
    for row in db.scalars(select(LegalRegionTranscription).where(LegalRegionTranscription.extraction_id == artifact.id)
                          .order_by(LegalRegionTranscription.page, LegalRegionTranscription.created_at)):
        if legal_review.is_approved(db, workspace_id=workspace_id, target_type="region_transcription",
                                    target_id=row.id, target_revision_sha256=row.transcription_sha256):
            regions.append({"kind": "approved_manual_transcription", "transcription_id": str(row.id),
                            "page": row.page, "bbox": row.bbox, "text": row.text})
    return {"label": "corrected_projection_not_original", "extraction_id": str(artifact.id),
            "source_sha256": artifact.source_sha256, "artifact_sha256": artifact.artifact_sha256,
            "original_text_sha256": hashlib.sha256(artifact.text.encode()).hexdigest(),
            "segments": segments, "manual_regions": regions,
            "text": "".join(segment["text"] for segment in segments)}
