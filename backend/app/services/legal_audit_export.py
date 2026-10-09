"""Step 7 audit/reporting: workspace-filtered legal audit, recorded-vs-effective as-of snapshots, frozen evidence
packs and JSON findings exports. Denied objects are silently excluded (no counts); manifests are immutable and
integrity-hashed over canonical JSON. Caller commits.
"""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditEvent, DocumentVersion
from app.db.models.legal_extraction import LegalExtraction
from app.db.models.legal_obligations import LegalEvidencePack, LegalObligation
from app.db.models.legal_review import LegalReview
from app.services import legal_events, legal_review
from app.services.audit import verify_chain
from app.services.canonicalization import canonical_hash
from app.services.legal_policy import (LEGAL_AUDIT_EVENT_TYPES, LegalAccessDenied, authorize_document,
                                       authorize_workspace)

POLICY = "legal-evidence-pack-v1"
AUDIT_ROLES = {"auditor", "workspace_admin"}
FINDING_TARGETS = ("contract_finding", "compliance_finding")


def _terms():
    from app.core.config import settings
    return settings.current_terms_version


def _aware(value):
    return value if value is None or value.tzinfo else value.replace(tzinfo=timezone.utc)


def _auditor(db, actor_id, workspace_id, terms):
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=terms)
    if ctx.role not in AUDIT_ROLES:
        raise LegalAccessDenied()
    return ctx


def audit_events(db: Session, *, actor_id: UUID, workspace_id: UUID, event_type: str | None = None,
                 since: datetime | None = None, until: datetime | None = None, limit: int = 200,
                 current_terms_version: str | None = None) -> list[dict]:
    """Legal audit for ONE workspace (payload.workspace_id), auditor/workspace-admin only. Payloads hold IDs,
    hashes and codes by construction (never source text)."""
    terms = current_terms_version or _terms()
    _auditor(db, actor_id, workspace_id, terms)
    readable = {}

    def visible(event):
        """Document-bound events need a current read grant on that document (no existence leak via audit)."""
        for key in ("document_id", "requested_document_id"):
            document_id = (event.payload or {}).get(key)
            if document_id:
                if document_id not in readable:
                    try:
                        authorize_document(db, actor_id, workspace_id, UUID(document_id), current_terms_version=terms)
                        readable[document_id] = True
                    except (LegalAccessDenied, ValueError):
                        readable[document_id] = False
                if not readable[document_id]:
                    return False
        return True
    query = select(AuditEvent).where(AuditEvent.event_type.in_(LEGAL_AUDIT_EVENT_TYPES),
                                     AuditEvent.payload["workspace_id"].as_string() == str(workspace_id))
    if event_type:
        query = query.where(AuditEvent.event_type == event_type)
    if since:
        query = query.where(AuditEvent.occurred_at >= since)
    if until:
        query = query.where(AuditEvent.occurred_at <= until)
    rows = db.scalars(query.order_by(AuditEvent.sequence_number.desc()).limit(max(1, min(limit, 1000))))
    # ponytail: filter after LIMIT, so a page can be short; add keyset paging if auditors need full pages
    return [{"sequence_number": e.sequence_number, "event_type": e.event_type, "occurred_at": e.occurred_at,
             "actor_id": e.actor_id, "actor_kind": e.actor_kind, "payload": e.payload, "event_hash": e.event_hash}
            for e in rows if visible(e)]


def _review_state(db, review, as_of):
    decided = [d for d in legal_review.decisions(db, review.id) if _aware(d.created_at) <= as_of]
    terminal = [d for d in decided if d.decision != "escalate"]
    state = ({"approve": "approved", "reject": "rejected", "request_changes": "changes_requested"}[terminal[0].decision]
             if terminal else ("escalated" if decided else "pending"))
    return state, decided


def snapshot(db: Session, *, actor_id: UUID, workspace_id: UUID, as_of: datetime,
             current_terms_version: str | None = None) -> dict:
    """What the system RECORDED by `as_of` (reviews/decisions are immutable, so their state is exact),
    kept separate from EFFECTIVE time (human-confirmed obligation due dates)."""
    terms = current_terms_version or _terms()
    ctx = _auditor(db, actor_id, workspace_id, terms)
    if as_of.tzinfo is None:
        raise ValueError("as_of requires a timezone")
    reviews = []
    for review in db.scalars(select(LegalReview).where(LegalReview.workspace_id == workspace_id)
                             .order_by(LegalReview.created_at, LegalReview.id)):
        if _aware(review.created_at) > as_of:
            continue
        try:
            legal_review.get(db, workspace_id=workspace_id, review_id=review.id, actor_id=actor_id,
                             current_terms_version=terms)
        except LegalAccessDenied:
            continue
        state, decided = _review_state(db, review, as_of)
        reviews.append({"review_id": str(review.id), "target_type": review.target_type,
            "target_id": str(review.target_id), "target_revision_sha256": review.target_revision_sha256,
            "recorded_at": _aware(review.created_at).isoformat(), "state_as_of": state,
            "decisions": [{"decision": d.decision, "reviewer_id": str(d.reviewer_id),
                           "recorded_at": _aware(d.created_at).isoformat()} for d in decided]})
    obligations = []
    for row in db.scalars(select(LegalObligation).where(LegalObligation.workspace_id == workspace_id)):
        if _aware(row.created_at) > as_of:
            continue
        try:
            authorize_document(db, actor_id, workspace_id, row.document_id, current_terms_version=terms)
        except LegalAccessDenied:
            continue
        confirmed = row.confirmed_at is not None and _aware(row.confirmed_at) <= as_of
        obligations.append({"obligation_id": str(row.id), "recorded_at": _aware(row.created_at).isoformat(),
            "confirmed_as_of": confirmed, "effective_due_at": _aware(row.due_at).isoformat() if confirmed else None,
            "due_by_as_of": bool(confirmed and _aware(row.due_at) <= as_of)})
    last = db.scalars(select(AuditEvent.sequence_number).where(
        AuditEvent.event_type.in_(LEGAL_AUDIT_EVENT_TYPES), AuditEvent.occurred_at <= as_of,
        AuditEvent.payload["workspace_id"].as_string() == str(workspace_id))
        .order_by(AuditEvent.sequence_number.desc()).limit(1)).first()
    return {"as_of": as_of.isoformat(), "time_semantics": {"recorded": "system record time",
            "effective": "human-confirmed obligation due time"}, "workspace_id": str(ctx.workspace_id),
            "last_audit_sequence_as_of": last, "reviews": reviews, "obligations": obligations}


def _document_entry(db, actor_id, workspace_id, document_id, terms):
    ctx = authorize_document(db, actor_id, workspace_id, document_id, current_terms_version=terms)
    versions = []
    for version in db.scalars(select(DocumentVersion).where(DocumentVersion.document_id == document_id,
            DocumentVersion.workspace_id == workspace_id, DocumentVersion.organization_id == ctx.organization_id)
            .order_by(DocumentVersion.created_at, DocumentVersion.id)):
        extractions = db.scalars(select(LegalExtraction).where(LegalExtraction.version_id == version.id)
                                 .order_by(LegalExtraction.created_at, LegalExtraction.id))
        versions.append({"version_id": str(version.id), "source_sha256": version.source_sha256,
            "status": version.status, "extractions": [{"extraction_id": str(x.id), "policy_version": x.policy_version,
                "artifact_sha256": x.artifact_sha256, "status": x.status} for x in extractions]})
    return {"document_id": str(document_id), "versions": versions}


def _review_entry(db, actor_id, workspace_id, review_id, terms):
    review = legal_review.get(db, workspace_id=workspace_id, review_id=review_id, actor_id=actor_id,
                              current_terms_version=terms)
    return {"review_id": str(review.id), "target_type": review.target_type, "target_id": str(review.target_id),
            "target_revision_sha256": review.target_revision_sha256, "requester_id": str(review.requester_id),
            "status": legal_review.status(db, review),
            "decisions": [{"decision_id": str(d.id), "decision": d.decision, "reviewer_id": str(d.reviewer_id),
                           "rationale": d.rationale, "recorded_at": _aware(d.created_at).isoformat()}
                          for d in legal_review.decisions(db, review.id)]}


def _freeze(db, ctx, kind, body):
    manifest = {"policy_version": POLICY, "kind": kind, "workspace_id": str(ctx.workspace_id),
                "generated_by": str(ctx.actor_id), "generated_at": datetime.now(timezone.utc).isoformat(),
                "audit_chain_valid": bool(verify_chain(db).get("valid")), **body}
    digest = canonical_hash(manifest)
    row = LegalEvidencePack(id=uuid4(), organization_id=ctx.organization_id, workspace_id=ctx.workspace_id,
                            actor_id=ctx.actor_id, kind=kind, manifest=manifest, manifest_sha256=digest)
    db.add(row)
    db.flush()
    legal_events.audit_activity(db, ctx, f"{kind}_created", export_id=str(row.id), manifest_sha256=digest)
    return row


def create_evidence_pack(db: Session, *, actor_id: UUID, workspace_id: UUID, document_ids=(), review_ids=(),
                         current_terms_version: str | None = None) -> LegalEvidencePack:
    terms = current_terms_version or _terms()
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=terms)
    documents, reviews = [], []
    for document_id in list(dict.fromkeys(document_ids))[:200]:
        try:
            documents.append(_document_entry(db, actor_id, workspace_id, document_id, terms))
        except LegalAccessDenied:
            continue  # excluded without a trace: the pack never reveals that a denied object exists
    for review_id in list(dict.fromkeys(review_ids))[:200]:
        try:
            reviews.append(_review_entry(db, actor_id, workspace_id, review_id, terms))
        except LegalAccessDenied:
            continue
    return _freeze(db, ctx, "evidence_pack", {"documents": documents, "reviews": reviews})


def create_findings_export(db: Session, *, actor_id: UUID, workspace_id: UUID,
                           current_terms_version: str | None = None) -> LegalEvidencePack:
    """JSON export of finding reviews the actor may read; approval state comes from the immutable ledger only."""
    terms = current_terms_version or _terms()
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=terms)
    findings = []
    for review_id in db.scalars(select(LegalReview.id).where(LegalReview.workspace_id == workspace_id,
            LegalReview.target_type.in_(FINDING_TARGETS)).order_by(LegalReview.created_at, LegalReview.id)):
        try:
            findings.append(_review_entry(db, actor_id, workspace_id, review_id, terms))
        except LegalAccessDenied:
            continue
    return _freeze(db, ctx, "findings_export", {"findings": findings})


def get_export(db: Session, *, actor_id: UUID, workspace_id: UUID, export_id: UUID,
               current_terms_version: str | None = None) -> dict:
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version or _terms())
    row = db.scalar(select(LegalEvidencePack).where(LegalEvidencePack.id == export_id,
        LegalEvidencePack.workspace_id == workspace_id, LegalEvidencePack.organization_id == ctx.organization_id))
    if row is None or (row.actor_id != actor_id and ctx.role not in AUDIT_ROLES):
        raise LegalAccessDenied()
    return {"export_id": str(row.id), "kind": row.kind, "manifest": row.manifest,
            "manifest_sha256": row.manifest_sha256,
            "integrity_verified": canonical_hash(row.manifest) == row.manifest_sha256,
            "created_at": row.created_at}
