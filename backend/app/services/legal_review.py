"""Exact-revision independent review ledger shared by every legal pillar. Caller commits.

Reviewer != requester; reviewer needs current scoped review permission plus server-owned
reviewer/admin platform eligibility (legal_policy); escalate never approves; approval binds
the exact target revision hash; registered on_approve handlers run in the decision transaction.
"""
from dataclasses import dataclass
from typing import Callable, Literal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.legal_review import LegalReview, LegalReviewDecision
from app.services.audit import append_event
from app.services.legal_policy import LegalAccessDenied, LegalContext, ROLE_OPERATIONS, authorize_workspace

POLICY = "legal-review-v1"
COMPLIANCE_TARGETS = {"regulatory_applicability", "regulatory_change", "requirement_interpretation",
                      "evidence_acceptance", "assessment", "compliance_finding", "remediation_closure", "exception"}


class LegalReviewConflict(ValueError):
    pass


@dataclass(frozen=True)
class _Target:
    on_approve: Callable | None
    authorize: Callable | None
    operation: str


_TARGETS: dict[str, _Target] = {}


def register_target(target_type: str, *, on_approve: Callable[[Session, LegalReview], None] | None = None,
                    authorize: Callable[[Session, LegalContext, UUID], None] | None = None,
                    operation: str | None = None):
    """Register a reviewable type. `authorize(db, ctx, target_id)` adds object-level checks
    (raise LegalAccessDenied); `operation` overrides the review_legal/review_compliance default."""
    _TARGETS[target_type] = _Target(on_approve, authorize,
        operation or ("review_compliance" if target_type in COMPLIANCE_TARGETS else "review_legal"))


def _target(target_type):
    if target_type not in _TARGETS:
        raise LegalReviewConflict("review_target_unregistered")
    return _TARGETS[target_type]


def _audit(db, ctx, event_type, review, **details):
    append_event(db, event_type=event_type, actor_id=ctx.actor_id, actor_kind="user", payload={
        "policy_version": POLICY, "organization_id": str(ctx.organization_id), "workspace_id": str(ctx.workspace_id),
        "review_id": str(review.id), "target_type": review.target_type, "target_id": str(review.target_id),
        "target_revision_sha256": review.target_revision_sha256, **details})


def _terms():
    from app.core.config import settings
    return settings.current_terms_version


def submit(db: Session, *, workspace_id: UUID, target_type: str, target_id: UUID, target_revision_sha256: str,
           requester_id: UUID, idempotency_key: str, current_terms_version: str | None = None) -> LegalReview:
    target = _target(target_type)
    if len(target_revision_sha256 or "") != 64 or not 1 <= len(idempotency_key or "") <= 200:
        raise LegalReviewConflict("review_request_invalid")
    ctx = authorize_workspace(db, requester_id, workspace_id, current_terms_version=current_terms_version or _terms())
    if "propose" not in ROLE_OPERATIONS[ctx.role]:
        raise LegalAccessDenied()
    if target.authorize:
        target.authorize(db, ctx, target_id)
    existing = db.scalar(select(LegalReview).where(LegalReview.workspace_id == workspace_id,
        LegalReview.requester_id == requester_id, LegalReview.idempotency_key == idempotency_key))
    if existing:
        if (existing.target_type, existing.target_id, existing.target_revision_sha256) != (
                target_type, target_id, target_revision_sha256):
            raise LegalReviewConflict("review_retry_conflict")
        return existing
    if db.scalar(select(LegalReview.id).where(LegalReview.workspace_id == workspace_id,
            LegalReview.target_type == target_type, LegalReview.target_id == target_id,
            LegalReview.target_revision_sha256 == target_revision_sha256)):
        raise LegalReviewConflict("review_revision_exists")
    review = LegalReview(id=uuid4(), organization_id=ctx.organization_id, workspace_id=workspace_id,
        target_type=target_type, target_id=target_id, target_revision_sha256=target_revision_sha256,
        requester_id=requester_id, idempotency_key=idempotency_key)
    db.add(review)
    try:
        with db.begin_nested():
            db.flush()
    except IntegrityError:
        raise LegalReviewConflict("review_revision_exists")
    _audit(db, ctx, "LEGAL_REVIEW_REQUESTED", review)
    return review


def _authorize_reviewer(db, review, reviewer_id, terms):
    target = _target(review.target_type)
    ctx = authorize_workspace(db, reviewer_id, review.workspace_id, current_terms_version=terms)
    if (target.operation not in ROLE_OPERATIONS[ctx.role] or ctx.platform_role not in {"reviewer", "admin"}
            or reviewer_id == review.requester_id):
        raise LegalAccessDenied()
    if target.authorize:
        target.authorize(db, ctx, review.target_id)
    return ctx


def get(db: Session, *, workspace_id: UUID, review_id: UUID, actor_id: UUID,
        current_terms_version: str | None = None, lock: bool = False) -> LegalReview:
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version or _terms())
    query = select(LegalReview).where(LegalReview.id == review_id, LegalReview.workspace_id == workspace_id,
                                      LegalReview.organization_id == ctx.organization_id)
    review = db.scalar(query.with_for_update() if lock else query)
    if review is None or review.target_type not in _TARGETS:
        raise LegalAccessDenied()
    if _TARGETS[review.target_type].authorize:
        _TARGETS[review.target_type].authorize(db, ctx, review.target_id)
    return review


def decisions(db: Session, review_id: UUID) -> list[LegalReviewDecision]:
    return list(db.scalars(select(LegalReviewDecision).where(LegalReviewDecision.review_id == review_id)
                           .order_by(LegalReviewDecision.created_at, LegalReviewDecision.id)))


def status(db: Session, review: LegalReview) -> str:
    rows = decisions(db, review.id)
    terminal = [row for row in rows if row.decision != "escalate"]
    if terminal:
        return {"approve": "approved", "reject": "rejected", "request_changes": "changes_requested"}[terminal[0].decision]
    return "escalated" if rows else "pending"


def decide(db: Session, *, workspace_id: UUID, review_id: UUID, reviewer_id: UUID,
           decision: Literal["approve", "reject", "request_changes", "escalate"], rationale: str,
           current_terms_version: str | None = None) -> LegalReviewDecision:
    terms = current_terms_version or _terms()
    if decision not in ("approve", "reject", "request_changes", "escalate"):
        raise LegalReviewConflict("review_decision_invalid")
    if not rationale or not rationale.strip() or "\0" in rationale or len(rationale) > 2000:
        raise LegalReviewConflict("review_rationale_invalid")
    review = get(db, workspace_id=workspace_id, review_id=review_id, actor_id=reviewer_id,
                 current_terms_version=terms, lock=True)  # serializes concurrent decisions on this revision
    ctx = _authorize_reviewer(db, review, reviewer_id, terms)
    for row in decisions(db, review.id):
        if (row.reviewer_id, row.decision, row.rationale) == (reviewer_id, decision, rationale):
            return row  # exact replay
        if row.decision != "escalate":
            raise LegalReviewConflict("review_already_decided")
    row = LegalReviewDecision(id=uuid4(), organization_id=ctx.organization_id, workspace_id=workspace_id,
        review_id=review.id, requester_id=review.requester_id, reviewer_id=reviewer_id, decision=decision,
        rationale=rationale)
    db.add(row)
    try:
        with db.begin_nested():
            db.flush()
    except IntegrityError:
        raise LegalReviewConflict("review_already_decided")
    _audit(db, ctx, "LEGAL_REVIEW_DECIDED", review, decision=decision, decision_id=str(row.id))
    handler = _target(review.target_type).on_approve
    if decision == "approve" and handler:
        handler(db, review)
    _authorize_reviewer(db, review, reviewer_id, terms)  # revocation during handler blocks release
    return row


def is_approved(db: Session, *, workspace_id: UUID, target_type: str, target_id: UUID,
                target_revision_sha256: str) -> bool:
    return db.scalar(select(LegalReviewDecision.id).join(LegalReview, LegalReview.id == LegalReviewDecision.review_id)
        .where(LegalReview.workspace_id == workspace_id, LegalReview.target_type == target_type,
               LegalReview.target_id == target_id, LegalReview.target_revision_sha256 == target_revision_sha256,
               LegalReviewDecision.decision == "approve")) is not None
