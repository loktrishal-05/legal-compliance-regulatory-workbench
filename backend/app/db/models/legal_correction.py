"""Append-only transcription corrections and exact-revision human decisions."""
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, ForeignKeyConstraint, String, Text, UniqueConstraint, event
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, IdentityMixin


class LegalCorrection(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_corrections"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    span_id: Mapped[UUID] = mapped_column()
    extraction_id: Mapped[UUID] = mapped_column()
    parent_correction_id: Mapped[UUID | None] = mapped_column(nullable=True)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    idempotency_key: Mapped[UUID] = mapped_column()
    original_quote_sha256: Mapped[str] = mapped_column(String(64))
    correction_sha256: Mapped[str] = mapped_column(String(64))
    corrected_text: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text)
    __table_args__ = (
        ForeignKeyConstraint(["span_id", "extraction_id", "organization_id", "workspace_id"],
            ["legal_source_spans.id", "legal_source_spans.extraction_id", "legal_source_spans.organization_id",
             "legal_source_spans.workspace_id"], name="fk_legal_corrections_span_lineage"),
        UniqueConstraint("id", "span_id", "organization_id", "workspace_id", name="uq_legal_corrections_parent_scope"),
        ForeignKeyConstraint(["parent_correction_id", "span_id", "organization_id", "workspace_id"],
            ["legal_corrections.id", "legal_corrections.span_id", "legal_corrections.organization_id",
             "legal_corrections.workspace_id"], name="fk_legal_corrections_parent_scope"),
        UniqueConstraint("id", "correction_sha256", "organization_id", "workspace_id", "actor_id", name="uq_legal_corrections_revision"),
        UniqueConstraint("workspace_id", "actor_id", "idempotency_key", name="uq_legal_corrections_retry"),
        CheckConstraint("length(original_quote_sha256) = 64 AND length(correction_sha256) = 64", name="hashes"),
        CheckConstraint("length(corrected_text) BETWEEN 1 AND 64000 AND length(rationale) BETWEEN 1 AND 2000", name="text_bounds"),
        CheckConstraint("parent_correction_id IS NULL OR parent_correction_id <> id", name="non_self_parent"),
    )


class LegalCorrectionDecision(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_correction_decisions"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    correction_id: Mapped[UUID] = mapped_column()
    correction_sha256: Mapped[str] = mapped_column(String(64))
    reviewer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    requester_id: Mapped[UUID] = mapped_column()
    outcome: Mapped[str] = mapped_column(String(20))
    rationale: Mapped[str] = mapped_column(Text)
    __table_args__ = (
        ForeignKeyConstraint(["correction_id", "correction_sha256", "organization_id", "workspace_id", "requester_id"],
            ["legal_corrections.id", "legal_corrections.correction_sha256", "legal_corrections.organization_id",
             "legal_corrections.workspace_id", "legal_corrections.actor_id"], name="fk_legal_correction_decisions_revision"),
        UniqueConstraint("correction_id", name="uq_legal_correction_decisions_final"),
        CheckConstraint("outcome IN ('approved','rejected')", name="outcome"),
        CheckConstraint("length(rationale) BETWEEN 1 AND 2000", name="rationale"),
        CheckConstraint("reviewer_id <> requester_id", name="independent_reviewer"),
    )


def _immutable(mapper, connection, target):
    raise ValueError("Legal correction records are immutable; create a successor proposal")


for model in (LegalCorrection, LegalCorrectionDecision):
    event.listen(model, "before_update", _immutable)
    event.listen(model, "before_delete", _immutable)
