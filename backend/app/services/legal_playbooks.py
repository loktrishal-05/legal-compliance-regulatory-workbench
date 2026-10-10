"""Versioned synthetic/owner-authored playbooks; exact independent approval is mandatory."""
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select
from app.db.models.legal_contract import Playbook, PlaybookRule
from app.services import legal_review
from app.services.canonicalization import canonical_hash
from app.services.legal_contracts import ContractConflict, audit, scope
from app.services.legal_policy import LegalAccessDenied, ROLE_OPERATIONS, authorize_workspace


def authorize_target(db, ctx, target_id):
    row = db.scalar(select(Playbook).where(Playbook.id == target_id, Playbook.workspace_id == ctx.workspace_id,
        Playbook.organization_id == ctx.organization_id))
    if row is None:
        raise LegalAccessDenied()


def on_approve(db, review):
    row = db.get(Playbook, review.target_id)
    if row is None or row.workspace_id != review.workspace_id or row.revision_sha256 != review.target_revision_sha256 or row.owner_id != review.requester_id:
        raise ContractConflict("playbook_revision_mismatch")


legal_review.register_target("playbook", authorize=authorize_target, on_approve=on_approve)


def create(db, *, request, actor_id, workspace_id, current_terms_version):
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version)
    if "propose" not in ROLE_OPERATIONS[ctx.role]:
        raise LegalAccessDenied()
    data = request.model_dump(mode="json")
    digest = canonical_hash({"policy": "legal-playbook-v1", "request": data, "owner": str(actor_id)})
    row = db.scalar(select(Playbook).where(Playbook.workspace_id == workspace_id, Playbook.name == request.name,
        Playbook.version == request.version))
    if row and row.revision_sha256 != digest:
        raise ContractConflict("playbook_version_conflict")
    if row is None:
        row = Playbook(id=uuid4(), **scope(ctx), owner_id=actor_id, revision_sha256=digest,
            **request.model_dump(exclude={"rules"}))
        db.add(row)
        db.flush()
        for rule in request.rules:
            db.add(PlaybookRule(id=uuid4(), **scope(ctx), playbook_id=row.id, **rule.model_dump()))
        db.flush()
        audit(db, ctx, "playbook_proposed", row.id)
    review = legal_review.submit(db, workspace_id=workspace_id, target_type="playbook", target_id=row.id,
        target_revision_sha256=digest, requester_id=actor_id, idempotency_key="playbook:" + str(row.id),
        current_terms_version=current_terms_version)
    return {"playbook_id": row.id, "revision_sha256": digest, "review_id": review.id, "outcome": legal_review.status(db, review),
        "name": row.name, "version": row.version, "legal_basis": row.legal_basis, "jurisdiction": row.jurisdiction}


def approved_rules(db, *, actor_id, workspace_id, playbook_id, current_terms_version):
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version)
    authorize_target(db, ctx, playbook_id)
    row = db.get(Playbook, playbook_id)
    if not legal_review.is_approved(db, workspace_id=workspace_id, target_type="playbook", target_id=row.id,
        target_revision_sha256=row.revision_sha256):
        raise ContractConflict("playbook_not_approved")
    now = datetime.now(timezone.utc)
    start, end = row.effective_from, row.effective_until
    # SQLite fixture datetimes represent UTC, as in existing audit/review fixtures.
    start = start.replace(tzinfo=timezone.utc) if start and start.tzinfo is None else start
    end = end.replace(tzinfo=timezone.utc) if end and end.tzinfo is None else end
    if start and now < start or end and now >= end:
        raise ContractConflict("playbook_not_effective")
    return [{"rule_id": str(r.id), "playbook_id": str(row.id), "playbook_version": row.version,
        "clause_type": r.clause_type, "kind": r.kind, "pattern": r.pattern, "label": r.label}
        for r in db.scalars(select(PlaybookRule).where(PlaybookRule.playbook_id == row.id).order_by(PlaybookRule.id))]


def list_playbooks(db, *, actor_id, workspace_id, current_terms_version):
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version)
    return {"items": [{"playbook_id": r.id, "name": r.name, "version": r.version, "jurisdiction": r.jurisdiction,
        "legal_basis": r.legal_basis, "revision_sha256": r.revision_sha256, "outcome": "approved" if legal_review.is_approved(db,
            workspace_id=workspace_id, target_type="playbook", target_id=r.id, target_revision_sha256=r.revision_sha256) else "proposed"}
        for r in db.scalars(select(Playbook).where(Playbook.workspace_id == workspace_id,
            Playbook.organization_id == ctx.organization_id).limit(200))]}
