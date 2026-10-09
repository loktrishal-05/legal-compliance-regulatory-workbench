"""Distinct compliance entities and append-only interpretations, proof and assessments."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, String, Text, UniqueConstraint, event
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base, CreatedAtMixin, IdentityMixin


class Scoped:
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()


def scope():
    return (ForeignKeyConstraint(["organization_id", "workspace_id"],
        ["legal_workspaces.organization_id", "legal_workspaces.id"]),
        UniqueConstraint("organization_id", "workspace_id", "id"))


def link(column, table):
    return ForeignKeyConstraint(["organization_id", "workspace_id", column],
        [f"{table}.organization_id", f"{table}.workspace_id", f"{table}.id"], name=f"fk_{table}_{column}")


class Requirement(Scoped, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_compliance_requirements"
    regulatory_version_id: Mapped[UUID] = mapped_column()
    title: Mapped[str] = mapped_column(String(250))
    __table_args__ = (*scope(), link("regulatory_version_id", "legal_regulatory_versions"))


class InterpretationRevision(Scoped, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_compliance_interpretations"
    requirement_id: Mapped[UUID] = mapped_column()
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text)
    citations: Mapped[list] = mapped_column(JSON)
    revision_sha256: Mapped[str] = mapped_column(String(64))
    __table_args__ = (*scope(), link("requirement_id", "legal_compliance_requirements"))


class Policy(Scoped, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_compliance_policies"
    title: Mapped[str] = mapped_column(String(250))
    __table_args__ = scope()


class PolicyVersion(Scoped, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_compliance_policy_versions"
    policy_id: Mapped[UUID] = mapped_column()
    document_id: Mapped[UUID] = mapped_column()
    version_id: Mapped[UUID] = mapped_column()
    source_sha256: Mapped[str] = mapped_column(String(64))
    __table_args__ = (*scope(), link("policy_id", "legal_compliance_policies"),
        ForeignKeyConstraint(["organization_id", "workspace_id", "document_id", "version_id", "source_sha256"],
            ["document_versions.organization_id", "document_versions.workspace_id", "document_versions.document_id", "document_versions.id", "document_versions.source_sha256"]),
        UniqueConstraint("policy_id", "version_id"))


class Control(Scoped, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_compliance_controls"
    title: Mapped[str] = mapped_column(String(250))
    description: Mapped[str] = mapped_column(Text)
    owner_id: Mapped[UUID] = mapped_column()
    __table_args__ = (*scope(), ForeignKeyConstraint(["organization_id", "workspace_id", "owner_id"],
        ["legal_workspace_memberships.organization_id", "legal_workspace_memberships.workspace_id", "legal_workspace_memberships.user_id"]))


class Evidence(Scoped, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_compliance_evidence"
    title: Mapped[str] = mapped_column(String(250))
    __table_args__ = scope()


class EvidenceVersion(Scoped, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_compliance_evidence_versions"
    evidence_id: Mapped[UUID] = mapped_column()
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    document_id: Mapped[UUID] = mapped_column()
    version_id: Mapped[UUID] = mapped_column()
    source_sha256: Mapped[str] = mapped_column(String(64))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaces_id: Mapped[UUID | None] = mapped_column()
    facts: Mapped[dict] = mapped_column(JSON)
    citations: Mapped[list] = mapped_column(JSON)
    revision_sha256: Mapped[str] = mapped_column(String(64))
    __table_args__ = (*scope(), link("evidence_id", "legal_compliance_evidence"),
        link("replaces_id", "legal_compliance_evidence_versions"),
        ForeignKeyConstraint(["organization_id", "workspace_id", "document_id", "version_id", "source_sha256"],
            ["document_versions.organization_id", "document_versions.workspace_id", "document_versions.document_id", "document_versions.id", "document_versions.source_sha256"]),
        CheckConstraint("expires_at IS NULL OR expires_at > valid_from", name="valid_interval"))


class Mapping(Scoped, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_compliance_mappings"
    requirement_id: Mapped[UUID] = mapped_column()
    control_id: Mapped[UUID] = mapped_column()
    policy_version_id: Mapped[UUID | None] = mapped_column()
    evidence_version_id: Mapped[UUID | None] = mapped_column()
    __table_args__ = (*scope(), link("requirement_id", "legal_compliance_requirements"),
        link("control_id", "legal_compliance_controls"), link("policy_version_id", "legal_compliance_policy_versions"),
        link("evidence_version_id", "legal_compliance_evidence_versions"))


class RuleVersion(Scoped, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_compliance_rules"
    control_id: Mapped[UUID] = mapped_column()
    interpretation_id: Mapped[UUID] = mapped_column()
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    checks: Mapped[list] = mapped_column(JSON)
    revision_sha256: Mapped[str] = mapped_column(String(64))
    __table_args__ = (*scope(), link("control_id", "legal_compliance_controls"),
        link("interpretation_id", "legal_compliance_interpretations"))


class Assessment(Scoped, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_compliance_assessments"
    requirement_id: Mapped[UUID] = mapped_column()
    applicability_id: Mapped[UUID] = mapped_column()
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    inputs: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30))
    revision_sha256: Mapped[str] = mapped_column(String(64))
    __table_args__ = (*scope(), link("requirement_id", "legal_compliance_requirements"),
        link("applicability_id", "legal_regulatory_applicability"),
        CheckConstraint("status IN ('satisfied','partially_satisfied','unsatisfied','insufficient_evidence','not_applicable','needs_review')", name="status"))


class ComplianceFinding(Scoped, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_compliance_findings"
    assessment_id: Mapped[UUID] = mapped_column()
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text)
    revision_sha256: Mapped[str] = mapped_column(String(64))
    __table_args__ = (*scope(), link("assessment_id", "legal_compliance_assessments"))


class Reevaluation(Scoped, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_compliance_reevaluations"
    assessment_id: Mapped[UUID] = mapped_column()
    reason: Mapped[str] = mapped_column(String(200))
    cause_key: Mapped[str] = mapped_column(String(200))
    __table_args__ = (*scope(), link("assessment_id", "legal_compliance_assessments"),
        UniqueConstraint("assessment_id", "cause_key"))


def _immutable(mapper, connection, target):
    raise ValueError("Compliance history is immutable; create a successor revision")


IMMUTABLE = (Requirement, InterpretationRevision, PolicyVersion, EvidenceVersion, Mapping, RuleVersion,
             Assessment, ComplianceFinding, Reevaluation)
for model in IMMUTABLE:
    event.listen(model, "before_update", _immutable)
    event.listen(model, "before_delete", _immutable)
