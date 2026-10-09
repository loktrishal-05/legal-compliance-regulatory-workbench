"""Workspace-qualified registry and immutable regulatory source history."""
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, ForeignKeyConstraint, Integer, String, Text, UniqueConstraint, event
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base, CreatedAtMixin, IdentityMixin


class RegulatorySource(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_regulatory_sources"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    owner_id: Mapped[UUID] = mapped_column()
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(200))
    jurisdiction: Mapped[str] = mapped_column(String(100))
    authority_tier: Mapped[str] = mapped_column(String(30))
    trust_state: Mapped[str] = mapped_column(String(20), default="proposed", server_default="proposed")
    import_policy: Mapped[str] = mapped_column(String(20), default="manual", server_default="manual")
    revision_sha256: Mapped[str] = mapped_column(String(64))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "workspace_id", "owner_id"],
            ["legal_workspace_memberships.organization_id", "legal_workspace_memberships.workspace_id", "legal_workspace_memberships.user_id"]),
        UniqueConstraint("organization_id", "workspace_id", "id"),
        CheckConstraint("trust_state IN ('proposed','approved','rejected')", name="trust_state"),
        CheckConstraint("import_policy = 'manual'", name="import_policy"),
        CheckConstraint("authority_tier IN ('unverified','primary','secondary')", name="authority_tier"),
        CheckConstraint("length(revision_sha256) = 64", name="revision_hash"),
    )


class RegulatoryDocument(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_regulatory_documents"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    source_id: Mapped[UUID] = mapped_column()
    title: Mapped[str] = mapped_column(String(250))
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "workspace_id", "source_id"],
            ["legal_regulatory_sources.organization_id", "legal_regulatory_sources.workspace_id", "legal_regulatory_sources.id"]),
        UniqueConstraint("organization_id", "workspace_id", "id"),
    )


class RegulatoryVersion(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_regulatory_versions"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    regulatory_document_id: Mapped[UUID] = mapped_column()
    document_id: Mapped[UUID] = mapped_column()
    version_id: Mapped[UUID] = mapped_column()
    extraction_id: Mapped[UUID] = mapped_column()
    source_sha256: Mapped[str] = mapped_column(String(64))
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    published_at: Mapped[date | None] = mapped_column(Date)
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_until: Mapped[date | None] = mapped_column(Date)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    amends_id: Mapped[UUID | None] = mapped_column()
    supersedes_id: Mapped[UUID | None] = mapped_column()
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "workspace_id", "regulatory_document_id"],
            ["legal_regulatory_documents.organization_id", "legal_regulatory_documents.workspace_id", "legal_regulatory_documents.id"]),
        ForeignKeyConstraint(["organization_id", "workspace_id", "document_id", "version_id", "source_sha256"],
            ["document_versions.organization_id", "document_versions.workspace_id", "document_versions.document_id", "document_versions.id", "document_versions.source_sha256"]),
        ForeignKeyConstraint(["extraction_id", "organization_id", "workspace_id"],
            ["legal_extractions.id", "legal_extractions.organization_id", "legal_extractions.workspace_id"]),
        UniqueConstraint("organization_id", "workspace_id", "id"),
        UniqueConstraint("organization_id", "workspace_id", "regulatory_document_id", "id", name="uq_regulatory_version_document"),
        ForeignKeyConstraint(["organization_id", "workspace_id", "regulatory_document_id", "amends_id"],
            ["legal_regulatory_versions.organization_id", "legal_regulatory_versions.workspace_id", "legal_regulatory_versions.regulatory_document_id", "legal_regulatory_versions.id"], name="fk_regulatory_version_amends"),
        ForeignKeyConstraint(["organization_id", "workspace_id", "regulatory_document_id", "supersedes_id"],
            ["legal_regulatory_versions.organization_id", "legal_regulatory_versions.workspace_id", "legal_regulatory_versions.regulatory_document_id", "legal_regulatory_versions.id"], name="fk_regulatory_version_supersedes"),
        UniqueConstraint("regulatory_document_id", "version_id"),
        CheckConstraint("effective_until IS NULL OR effective_from IS NULL OR effective_until > effective_from", name="effective_interval"),
    )


class RegulatoryChange(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_regulatory_changes"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    regulatory_document_id: Mapped[UUID] = mapped_column()
    from_version_id: Mapped[UUID] = mapped_column()
    to_version_id: Mapped[UUID] = mapped_column()
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    exact_diff: Mapped[list] = mapped_column(JSON)
    semantic_proposal: Mapped[dict] = mapped_column(JSON)
    revision_sha256: Mapped[str] = mapped_column(String(64))
    __table_args__ = (
        *(ForeignKeyConstraint(["organization_id", "workspace_id", "regulatory_document_id", name],
            ["legal_regulatory_versions.organization_id", "legal_regulatory_versions.workspace_id", "legal_regulatory_versions.regulatory_document_id", "legal_regulatory_versions.id"], name=f"fk_regulatory_change_{name}")
            for name in ("from_version_id", "to_version_id")),
        UniqueConstraint("organization_id", "workspace_id", "id"),
        UniqueConstraint("from_version_id", "to_version_id"),
        CheckConstraint("from_version_id <> to_version_id", name="different_versions"),
    )


class ApplicabilityDecision(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_regulatory_applicability"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    regulatory_version_id: Mapped[UUID] = mapped_column()
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    state: Mapped[str] = mapped_column(String(20))
    jurisdiction: Mapped[str] = mapped_column(String(100))
    entity: Mapped[str] = mapped_column(String(200))
    product: Mapped[str] = mapped_column(String(200))
    business_unit: Mapped[str] = mapped_column(String(200))
    rationale: Mapped[str] = mapped_column(Text)
    effective_on: Mapped[date] = mapped_column(Date)
    revision_sha256: Mapped[str] = mapped_column(String(64))
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "workspace_id", "regulatory_version_id"],
            ["legal_regulatory_versions.organization_id", "legal_regulatory_versions.workspace_id", "legal_regulatory_versions.id"]),
        UniqueConstraint("organization_id", "workspace_id", "id"),
        CheckConstraint("state IN ('applicable','not_applicable')", name="state"),
    )


class RegulatoryWatchlist(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_regulatory_watchlists"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    source_id: Mapped[UUID] = mapped_column()
    owner_id: Mapped[UUID] = mapped_column()
    max_age_days: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "workspace_id", "source_id"],
            ["legal_regulatory_sources.organization_id", "legal_regulatory_sources.workspace_id", "legal_regulatory_sources.id"]),
        ForeignKeyConstraint(["organization_id", "workspace_id", "owner_id"],
            ["legal_workspace_memberships.organization_id", "legal_workspace_memberships.workspace_id", "legal_workspace_memberships.user_id"]),
        UniqueConstraint("source_id", "owner_id"),
        CheckConstraint("max_age_days BETWEEN 1 AND 3650", name="max_age_days"),
    )


class RegulatoryCampaign(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_regulatory_campaigns"
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()
    change_id: Mapped[UUID] = mapped_column()
    affected: Mapped[list] = mapped_column(JSON)
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "workspace_id", "change_id"],
            ["legal_regulatory_changes.organization_id", "legal_regulatory_changes.workspace_id", "legal_regulatory_changes.id"]),
        UniqueConstraint("change_id"),
    )


def _immutable(mapper, connection, target):
    raise ValueError("Regulatory history is immutable; create a successor revision")


for model in (RegulatoryVersion, RegulatoryChange, ApplicabilityDecision, RegulatoryCampaign):
    event.listen(model, "before_update", _immutable)
    event.listen(model, "before_delete", _immutable)
