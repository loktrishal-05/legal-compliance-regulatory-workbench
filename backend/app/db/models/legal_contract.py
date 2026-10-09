"""Agent B immutable contract/source/proposal records and separately erasable chat memory."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Integer, String, Text, UniqueConstraint, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, IdentityMixin


class Scope:
    organization_id: Mapped[UUID] = mapped_column()
    workspace_id: Mapped[UUID] = mapped_column()


def scoped(table):
    return (ForeignKeyConstraint(["organization_id", "workspace_id"],
        ["legal_workspaces.organization_id", "legal_workspaces.id"]),
        UniqueConstraint("id", "organization_id", "workspace_id", name=f"uq_{table}_scope"))


def parent(local, table):
    return ForeignKeyConstraint([local, "organization_id", "workspace_id"],
        [table + ".id", table + ".organization_id", table + ".workspace_id"])


class Contract(Scope, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_contracts"
    document_id: Mapped[UUID] = mapped_column()
    title: Mapped[str] = mapped_column(String(200))
    requester_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    __table_args__ = scoped(__tablename__) + (
        ForeignKeyConstraint(["organization_id", "workspace_id", "document_id"],
            ["legal_document_scopes.organization_id", "legal_document_scopes.workspace_id", "legal_document_scopes.document_id"]),
        UniqueConstraint("workspace_id", "document_id", name="uq_legal_contracts_document"),)


class ContractVersion(Scope, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_contract_versions"
    contract_id: Mapped[UUID] = mapped_column()
    document_id: Mapped[UUID] = mapped_column()
    version_id: Mapped[UUID] = mapped_column()
    source_sha256: Mapped[str] = mapped_column(String(64))
    __table_args__ = scoped(__tablename__) + (parent("contract_id", "legal_contracts"),
        ForeignKeyConstraint(["organization_id", "workspace_id", "document_id", "version_id", "source_sha256"],
            ["document_versions.organization_id", "document_versions.workspace_id", "document_versions.document_id", "document_versions.id", "document_versions.source_sha256"]),
        UniqueConstraint("contract_id", "version_id", name="uq_legal_contract_versions_source"),)


class ContractAnalysis(Scope, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_contract_analyses"
    contract_version_id: Mapped[UUID] = mapped_column()
    extraction_id: Mapped[UUID] = mapped_column()
    requester_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    profile_version: Mapped[str] = mapped_column(String(100))
    schema_version: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(100))
    rule_version: Mapped[str] = mapped_column(String(100))
    revision_sha256: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict] = mapped_column(JSONB)
    __table_args__ = scoped(__tablename__) + (parent("contract_version_id", "legal_contract_versions"),
        parent("extraction_id", "legal_extractions"),
        UniqueConstraint("id", "extraction_id", "organization_id", "workspace_id", name="uq_legal_contract_analyses_extraction"),
        UniqueConstraint("workspace_id", "contract_version_id", "revision_sha256", name="uq_legal_contract_analyses_replay"),
        CheckConstraint("length(revision_sha256) = 64", name="revision_hash"))


class AnalysisChild:
    analysis_id: Mapped[UUID] = mapped_column()
    payload: Mapped[dict] = mapped_column(JSONB)


class ContractParty(Scope, AnalysisChild, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_contract_parties"
    name: Mapped[str] = mapped_column(String(300))
    __table_args__ = scoped(__tablename__) + (parent("analysis_id", "legal_contract_analyses"),)


class ContractFact(Scope, AnalysisChild, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_contract_facts"
    kind: Mapped[str] = mapped_column(String(40))
    __table_args__ = scoped(__tablename__) + (parent("analysis_id", "legal_contract_analyses"),)


class ContractClause(Scope, AnalysisChild, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_contract_clauses"
    extraction_id: Mapped[UUID] = mapped_column()
    ordinal: Mapped[int] = mapped_column(Integer)
    clause_type: Mapped[str] = mapped_column(String(40))
    __table_args__ = scoped(__tablename__) + (
        ForeignKeyConstraint(["analysis_id", "extraction_id", "organization_id", "workspace_id"],
            ["legal_contract_analyses.id", "legal_contract_analyses.extraction_id", "legal_contract_analyses.organization_id", "legal_contract_analyses.workspace_id"]),
        UniqueConstraint("id", "extraction_id", "organization_id", "workspace_id", name="uq_legal_contract_clauses_extraction"),
        UniqueConstraint("analysis_id", "ordinal", name="uq_legal_contract_clauses_order"),
        CheckConstraint("ordinal > 0", name="ordinal"))


class ContractClauseSpan(Scope, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_contract_clause_spans"
    clause_id: Mapped[UUID] = mapped_column()
    extraction_id: Mapped[UUID] = mapped_column()
    span_id: Mapped[UUID] = mapped_column()
    __table_args__ = scoped(__tablename__) + (
        ForeignKeyConstraint(["clause_id", "extraction_id", "organization_id", "workspace_id"],
            ["legal_contract_clauses.id", "legal_contract_clauses.extraction_id", "legal_contract_clauses.organization_id", "legal_contract_clauses.workspace_id"]),
        ForeignKeyConstraint(["span_id", "extraction_id", "organization_id", "workspace_id"],
            ["legal_source_spans.id", "legal_source_spans.extraction_id", "legal_source_spans.organization_id", "legal_source_spans.workspace_id"]),
        UniqueConstraint("clause_id", "span_id", name="uq_legal_contract_clause_spans_link"))


class ContractFinding(Scope, AnalysisChild, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_contract_findings"
    requester_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    revision_sha256: Mapped[str] = mapped_column(String(64))
    __table_args__ = scoped(__tablename__) + (parent("analysis_id", "legal_contract_analyses"),
        CheckConstraint("length(revision_sha256) = 64", name="revision_hash"))


class ObligationProposal(Scope, AnalysisChild, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_contract_obligation_proposals"
    requester_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    revision_sha256: Mapped[str] = mapped_column(String(64))
    __table_args__ = scoped(__tablename__) + (parent("analysis_id", "legal_contract_analyses"),
        CheckConstraint("length(revision_sha256) = 64", name="revision_hash"))


class Playbook(Scope, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_contract_playbooks"
    name: Mapped[str] = mapped_column(String(200))
    version: Mapped[str] = mapped_column(String(60))
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    legal_basis: Mapped[str] = mapped_column(Text)
    jurisdiction: Mapped[str] = mapped_column(String(200))
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revision_sha256: Mapped[str] = mapped_column(String(64))
    __table_args__ = scoped(__tablename__) + (UniqueConstraint("workspace_id", "name", "version", name="uq_legal_contract_playbooks_version"),
        CheckConstraint("length(revision_sha256) = 64", name="revision_hash"),
        CheckConstraint("effective_until IS NULL OR (effective_from IS NOT NULL AND effective_until > effective_from)", name="effective_interval"))


class PlaybookRule(Scope, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_contract_playbook_rules"
    playbook_id: Mapped[UUID] = mapped_column()
    clause_type: Mapped[str] = mapped_column(String(40))
    kind: Mapped[str] = mapped_column(String(40))
    label: Mapped[str] = mapped_column(String(300))
    pattern: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    __table_args__ = scoped(__tablename__) + (parent("playbook_id", "legal_contract_playbooks"),
        CheckConstraint("kind IN ('required_clause','forbidden_text')", name="kind"))


class ContractSummary(Scope, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_contract_summaries"
    requester_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    profile: Mapped[str] = mapped_column(String(40))
    audience: Mapped[str] = mapped_column(String(40))
    revision_sha256: Mapped[str] = mapped_column(String(64))
    content: Mapped[dict] = mapped_column(JSONB)
    __table_args__ = scoped(__tablename__) + (UniqueConstraint("workspace_id", "requester_id", "revision_sha256", name="uq_legal_contract_summaries_replay"),
        CheckConstraint("length(revision_sha256) = 64", name="revision_hash"))


class SummarySpan(Scope, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_contract_summary_spans"
    summary_id: Mapped[UUID] = mapped_column()
    extraction_id: Mapped[UUID] = mapped_column()
    span_id: Mapped[UUID] = mapped_column()
    __table_args__ = scoped(__tablename__) + (parent("summary_id", "legal_contract_summaries"),
        ForeignKeyConstraint(["span_id", "extraction_id", "organization_id", "workspace_id"],
            ["legal_source_spans.id", "legal_source_spans.extraction_id", "legal_source_spans.organization_id", "legal_source_spans.workspace_id"]),
        UniqueConstraint("summary_id", "span_id", name="uq_legal_contract_summary_spans_link"))


class ContractConversation(Scope, IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_contract_conversations"
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    matter_id: Mapped[UUID | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    messages: Mapped[list] = mapped_column(JSONB)
    __table_args__ = scoped(__tablename__) + (ForeignKeyConstraint(["organization_id", "workspace_id", "matter_id"],
        ["legal_matters.organization_id", "legal_matters.workspace_id", "legal_matters.id"]),)


MODELS = (Contract, ContractVersion, ContractAnalysis, ContractParty, ContractFact, ContractClause,
    ContractClauseSpan, ContractFinding, ObligationProposal, Playbook, PlaybookRule, ContractSummary, SummarySpan, ContractConversation)
TABLES = tuple(m.__tablename__ for m in MODELS)


def _immutable(mapper, connection, target):
    raise ValueError("Legal contract revisions are immutable; create a successor revision")


for model in MODELS[:-1]:
    event.listen(model, "before_update", _immutable)
    event.listen(model, "before_delete", _immutable)
