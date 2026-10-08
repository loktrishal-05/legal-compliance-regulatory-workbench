"""Immutable native extraction and tenant-bound source coordinates (E2a)."""
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, ForeignKeyConstraint, Integer, String, Text, UniqueConstraint, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, IdentityMixin


class LegalExtraction(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_extractions"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    document_id: Mapped[UUID] = mapped_column()
    version_id: Mapped[UUID] = mapped_column()
    source_sha256: Mapped[str] = mapped_column(String(64))
    policy_version: Mapped[str] = mapped_column(String(60))
    extractor: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30))
    text: Mapped[str] = mapped_column(Text)
    artifact_sha256: Mapped[str] = mapped_column(String(64))
    warnings: Mapped[list] = mapped_column(JSONB)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "workspace_id", "document_id", "version_id", "source_sha256"],
            ["document_versions.organization_id", "document_versions.workspace_id", "document_versions.document_id",
             "document_versions.id", "document_versions.source_sha256"], name="fk_legal_extractions_source_version"),
        UniqueConstraint("version_id", "policy_version", name="uq_legal_extractions_version_policy"),
        UniqueConstraint("id", "organization_id", "workspace_id", name="uq_legal_extractions_scope"),
        CheckConstraint("status IN ('ready','needs_verification')", name="status"),
        CheckConstraint("length(source_sha256) = 64 AND length(artifact_sha256) = 64", name="hashes"),
    )


class LegalSourceSpan(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_source_spans"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    extraction_id: Mapped[UUID] = mapped_column()
    start: Mapped[int] = mapped_column(Integer)
    end: Mapped[int] = mapped_column(Integer)
    locator: Mapped[dict] = mapped_column(JSONB)
    __table_args__ = (
        ForeignKeyConstraint(["extraction_id", "organization_id", "workspace_id"],
            ["legal_extractions.id", "legal_extractions.organization_id", "legal_extractions.workspace_id"],
            name="fk_legal_source_spans_extraction_scope"),
        UniqueConstraint("extraction_id", "start", name="uq_legal_source_spans_start"),
        UniqueConstraint("id", "extraction_id", "organization_id", "workspace_id", name="uq_legal_source_spans_lineage"),
        CheckConstraint('start >= 0 AND "end" > start', name="offsets"),
    )


def _immutable(mapper, connection, target):
    raise ValueError("Legal extraction and source spans are immutable; create a successor revision")


for model in (LegalExtraction, LegalSourceSpan):
    event.listen(model, "before_update", _immutable)
    event.listen(model, "before_delete", _immutable)
