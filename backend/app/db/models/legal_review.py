"""Exact-revision independent review requests/decisions, outbox events and scheduler receipts (0027)."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import (CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text,
                        UniqueConstraint, event, inspect, text)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, IdentityMixin

DECISIONS = ("approve", "reject", "request_changes", "escalate")


class LegalReview(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_reviews"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    target_type: Mapped[str] = mapped_column(String(60))
    target_id: Mapped[UUID] = mapped_column()
    target_revision_sha256: Mapped[str] = mapped_column(String(64))
    requester_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    idempotency_key: Mapped[str] = mapped_column(String(200))
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "workspace_id"],
                             ["legal_workspaces.organization_id", "legal_workspaces.id"]),
        UniqueConstraint("workspace_id", "requester_id", "idempotency_key", name="uq_legal_reviews_retry"),
        UniqueConstraint("workspace_id", "target_type", "target_id", "target_revision_sha256",
                         name="uq_legal_reviews_revision"),
        UniqueConstraint("id", "organization_id", "workspace_id", "requester_id", name="uq_legal_reviews_scope"),
        CheckConstraint("length(target_revision_sha256) = 64", name="revision_hash"),
        CheckConstraint("length(idempotency_key) BETWEEN 1 AND 200", name="idempotency_key"),
    )


class LegalReviewDecision(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_review_decisions"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    review_id: Mapped[UUID] = mapped_column()
    requester_id: Mapped[UUID] = mapped_column()
    reviewer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(20))
    rationale: Mapped[str] = mapped_column(Text)
    __table_args__ = (
        ForeignKeyConstraint(["review_id", "organization_id", "workspace_id", "requester_id"],
            ["legal_reviews.id", "legal_reviews.organization_id", "legal_reviews.workspace_id",
             "legal_reviews.requester_id"], name="fk_legal_review_decisions_review"),
        CheckConstraint("decision IN ('approve','reject','request_changes','escalate')", name="decision"),
        CheckConstraint("length(rationale) BETWEEN 1 AND 2000", name="rationale"),
        CheckConstraint("reviewer_id <> requester_id", name="independent_reviewer"),
        # One terminal outcome per exact revision; escalations may precede it.
        Index("uq_legal_review_decisions_terminal", "review_id", unique=True,
              postgresql_where=text("decision <> 'escalate'"), sqlite_where=text("decision <> 'escalate'")),
    )


class LegalEvent(IdentityMixin, CreatedAtMixin, Base):
    """Transactional outbox row; payload is immutable, dispatch columns are worker-owned."""
    __tablename__ = "legal_events"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    event_type: Mapped[str] = mapped_column(String(80))
    idempotency_key: Mapped[str] = mapped_column(String(200))
    payload: Mapped[dict] = mapped_column(JSONB)
    payload_sha256: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lease_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "workspace_id"],
                             ["legal_workspaces.organization_id", "legal_workspaces.id"]),
        UniqueConstraint("workspace_id", "event_type", "idempotency_key", name="uq_legal_events_retry"),
        CheckConstraint("status IN ('pending','dispatched','dead_letter')", name="status"),
        CheckConstraint("attempts >= 0", name="attempts"),
        Index("ix_legal_events_due", "status", "next_attempt_at"),
    )


class LegalSchedulerScan(Base):
    """Last-run receipt per registered scan. System-level: counts/codes only, never tenant content."""
    __tablename__ = "legal_scheduler_scans"
    name: Mapped[str] = mapped_column(String(80), primary_key=True)
    last_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    runs: Mapped[int] = mapped_column(Integer, default=0)


def _immutable(mapper, connection, target):
    raise ValueError("Legal review records are immutable; submit a new revision")


for model in (LegalReview, LegalReviewDecision):
    event.listen(model, "before_update", _immutable)
    event.listen(model, "before_delete", _immutable)


@event.listens_for(LegalEvent, "before_update")
def _payload_frozen(mapper, connection, target):
    state = inspect(target)
    for name in ("payload", "payload_sha256", "event_type", "idempotency_key", "workspace_id", "organization_id"):
        if state.attrs[name].history.has_changes():
            raise ValueError("Legal event payload is immutable")
