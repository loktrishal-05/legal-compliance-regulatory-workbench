"""Immutable tenant/source-bound native extraction and spans; no ownership backfill."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0024_legal_extraction"
down_revision = "0023_legal_intake_audit"
branch_labels = None
depends_on = None
EVENTS = ("LEGAL_DOCUMENT_EXTRACTED", "LEGAL_EXTRACTION_FAILED")
QUOTED = ", ".join(f"''{name}''" for name in EVENTS)


def upgrade():
    op.create_unique_constraint("uq_document_versions_legal_lineage", "document_versions",
        ["organization_id", "workspace_id", "document_id", "id", "source_sha256"])
    op.create_table("legal_extractions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        *(sa.Column(name, sa.Uuid(), nullable=False) for name in
          ("organization_id", "workspace_id", "document_id", "version_id")),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.Column("policy_version", sa.String(60), nullable=False),
        sa.Column("extractor", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("artifact_sha256", sa.String(64), nullable=False),
        sa.Column("warnings", postgresql.JSONB(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id", "workspace_id", "document_id", "version_id", "source_sha256"],
            ["document_versions.organization_id", "document_versions.workspace_id", "document_versions.document_id",
             "document_versions.id", "document_versions.source_sha256"], name="fk_legal_extractions_source_version"),
        sa.UniqueConstraint("version_id", "policy_version", name="uq_legal_extractions_version_policy"),
        sa.UniqueConstraint("id", "organization_id", "workspace_id", name="uq_legal_extractions_scope"),
        sa.CheckConstraint("status IN ('ready','needs_verification')", name="status"),
        sa.CheckConstraint("length(source_sha256) = 64 AND length(artifact_sha256) = 64", name="hashes"))
    op.create_table("legal_source_spans",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        *(sa.Column(name, sa.Uuid(), nullable=False) for name in ("organization_id", "workspace_id", "extraction_id")),
        sa.Column("start", sa.Integer(), nullable=False), sa.Column("end", sa.Integer(), nullable=False),
        sa.Column("locator", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(["extraction_id", "organization_id", "workspace_id"],
            ["legal_extractions.id", "legal_extractions.organization_id", "legal_extractions.workspace_id"],
            name="fk_legal_source_spans_extraction_scope"),
        sa.UniqueConstraint("extraction_id", "start", name="uq_legal_source_spans_start"),
        sa.CheckConstraint('start >= 0 AND "end" > start', name="offsets"))
    op.execute("""CREATE FUNCTION protect_legal_extraction() RETURNS trigger AS $$ BEGIN
      RAISE EXCEPTION 'Legal extractions and source spans are immutable'; END; $$ LANGUAGE plpgsql""")
    for table in ("legal_extractions", "legal_source_spans"):
        op.execute(f"CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} "
                   "FOR EACH ROW EXECUTE FUNCTION protect_legal_extraction()")
        op.execute(f"CREATE TRIGGER immutable_truncate_{table} BEFORE TRUNCATE ON {table} "
                   "FOR EACH STATEMENT EXECUTE FUNCTION protect_legal_extraction()")
    op.execute(f"""DO $$ DECLARE definition text; BEGIN
      SELECT pg_get_constraintdef(oid) INTO definition FROM pg_constraint
      WHERE conrelid = 'audit_events'::regclass AND conname = 'ck_audit_events_event_type';
      ALTER TABLE audit_events DROP CONSTRAINT ck_audit_events_event_type;
      EXECUTE 'ALTER TABLE audit_events ADD CONSTRAINT ck_audit_events_event_type CHECK ('
        || substring(definition from 8 for length(definition)-8)
        || ' OR event_type IN ({QUOTED}))'; END $$""")


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM legal_extractions) OR EXISTS (SELECT 1 FROM legal_source_spans)
         OR EXISTS (SELECT 1 FROM audit_events WHERE event_type IN
                    ('LEGAL_DOCUMENT_EXTRACTED', 'LEGAL_EXTRACTION_FAILED')) THEN
        RAISE EXCEPTION 'Legal extraction history exists; refusing lossy downgrade';
      END IF; END $$""")
    op.execute(f"""DO $$ DECLARE definition text; BEGIN
      SELECT pg_get_constraintdef(oid) INTO definition FROM pg_constraint
      WHERE conrelid = 'audit_events'::regclass AND conname = 'ck_audit_events_event_type';
      ALTER TABLE audit_events DROP CONSTRAINT ck_audit_events_event_type;
      EXECUTE 'ALTER TABLE audit_events ADD CONSTRAINT ck_audit_events_event_type CHECK ('
        || substring(definition from 8 for length(definition)-8)
        || ' AND event_type NOT IN ({QUOTED}))'; END $$""")
    op.drop_table("legal_source_spans")
    op.drop_table("legal_extractions")
    op.execute("DROP FUNCTION protect_legal_extraction()")
    op.drop_constraint("uq_document_versions_legal_lineage", "document_versions", type_="unique")
