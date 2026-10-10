"""Legal contracts, clauses, playbooks, summaries and assistant. Owner: agent B (parallel build 2026-10-09); pre-allocated stub."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0028_legal_contracts"
down_revision = "0027_legal_reviews_events"
branch_labels = None
depends_on = None

TABLES = ("legal_contracts", "legal_contract_versions", "legal_contract_analyses", "legal_contract_parties",
    "legal_contract_facts", "legal_contract_clauses", "legal_contract_clause_spans", "legal_contract_findings",
    "legal_contract_obligation_proposals", "legal_contract_playbooks", "legal_contract_playbook_rules",
    "legal_contract_summaries", "legal_contract_summary_spans", "legal_contract_conversations")


def uid(name, nullable=False, foreign=None):
    return sa.Column(name, sa.Uuid(), *([sa.ForeignKey(foreign)] if foreign else []), nullable=nullable)


def string(name, length, nullable=False):
    return sa.Column(name, sa.String(length), nullable=nullable)


def parent(local, table):
    return sa.ForeignKeyConstraint([local, "organization_id", "workspace_id"],
        [table + ".id", table + ".organization_id", table + ".workspace_id"])


def create(name, *items):
    op.create_table(name, sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        uid("organization_id"), uid("workspace_id"),
        sa.ForeignKeyConstraint(["organization_id", "workspace_id"],
            ["legal_workspaces.organization_id", "legal_workspaces.id"]),
        sa.UniqueConstraint("id", "organization_id", "workspace_id", name=f"uq_{name}_scope"), *items)


def payload():
    return sa.Column("payload", postgresql.JSONB(), nullable=False)


def hash_check():
    return sa.CheckConstraint("length(revision_sha256) = 64", name="revision_hash")


def upgrade():
    create("legal_contracts", uid("document_id"), string("title", 200), uid("requester_id", foreign="users.id"),
        sa.ForeignKeyConstraint(["organization_id", "workspace_id", "document_id"],
            ["legal_document_scopes.organization_id", "legal_document_scopes.workspace_id", "legal_document_scopes.document_id"]),
        sa.UniqueConstraint("workspace_id", "document_id", name="uq_legal_contracts_document"))
    create("legal_contract_versions", uid("contract_id"), uid("document_id"), uid("version_id"), string("source_sha256", 64),
        parent("contract_id", "legal_contracts"),
        sa.ForeignKeyConstraint(["organization_id", "workspace_id", "document_id", "version_id", "source_sha256"],
            ["document_versions.organization_id", "document_versions.workspace_id", "document_versions.document_id", "document_versions.id", "document_versions.source_sha256"]),
        sa.UniqueConstraint("contract_id", "version_id", name="uq_legal_contract_versions_source"))
    create("legal_contract_analyses", uid("contract_version_id"), uid("extraction_id"), uid("requester_id", foreign="users.id"),
        *(string(n, 100) for n in ("profile_version", "schema_version", "prompt_version", "rule_version")),
        string("revision_sha256", 64), sa.Column("result", postgresql.JSONB(), nullable=False),
        parent("contract_version_id", "legal_contract_versions"), parent("extraction_id", "legal_extractions"),
        sa.UniqueConstraint("id", "extraction_id", "organization_id", "workspace_id", name="uq_legal_contract_analyses_extraction"),
        sa.UniqueConstraint("workspace_id", "contract_version_id", "revision_sha256", name="uq_legal_contract_analyses_replay"), hash_check())
    create("legal_contract_parties", uid("analysis_id"), payload(), string("name", 300), parent("analysis_id", "legal_contract_analyses"))
    create("legal_contract_facts", uid("analysis_id"), payload(), string("kind", 40), parent("analysis_id", "legal_contract_analyses"))
    create("legal_contract_clauses", uid("analysis_id"), payload(), uid("extraction_id"),
        sa.Column("ordinal", sa.Integer(), nullable=False), string("clause_type", 40),
        sa.ForeignKeyConstraint(["analysis_id", "extraction_id", "organization_id", "workspace_id"],
            ["legal_contract_analyses.id", "legal_contract_analyses.extraction_id", "legal_contract_analyses.organization_id", "legal_contract_analyses.workspace_id"]),
        sa.UniqueConstraint("id", "extraction_id", "organization_id", "workspace_id", name="uq_legal_contract_clauses_extraction"),
        sa.UniqueConstraint("analysis_id", "ordinal", name="uq_legal_contract_clauses_order"), sa.CheckConstraint("ordinal > 0", name="ordinal"))
    create("legal_contract_clause_spans", uid("clause_id"), uid("extraction_id"), uid("span_id"),
        sa.ForeignKeyConstraint(["clause_id", "extraction_id", "organization_id", "workspace_id"],
            ["legal_contract_clauses.id", "legal_contract_clauses.extraction_id", "legal_contract_clauses.organization_id", "legal_contract_clauses.workspace_id"]),
        sa.ForeignKeyConstraint(["span_id", "extraction_id", "organization_id", "workspace_id"],
            ["legal_source_spans.id", "legal_source_spans.extraction_id", "legal_source_spans.organization_id", "legal_source_spans.workspace_id"]),
        sa.UniqueConstraint("clause_id", "span_id", name="uq_legal_contract_clause_spans_link"))
    for name in ("legal_contract_findings", "legal_contract_obligation_proposals"):
        create(name, uid("analysis_id"), payload(), uid("requester_id", foreign="users.id"), string("revision_sha256", 64),
            parent("analysis_id", "legal_contract_analyses"), hash_check())
    create("legal_contract_playbooks", string("name", 200), string("version", 60), uid("owner_id", foreign="users.id"),
        sa.Column("legal_basis", sa.Text(), nullable=False), string("jurisdiction", 200),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True), string("revision_sha256", 64),
        sa.UniqueConstraint("workspace_id", "name", "version", name="uq_legal_contract_playbooks_version"), hash_check(),
        sa.CheckConstraint("effective_until IS NULL OR (effective_from IS NOT NULL AND effective_until > effective_from)", name="effective_interval"))
    create("legal_contract_playbook_rules", uid("playbook_id"), string("clause_type", 40), string("kind", 40), string("label", 300),
        string("pattern", 1000, nullable=True), parent("playbook_id", "legal_contract_playbooks"),
        sa.CheckConstraint("kind IN ('required_clause','forbidden_text')", name="kind"))
    create("legal_contract_summaries", uid("requester_id", foreign="users.id"), string("profile", 40), string("audience", 40),
        string("revision_sha256", 64), sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.UniqueConstraint("workspace_id", "requester_id", "revision_sha256", name="uq_legal_contract_summaries_replay"), hash_check())
    create("legal_contract_summary_spans", uid("summary_id"), uid("extraction_id"), uid("span_id"),
        parent("summary_id", "legal_contract_summaries"),
        sa.ForeignKeyConstraint(["span_id", "extraction_id", "organization_id", "workspace_id"],
            ["legal_source_spans.id", "legal_source_spans.extraction_id", "legal_source_spans.organization_id", "legal_source_spans.workspace_id"]),
        sa.UniqueConstraint("summary_id", "span_id", name="uq_legal_contract_summary_spans_link"))
    create("legal_contract_conversations", uid("owner_id", foreign="users.id"), uid("matter_id", nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"), sa.Column("messages", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id", "workspace_id", "matter_id"],
            ["legal_matters.organization_id", "legal_matters.workspace_id", "legal_matters.id"]))
    op.execute("""CREATE FUNCTION protect_legal_contract() RETURNS trigger AS $$ BEGIN
        RAISE EXCEPTION 'Legal contract revisions are immutable'; END; $$ LANGUAGE plpgsql""")
    for table in TABLES[:-1]:
        op.execute(f"CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION protect_legal_contract()")
        op.execute(f"CREATE TRIGGER immutable_truncate_{table} BEFORE TRUNCATE ON {table} FOR EACH STATEMENT EXECUTE FUNCTION protect_legal_contract()")


def downgrade():
    checks = " OR ".join(f"EXISTS (SELECT 1 FROM {table})" for table in TABLES)
    op.execute(f"DO $$ BEGIN IF {checks} THEN RAISE EXCEPTION 'Legal contract history exists; refusing lossy downgrade'; END IF; END $$")
    for table in reversed(TABLES):
        op.drop_table(table)
    op.execute("DROP FUNCTION protect_legal_contract()")
