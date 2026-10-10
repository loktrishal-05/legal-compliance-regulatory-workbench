"""Transcription review only; never rewrites source text or approves legal meaning. Caller commits."""
import hashlib
import json
from uuid import uuid4

from sqlalchemy import select

from app.db.models import DocumentVersion
from app.db.models.legal_correction import LegalCorrection, LegalCorrectionDecision
from app.db.models.legal_extraction import LegalExtraction
from app.services.audit import append_event
from app.services.legal_extraction import ExtractionBlocked, resolve_span
from app.services.legal_policy import LegalAccessDenied, authorize_document, authorize_workspace

POLICY = "legal-correction-v1"


class CorrectionConflict(ValueError):
    pass


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _audit(db, ctx, event, correction, **details):
    append_event(db, event_type=event, actor_id=ctx.actor_id, actor_kind="user", payload={
        "policy_version": POLICY, "organization_id": str(ctx.organization_id), "workspace_id": str(ctx.workspace_id),
        "correction_id": str(correction.id), "correction_sha256": correction.correction_sha256,
        "span_id": str(correction.span_id), "extraction_id": str(correction.extraction_id), **details})


def _load(db, actor_id, workspace_id, document_id, version_id, correction_id, terms, lock=False):
    ctx = authorize_document(db, actor_id, workspace_id, document_id, current_terms_version=terms)
    query = select(LegalCorrection).join(LegalExtraction, LegalExtraction.id == LegalCorrection.extraction_id).where(
        LegalCorrection.id == correction_id, LegalCorrection.workspace_id == workspace_id,
        LegalCorrection.organization_id == ctx.organization_id,
        LegalExtraction.document_id == document_id, LegalExtraction.version_id == version_id)
    row = db.scalar(query.with_for_update(of=LegalCorrection) if lock else query)
    if row is None:
        raise LegalAccessDenied()
    return row


def _response(db, row, actor_id, workspace_id, document_id, version_id, terms):
    source = resolve_span(db, actor_id=actor_id, workspace_id=workspace_id, document_id=document_id,
        version_id=version_id, span_id=row.span_id, current_terms_version=terms)
    if hashlib.sha256(source["quote"].encode()).hexdigest() != row.original_quote_sha256:
        raise CorrectionConflict("correction_source_mismatch")
    decision = db.scalar(select(LegalCorrectionDecision).where(LegalCorrectionDecision.correction_id == row.id))
    return {"correction_id": row.id, "correction_sha256": row.correction_sha256,
        "parent_correction_id": row.parent_correction_id, "span_id": row.span_id, "extraction_id": row.extraction_id,
        "document_id": document_id, "version_id": version_id, "source_sha256": source["source_sha256"],
        "original_quote": source["quote"], "corrected_text": row.corrected_text, "rationale": row.rationale,
        "locator": source["locator"], "actor_id": row.actor_id,
        "outcome": decision.outcome if decision else "proposed",
        "reviewer_id": decision.reviewer_id if decision else None,
        "review_rationale": decision.rationale if decision else None}


def _eligible(db, version_id, document_id, workspace_id):
    version = db.scalar(select(DocumentVersion).where(DocumentVersion.id == version_id,
        DocumentVersion.document_id == document_id, DocumentVersion.workspace_id == workspace_id).with_for_update()
        .execution_options(populate_existing=True))
    if version is None:
        raise LegalAccessDenied()
    if version.status == "quarantined" or version.ingestion_metadata.get("quarantine_reasons"):
        raise ExtractionBlocked("document_quarantined")


def propose(db, *, actor_id, workspace_id, document_id, version_id, span_id, request, current_terms_version):
    ctx = authorize_document(db, actor_id, workspace_id, document_id,
        current_terms_version=current_terms_version, operation="propose")
    _eligible(db, version_id, document_id, workspace_id)  # serializes retries within the exact source version
    source = resolve_span(db, actor_id=actor_id, workspace_id=workspace_id, document_id=document_id,
        version_id=version_id, span_id=span_id, current_terms_version=current_terms_version)
    quote_hash = hashlib.sha256(source["quote"].encode()).hexdigest()
    if quote_hash != request.expected_quote_sha256:
        raise CorrectionConflict("correction_source_mismatch")
    digest = _digest({"policy": POLICY, "span_id": str(span_id), "extraction_id": str(source["extraction_id"]),
        "original_quote_sha256": quote_hash, "request": request.model_dump(mode="json")})
    existing = db.scalar(select(LegalCorrection).where(LegalCorrection.workspace_id == workspace_id,
        LegalCorrection.actor_id == actor_id, LegalCorrection.idempotency_key == request.idempotency_key))
    if existing:
        if existing.correction_sha256 != digest:
            raise CorrectionConflict("correction_retry_conflict")
        return _response(db, existing, actor_id, workspace_id, document_id, version_id, current_terms_version)
    if request.parent_correction_id:
        parent = _load(db, actor_id, workspace_id, document_id, version_id, request.parent_correction_id,
                       current_terms_version)
        if parent.span_id != span_id:
            raise CorrectionConflict("correction_parent_mismatch")
    ctx = authorize_document(db, actor_id, workspace_id, document_id,
        current_terms_version=current_terms_version, operation="propose")
    row = LegalCorrection(id=uuid4(), organization_id=ctx.organization_id, workspace_id=workspace_id,
        span_id=span_id, extraction_id=source["extraction_id"], parent_correction_id=request.parent_correction_id,
        actor_id=actor_id, idempotency_key=request.idempotency_key, original_quote_sha256=quote_hash,
        correction_sha256=digest, corrected_text=request.corrected_text, rationale=request.rationale)
    db.add(row)
    db.flush()
    _audit(db, ctx, "LEGAL_CORRECTION_PROPOSED", row, source_sha256=source["source_sha256"])
    return _response(db, row, actor_id, workspace_id, document_id, version_id, current_terms_version)


def decide(db, *, actor_id, workspace_id, document_id, version_id, correction_id, request, current_terms_version):
    row = _load(db, actor_id, workspace_id, document_id, version_id, correction_id, current_terms_version, lock=True)
    _eligible(db, version_id, document_id, workspace_id)
    role = authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version).role
    operation = "review_compliance" if role == "compliance_reviewer" else "review_legal"
    ctx = authorize_document(db, actor_id, workspace_id, document_id, current_terms_version=current_terms_version,
                             operation=operation, requester_id=row.actor_id)
    existing = db.scalar(select(LegalCorrectionDecision).where(LegalCorrectionDecision.correction_id == row.id))
    if existing:
        if (existing.reviewer_id, existing.outcome, existing.rationale) != (actor_id, request.outcome, request.rationale):
            raise CorrectionConflict("correction_decision_conflict")
    else:
        db.add(LegalCorrectionDecision(id=uuid4(), organization_id=ctx.organization_id, workspace_id=workspace_id,
            correction_id=row.id, correction_sha256=row.correction_sha256, reviewer_id=actor_id,
            requester_id=row.actor_id,
            outcome=request.outcome, rationale=request.rationale))
        db.flush()
        _audit(db, ctx, "LEGAL_CORRECTION_DECIDED", row, outcome=request.outcome)
    authorize_document(db, actor_id, workspace_id, document_id, current_terms_version=current_terms_version,
                       operation=operation, requester_id=row.actor_id)
    return _response(db, row, actor_id, workspace_id, document_id, version_id, current_terms_version)


def get(db, *, actor_id, workspace_id, document_id, version_id, correction_id, current_terms_version):
    row = _load(db, actor_id, workspace_id, document_id, version_id, correction_id, current_terms_version)
    return _response(db, row, actor_id, workspace_id, document_id, version_id, current_terms_version)
