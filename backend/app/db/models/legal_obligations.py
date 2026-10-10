"""Accepted obligations, deadlines, tasks, remediation, exceptions, notifications, comments, evidence packs (0031)."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import (Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String,
                        Text, UniqueConstraint, event, func)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, IdentityMixin


def _ws_fk():
    return ForeignKeyConstraint(["organization_id", "workspace_id"],
                                ["legal_workspaces.organization_id", "legal_workspaces.id"])


def _member_fk(column, name):
    return ForeignKeyConstraint(["organization_id", "workspace_id", column],
        ["legal_workspace_memberships.organization_id", "legal_workspace_memberships.workspace_id",
         "legal_workspace_memberships.user_id"], name=name)


def _scoped_fk(column, table, name):
    return ForeignKeyConstraint([column, "organization_id", "workspace_id"],
        [f"{table}.id", f"{table}.organization_id", f"{table}.workspace_id"], name=name)


class LegalObligation(IdentityMixin, CreatedAtMixin, Base):
    """Accepted (independently reviewed) duty; created only by the obligation_accepted handler."""
    __tablename__ = "legal_obligations"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    proposal_id: Mapped[UUID] = mapped_column()
    proposal_sha256: Mapped[str] = mapped_column(String(64))
    review_id: Mapped[UUID] = mapped_column()
    source_event_id: Mapped[UUID] = mapped_column()
    document_id: Mapped[UUID] = mapped_column()
    version_id: Mapped[UUID] = mapped_column()
    source_sha256: Mapped[str] = mapped_column(String(64))
    citations: Mapped[list] = mapped_column(JSONB)
    actor_text: Mapped[str] = mapped_column(Text)
    action_text: Mapped[str] = mapped_column(Text)
    obligation_type: Mapped[str] = mapped_column(String(40))
    trigger_text: Mapped[str] = mapped_column(Text)
    conditions: Mapped[list] = mapped_column(JSONB)
    original_deadline_phrase: Mapped[str] = mapped_column(Text)
    uncertainties: Mapped[list] = mapped_column(JSONB)
    owner_id: Mapped[UUID | None] = mapped_column(nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    date_only: Mapped[bool] = mapped_column(Boolean, default=False)
    notice_days: Mapped[int] = mapped_column(Integer, default=0)
    recurrence_rule: Mapped[str | None] = mapped_column(String(100), nullable=True)
    calendar_policy: Mapped[str] = mapped_column(String(40), default="legal-deadline-v1")
    status: Mapped[str] = mapped_column(String(30), default="needs_confirmation")
    confirmed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        _ws_fk(), _member_fk("owner_id", "fk_legal_obligations_owner"),
        UniqueConstraint("workspace_id", "proposal_id", "proposal_sha256", name="uq_legal_obligations_proposal"),
        UniqueConstraint("id", "organization_id", "workspace_id", name="uq_legal_obligations_scope"),
        CheckConstraint("status IN ('needs_confirmation','active','completed','impact_review')", name="status"),
        CheckConstraint("notice_days BETWEEN 0 AND 365", name="notice_days"),
        CheckConstraint("status = 'needs_confirmation' OR (timezone IS NOT NULL AND due_at IS NOT NULL)",
                        name="confirmed_deadline"),
    )


class LegalDeadlineOccurrence(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_deadline_occurrences"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    obligation_id: Mapped[UUID] = mapped_column()
    sequence: Mapped[int] = mapped_column(Integer)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    __table_args__ = (
        _scoped_fk("obligation_id", "legal_obligations", "fk_legal_deadline_occurrences_obligation"),
        UniqueConstraint("obligation_id", "sequence", name="uq_legal_deadline_occurrences_key"),
        CheckConstraint("status IN ('scheduled','done','cancelled')", name="status"),
        Index("ix_legal_deadline_occurrences_due", "status", "due_at"),
    )


class LegalTask(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_tasks"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    kind: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(300))
    source_type: Mapped[str] = mapped_column(String(40))
    source_id: Mapped[UUID] = mapped_column()
    document_id: Mapped[UUID | None] = mapped_column(nullable=True)
    owner_id: Mapped[UUID | None] = mapped_column(nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")
    evidence_request: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    __table_args__ = (
        _ws_fk(), _member_fk("owner_id", "fk_legal_tasks_owner"),
        UniqueConstraint("workspace_id", "source_type", "source_id", "kind", name="uq_legal_tasks_source"),
        UniqueConstraint("id", "organization_id", "workspace_id", name="uq_legal_tasks_scope"),
        CheckConstraint("kind IN ('obligation','remediation','evidence_request','evidence_expired',"
                        "'regulatory_change','exception_expired')", name="kind"),
        CheckConstraint("status IN ('open','in_progress','submitted','done','cancelled')", name="status"),
    )


class LegalTaskDependency(CreatedAtMixin, Base):
    __tablename__ = "legal_task_dependencies"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    task_id: Mapped[UUID] = mapped_column(primary_key=True)
    depends_on_id: Mapped[UUID] = mapped_column(primary_key=True)
    __table_args__ = (
        _scoped_fk("task_id", "legal_tasks", "fk_legal_task_dependencies_task"),
        _scoped_fk("depends_on_id", "legal_tasks", "fk_legal_task_dependencies_depends_on"),
        CheckConstraint("task_id <> depends_on_id", name="no_self_dependency"),
    )


class LegalRemediation(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_remediations"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    finding_id: Mapped[UUID] = mapped_column()
    assessment_id: Mapped[UUID | None] = mapped_column(nullable=True)
    task_id: Mapped[UUID] = mapped_column()
    status: Mapped[str] = mapped_column(String(20), default="open")
    closure_evidence: Mapped[list] = mapped_column(JSONB)
    closure_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    retest_required: Mapped[bool] = mapped_column(Boolean, default=True)
    retest_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    closed_review_id: Mapped[UUID | None] = mapped_column(nullable=True)
    reopen_count: Mapped[int] = mapped_column(Integer, default=0)
    __table_args__ = (
        _ws_fk(), _scoped_fk("task_id", "legal_tasks", "fk_legal_remediations_task"),
        UniqueConstraint("workspace_id", "finding_id", name="uq_legal_remediations_finding"),
        CheckConstraint("status IN ('open','in_progress','submitted','closed','reopened')", name="status"),
        CheckConstraint("status <> 'closed' OR (closure_sha256 IS NOT NULL AND closed_review_id IS NOT NULL)",
                        name="closure_needs_review"),
    )


class LegalException(IdentityMixin, CreatedAtMixin, Base):
    """Risk acceptance with mandatory expiry (FR-046); active only after independent review."""
    __tablename__ = "legal_exceptions"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    subject_type: Mapped[str] = mapped_column(String(40))
    subject_id: Mapped[UUID] = mapped_column()
    rationale: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    requester_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    exception_sha256: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default="proposed")
    __table_args__ = (
        _ws_fk(),
        CheckConstraint("status IN ('proposed','active','expired','rejected')", name="status"),
        CheckConstraint("length(rationale) BETWEEN 1 AND 4000", name="rationale"),
        CheckConstraint("expires_at > created_at", name="future_expiry"),
    )


class LegalNotification(IdentityMixin, CreatedAtMixin, Base):
    """Authoritative in-app notification; carries IDs/codes, never source text."""
    __tablename__ = "legal_notifications"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    recipient_id: Mapped[UUID] = mapped_column()
    kind: Mapped[str] = mapped_column(String(40))
    subject_type: Mapped[str] = mapped_column(String(40))
    subject_id: Mapped[UUID] = mapped_column()
    dedupe_key: Mapped[str] = mapped_column(String(200))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        _member_fk("recipient_id", "fk_legal_notifications_recipient"),
        UniqueConstraint("workspace_id", "recipient_id", "dedupe_key", name="uq_legal_notifications_dedupe"),
    )


class LegalDispatchReceipt(CreatedAtMixin, Base):
    """Exactly-once marker for timer effects (reminder/escalation/expiry) across restarts and workers."""
    __tablename__ = "legal_dispatch_receipts"
    receipt_key: Mapped[str] = mapped_column(String(200), primary_key=True)
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    kind: Mapped[str] = mapped_column(String(40))
    __table_args__ = (_ws_fk(),)


class LegalComment(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_comments"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    subject_type: Mapped[str] = mapped_column(String(40))
    subject_id: Mapped[UUID] = mapped_column()
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    mentions: Mapped[list] = mapped_column(JSONB)
    __table_args__ = (_ws_fk(), CheckConstraint("length(body) BETWEEN 1 AND 4000", name="body"))


class LegalEvidencePack(IdentityMixin, CreatedAtMixin, Base):
    """Frozen manifest of permitted sources/versions/hashes/reviews; integrity hash over canonical JSON."""
    __tablename__ = "legal_evidence_packs"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(String(30))
    manifest: Mapped[dict] = mapped_column(JSONB)
    manifest_sha256: Mapped[str] = mapped_column(String(64))
    __table_args__ = (_ws_fk(), CheckConstraint("kind IN ('evidence_pack','findings_export')", name="kind"))


def _append_only(mapper, connection, target):
    raise ValueError("Legal comments, receipts and evidence packs are append-only")


for model in (LegalComment, LegalEvidencePack, LegalDispatchReceipt):
    event.listen(model, "before_update", _append_only)
    event.listen(model, "before_delete", _append_only)
