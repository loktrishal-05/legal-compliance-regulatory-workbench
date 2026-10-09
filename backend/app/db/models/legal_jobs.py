"""Durable legal document jobs and anchored blank-region transcriptions (0026)."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import (CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text,
                        UniqueConstraint, event, func)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, IdentityMixin

JOB_STATES = ("queued", "running", "succeeded", "failed", "dead_letter")


class LegalJob(IdentityMixin, CreatedAtMixin, Base):
    """Queue row; the actor/scope/hash recorded at submit are re-verified by the worker."""
    __tablename__ = "legal_jobs"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    document_id: Mapped[UUID] = mapped_column()
    version_id: Mapped[UUID] = mapped_column()
    source_sha256: Mapped[str] = mapped_column(String(64))
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    operation: Mapped[str] = mapped_column(String(20))
    profile: Mapped[str] = mapped_column(String(60))
    idempotency_key: Mapped[str] = mapped_column(String(200))
    state: Mapped[str] = mapped_column(String(20), default="queued")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    lease_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    extraction_id: Mapped[UUID | None] = mapped_column(nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "workspace_id", "document_id", "version_id", "source_sha256"],
            ["document_versions.organization_id", "document_versions.workspace_id", "document_versions.document_id",
             "document_versions.id", "document_versions.source_sha256"], name="fk_legal_jobs_source_version"),
        UniqueConstraint("workspace_id", "actor_id", "idempotency_key", name="uq_legal_jobs_retry"),
        CheckConstraint("state IN ('queued','running','succeeded','failed','dead_letter')", name="state"),
        CheckConstraint("operation IN ('extract','ocr')", name="operation"),
        CheckConstraint("attempts >= 0 AND max_attempts BETWEEN 1 AND 10", name="attempts"),
        CheckConstraint("length(source_sha256) = 64", name="source_hash"),
        Index("ix_legal_jobs_claim", "state", "next_retry_at"),
        Index("ix_legal_jobs_workspace_state", "workspace_id", "state"),
    )


class LegalRegionTranscription(IdentityMixin, CreatedAtMixin, Base):
    """Manual transcription of a page region that has no stored span; reviewed via legal_review."""
    __tablename__ = "legal_region_transcriptions"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    extraction_id: Mapped[UUID] = mapped_column()
    page: Mapped[int] = mapped_column(Integer)
    bbox: Mapped[list] = mapped_column(JSONB)
    text: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    idempotency_key: Mapped[str] = mapped_column(String(200))
    transcription_sha256: Mapped[str] = mapped_column(String(64))
    __table_args__ = (
        ForeignKeyConstraint(["extraction_id", "organization_id", "workspace_id"],
            ["legal_extractions.id", "legal_extractions.organization_id", "legal_extractions.workspace_id"],
            name="fk_legal_region_transcriptions_extraction"),
        UniqueConstraint("workspace_id", "actor_id", "idempotency_key", name="uq_legal_region_transcriptions_retry"),
        CheckConstraint("page BETWEEN 1 AND 10000", name="page"),
        CheckConstraint("length(text) BETWEEN 1 AND 64000 AND length(rationale) BETWEEN 1 AND 2000", name="text_bounds"),
        CheckConstraint("length(transcription_sha256) = 64", name="hash"),
    )


def _immutable(mapper, connection, target):
    raise ValueError("Legal region transcriptions are immutable; submit a successor")


event.listen(LegalRegionTranscription, "before_update", _immutable)
event.listen(LegalRegionTranscription, "before_delete", _immutable)
