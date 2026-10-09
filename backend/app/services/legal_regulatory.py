"""Governed manual registry; source content remains behind existing document policy."""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select

from app.db.models import DocumentVersion
from app.db.models.legal_extraction import LegalExtraction, LegalSourceSpan
from app.db.models.legal_regulatory import (RegulatorySource, RegulatoryDocument, RegulatoryVersion,
    RegulatoryChange, ApplicabilityDecision, RegulatoryWatchlist, RegulatoryCampaign)
from app.db.models.legal_scope import WorkspaceMembership
from app.services.audit import append_event
from app.services.canonicalization import canonical_hash
from app.services.legal_policy import LegalAccessDenied, ROLE_OPERATIONS, authorize_workspace, authorize_document
from app.services import legal_review, legal_events, legal_scheduler, legal_extraction
from app.services.legal_regulatory_projection import structural_changes, monitoring_status


class RegulatoryConflict(ValueError):
    pass


def context(db, actor_id, workspace_id, current_terms_version, *, write=False):
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version)
    if write and "propose" not in ROLE_OPERATIONS[ctx.role]:
        raise LegalAccessDenied()
    return ctx


def create_source(db, *, actor_id, workspace_id, request, current_terms_version):
    ctx = context(db, actor_id, workspace_id, current_terms_version, write=True)
    owner = db.scalar(select(WorkspaceMembership).where(WorkspaceMembership.organization_id == ctx.organization_id,
        WorkspaceMembership.workspace_id == workspace_id, WorkspaceMembership.user_id == request.owner_id,
        WorkspaceMembership.is_active.is_(True)))
    if owner is None:
        raise LegalAccessDenied()
    values = request.model_dump(mode="json")
    row = RegulatorySource(id=uuid4(), organization_id=ctx.organization_id, workspace_id=workspace_id,
        actor_id=actor_id, **request.model_dump(), revision_sha256=canonical_hash(values))
    db.add(row)
    append_event(db, event_type="LEGAL_ACTIVITY_RECORDED", actor_id=actor_id, actor_kind="user",
        payload={"organization_id": str(ctx.organization_id), "workspace_id": str(workspace_id),
                 "domain": "regulatory", "operation": "source_proposed", "source_id": str(row.id), "revision_sha256": row.revision_sha256})
    db.flush()
    return row


def scoped(db, model, ctx, object_id):
    row = db.scalar(select(model).where(model.id == object_id, model.organization_id == ctx.organization_id,
                                        model.workspace_id == ctx.workspace_id))
    if row is None:
        raise LegalAccessDenied()
    return row


def audit(db, ctx, operation, row):
    append_event(db, event_type="LEGAL_ACTIVITY_RECORDED", actor_id=ctx.actor_id, actor_kind="user",
        payload={"organization_id": str(ctx.organization_id), "workspace_id": str(ctx.workspace_id),
                 "domain": "regulatory", "operation": operation, "object_id": str(row.id)})


def create_document(db, *, actor_id, workspace_id, request, current_terms_version):
    ctx = context(db, actor_id, workspace_id, current_terms_version, write=True)
    scoped(db, RegulatorySource, ctx, request.source_id)
    row = RegulatoryDocument(id=uuid4(), organization_id=ctx.organization_id, workspace_id=workspace_id,
                             **request.model_dump())
    db.add(row)
    audit(db, ctx, "document_created", row)
    db.flush()
    return row


def approved(db, row, target):
    return legal_review.is_approved(db, workspace_id=row.workspace_id, target_type=target,
        target_id=row.id, target_revision_sha256=row.revision_sha256)


def import_version(db, *, actor_id, workspace_id, request, current_terms_version, data_root):
    ctx = context(db, actor_id, workspace_id, current_terms_version, write=True)
    document = scoped(db, RegulatoryDocument, ctx, request.regulatory_document_id)
    source = scoped(db, RegulatorySource, ctx, document.source_id)
    if source.trust_state != "approved" or not approved(db, source, "regulatory_source"):
        raise LegalAccessDenied()
    # Intake and extraction own byte verification, scanner quarantine and immutable source storage.
    artifact = scoped(db, LegalExtraction, ctx, request.extraction_id)
    if (artifact.document_id, artifact.version_id) != (request.document_id, request.version_id):
        raise LegalAccessDenied()
    legal_extraction.process(db, actor_id=actor_id, workspace_id=workspace_id,
        document_id=request.document_id, version_id=request.version_id, current_terms_version=current_terms_version,
        data_root=data_root, ocr=artifact.policy_version == "legal-ocr-v1")
    for parent in (request.amends_id, request.supersedes_id):
        if parent and scoped(db, RegulatoryVersion, ctx, parent).regulatory_document_id != document.id:
            raise LegalAccessDenied()
    existing = db.scalar(select(RegulatoryVersion).where(RegulatoryVersion.regulatory_document_id == document.id,
                                                        RegulatoryVersion.version_id == request.version_id))
    if existing:
        if any(getattr(existing, key) != value for key, value in request.model_dump().items()):
            raise RegulatoryConflict("regulatory_version_retry_conflict")
        return existing
    now = datetime.now(timezone.utc)
    row = RegulatoryVersion(id=uuid4(), organization_id=ctx.organization_id, workspace_id=workspace_id,
        actor_id=actor_id, source_sha256=artifact.source_sha256, imported_at=now, **request.model_dump())
    db.add(row)
    source.last_success_at = source.last_check_at = now
    audit(db, ctx, "version_imported", row)
    db.flush()
    return row


def authorize_version(db, ctx, row, terms, operation="read", requester_id=None):
    authorize_document(db, ctx.actor_id, ctx.workspace_id, row.document_id, current_terms_version=terms,
                       operation=operation, requester_id=requester_id)
    version = db.get(DocumentVersion, row.version_id)
    if version is None or version.status == "quarantined":
        raise LegalAccessDenied()


def sections(db, ctx, row, terms):
    authorize_version(db, ctx, row, terms)
    spans = db.scalars(select(LegalSourceSpan).where(LegalSourceSpan.extraction_id == row.extraction_id)
                      .order_by(LegalSourceSpan.start)).all()
    result, citations = [], []
    for index, span in enumerate(spans):
        citation = legal_extraction.resolve_span(db, actor_id=ctx.actor_id, workspace_id=ctx.workspace_id,
            document_id=row.document_id, version_id=row.version_id, span_id=span.id, current_terms_version=terms)
        # shortcut: locator/ordinal is structural identity; add reviewed section IDs for complex layouts.
        ref = str(span.locator.get("section", span.locator.get("line", index + 1)))
        result.append((ref, citation["quote"]))
        citations.append({k: str(v) if isinstance(v, UUID) else v for k, v in citation.items()})
    return result, citations


def create_change(db, *, actor_id, workspace_id, request, current_terms_version):
    ctx = context(db, actor_id, workspace_id, current_terms_version, write=True)
    old, new = [scoped(db, RegulatoryVersion, ctx, ident) for ident in (request.from_version_id, request.to_version_id)]
    if old.id == new.id or old.regulatory_document_id != new.regulatory_document_id:
        raise RegulatoryConflict("regulatory_change_versions_invalid")
    old_sections, old_citations = sections(db, ctx, old, current_terms_version)
    new_sections, new_citations = sections(db, ctx, new, current_terms_version)
    existing = db.scalar(select(RegulatoryChange).where(RegulatoryChange.from_version_id == old.id,
                                                       RegulatoryChange.to_version_id == new.id))
    if existing:
        return existing
    exact = structural_changes(old_sections, new_sections)
    proposal = {"kind": "observation", "profile": "regulatory-exact-v1", "review_required": True,
        "text": "Exact source differences require human materiality and applicability review.",
        "citations": old_citations + new_citations, "uncertainties": ["No semantic legal interpretation performed."]}
    row = RegulatoryChange(id=uuid4(), organization_id=ctx.organization_id, workspace_id=workspace_id,
        regulatory_document_id=old.regulatory_document_id, actor_id=actor_id, **request.model_dump(),
        exact_diff=exact, semantic_proposal=proposal, revision_sha256=canonical_hash({"diff": exact, "proposal": proposal}))
    db.add(row)
    audit(db, ctx, "change_proposed", row)
    db.flush()
    return row


def create_applicability(db, *, actor_id, workspace_id, request, current_terms_version):
    ctx = context(db, actor_id, workspace_id, current_terms_version, write=True)
    version = scoped(db, RegulatoryVersion, ctx, request.regulatory_version_id)
    authorize_version(db, ctx, version, current_terms_version, operation="propose")
    row = ApplicabilityDecision(id=uuid4(), organization_id=ctx.organization_id, workspace_id=workspace_id,
        actor_id=actor_id, **request.model_dump(), revision_sha256=canonical_hash(request.model_dump(mode="json")))
    db.add(row)
    audit(db, ctx, "applicability_proposed", row)
    db.flush()
    return row


def create_watchlist(db, *, actor_id, workspace_id, request, current_terms_version):
    ctx = context(db, actor_id, workspace_id, current_terms_version, write=True)
    scoped(db, RegulatorySource, ctx, request.source_id)
    existing = db.scalar(select(RegulatoryWatchlist).where(RegulatoryWatchlist.source_id == request.source_id,
                                                          RegulatoryWatchlist.owner_id == actor_id))
    if existing:
        if existing.max_age_days != request.max_age_days:
            raise RegulatoryConflict("watchlist_retry_conflict")
        return existing
    row = RegulatoryWatchlist(id=uuid4(), organization_id=ctx.organization_id, workspace_id=workspace_id,
                             owner_id=actor_id, **request.model_dump())
    db.add(row)
    audit(db, ctx, "watchlist_created", row)
    db.flush()
    return row


TARGET_MODELS = {"regulatory_source": RegulatorySource, "regulatory_change": RegulatoryChange,
                 "regulatory_applicability": ApplicabilityDecision}


def _authorize_target(db, ctx, target_id, target):
    row = scoped(db, TARGET_MODELS[target], ctx, target_id)
    terms = legal_review._terms()
    ids = ([row.from_version_id, row.to_version_id] if target == "regulatory_change" else
           [row.regulatory_version_id] if target == "regulatory_applicability" else [])
    for ident in ids:
        authorize_version(db, ctx, scoped(db, RegulatoryVersion, ctx, ident), terms)


def _on_approve(db, review):
    row = db.get(TARGET_MODELS[review.target_type], review.target_id)
    if row is None or (row.workspace_id, row.actor_id, row.revision_sha256) != (
            review.workspace_id, review.requester_id, review.target_revision_sha256):
        raise LegalAccessDenied()
    decisions = legal_review.decisions(db, review.id)
    decision = next((d for d in decisions if d.decision == "approve"), None)
    if decision is None:
        raise LegalAccessDenied()
    ctx = context(db, decision.reviewer_id, review.workspace_id, legal_review._terms())
    ids = ([row.from_version_id, row.to_version_id] if review.target_type == "regulatory_change" else
           [row.regulatory_version_id] if review.target_type == "regulatory_applicability" else [])
    for ident in ids:
        version = scoped(db, RegulatoryVersion, ctx, ident)
        authorize_version(db, ctx, version, legal_review._terms(), "review_compliance", row.actor_id)
        if review.target_type == "regulatory_applicability" and (version.effective_from is None or
                row.effective_on < version.effective_from or
                (version.effective_until is not None and row.effective_on >= version.effective_until)):
            raise RegulatoryConflict("applicability_effectivity_needs_verification")
    if review.target_type == "regulatory_source":
        row.trust_state = "approved"
    elif review.target_type == "regulatory_change":
        legal_events.emit(db, workspace_id=row.workspace_id, event_type="legal.regulatory.change_accepted",
            payload={"change_id": str(row.id), "from_version_id": str(row.from_version_id),
                     "to_version_id": str(row.to_version_id)}, idempotency_key=str(row.id))
        if db.scalar(select(RegulatoryCampaign.id).where(RegulatoryCampaign.change_id == row.id)) is None:
            db.add(RegulatoryCampaign(id=uuid4(), organization_id=row.organization_id,
                workspace_id=row.workspace_id, change_id=row.id, affected=[]))
    audit(db, ctx, "review_approved", row)


def scan_freshness(db, now):
    count = 0
    for watch, source in db.execute(select(RegulatoryWatchlist, RegulatorySource).join(RegulatorySource,
            RegulatorySource.id == RegulatoryWatchlist.source_id)):
        state = monitoring_status(now, watch.max_age_days, source.last_success_at, source.last_failure_at)
        if state["freshness"] != "fresh":
            legal_events.emit(db, workspace_id=watch.workspace_id, event_type="legal.regulatory.source_stale",
                payload={"watchlist_id": str(watch.id), "source_id": str(source.id), **state},
                idempotency_key=f"{watch.id}:{now.date()}:{state['freshness']}")
            count += 1
    return count


for _target in TARGET_MODELS:
    legal_review.register_target(_target, on_approve=_on_approve, operation="review_compliance",
        authorize=lambda db, ctx, ident, target=_target: _authorize_target(db, ctx, ident, target))
legal_scheduler.register_scan("regulatory_source_freshness", scan_freshness)
