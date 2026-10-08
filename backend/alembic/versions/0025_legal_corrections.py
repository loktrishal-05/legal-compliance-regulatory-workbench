"""Immutable scoped transcription corrections and independent exact-revision decisions."""
from alembic import op
import sqlalchemy as sa

revision = "0025_legal_corrections"
down_revision = "0024_legal_extraction"
branch_labels = None
depends_on = None
EVENTS = ("LEGAL_CORRECTION_PROPOSED", "LEGAL_CORRECTION_DECIDED")
QUOTED = ", ".join(f"''{name}''" for name in EVENTS)


def upgrade():
    op.create_unique_constraint("uq_legal_source_spans_lineage", "legal_source_spans",
        ["id", "extraction_id", "organization_id", "workspace_id"])
    op.create_table("legal_corrections",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        *(sa.Column(name, sa.Uuid(), nullable=False) for name in
            ("organization_id", "workspace_id", "span_id", "extraction_id", "idempotency_key")),
        sa.Column("parent_correction_id", sa.Uuid(), nullable=True),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("original_quote_sha256", sa.String(64), nullable=False),
        sa.Column("correction_sha256", sa.String(64), nullable=False),
        sa.Column("corrected_text", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["span_id", "extraction_id", "organization_id", "workspace_id"],
            ["legal_source_spans.id", "legal_source_spans.extraction_id", "legal_source_spans.organization_id",
             "legal_source_spans.workspace_id"], name="fk_legal_corrections_span_lineage"),
        sa.UniqueConstraint("id", "span_id", "organization_id", "workspace_id", name="uq_legal_corrections_parent_scope"),
        sa.ForeignKeyConstraint(["parent_correction_id", "span_id", "organization_id", "workspace_id"],
            ["legal_corrections.id", "legal_corrections.span_id", "legal_corrections.organization_id",
             "legal_corrections.workspace_id"], name="fk_legal_corrections_parent_scope"),
        sa.UniqueConstraint("id", "correction_sha256", "organization_id", "workspace_id", "actor_id", name="uq_legal_corrections_revision"),
        sa.UniqueConstraint("workspace_id", "actor_id", "idempotency_key", name="uq_legal_corrections_retry"),
        sa.CheckConstraint("length(original_quote_sha256) = 64 AND length(correction_sha256) = 64", name="hashes"),
        sa.CheckConstraint("length(corrected_text) BETWEEN 1 AND 64000 AND length(rationale) BETWEEN 1 AND 2000", name="text_bounds"),
        sa.CheckConstraint("parent_correction_id IS NULL OR parent_correction_id <> id", name="non_self_parent"))
    op.create_table("legal_correction_decisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        *(sa.Column(name, sa.Uuid(), nullable=False) for name in
            ("organization_id", "workspace_id", "correction_id", "requester_id")),
        sa.Column("reviewer_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("correction_sha256", sa.String(64), nullable=False),
        sa.Column("outcome", sa.String(20), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["correction_id", "correction_sha256", "organization_id", "workspace_id", "requester_id"],
            ["legal_corrections.id", "legal_corrections.correction_sha256", "legal_corrections.organization_id",
             "legal_corrections.workspace_id", "legal_corrections.actor_id"], name="fk_legal_correction_decisions_revision"),
        sa.UniqueConstraint("correction_id", name="uq_legal_correction_decisions_final"),
        sa.CheckConstraint("outcome IN ('approved','rejected')", name="outcome"),
        sa.CheckConstraint("length(rationale) BETWEEN 1 AND 2000", name="rationale"),
        sa.CheckConstraint("reviewer_id <> requester_id", name="independent_reviewer"))
    op.execute("""CREATE FUNCTION protect_legal_correction() RETURNS trigger AS $$ BEGIN
      RAISE EXCEPTION 'Legal correction records are immutable'; END; $$ LANGUAGE plpgsql""")
    for table in ("legal_corrections", "legal_correction_decisions"):
        op.execute(f"CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} "
                   "FOR EACH ROW EXECUTE FUNCTION protect_legal_correction()")
        op.execute(f"CREATE TRIGGER immutable_truncate_{table} BEFORE TRUNCATE ON {table} "
                   "FOR EACH STATEMENT EXECUTE FUNCTION protect_legal_correction()")
    op.execute(f"""DO $$ DECLARE definition text; BEGIN
      SELECT pg_get_constraintdef(oid) INTO definition FROM pg_constraint
      WHERE conrelid = 'audit_events'::regclass AND conname = 'ck_audit_events_event_type';
      ALTER TABLE audit_events DROP CONSTRAINT ck_audit_events_event_type;
      EXECUTE 'ALTER TABLE audit_events ADD CONSTRAINT ck_audit_events_event_type CHECK ('
        || substring(definition from 8 for length(definition)-8)
        || ' OR event_type IN ({QUOTED}))'; END $$""")


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM legal_corrections) OR EXISTS (SELECT 1 FROM legal_correction_decisions)
         OR EXISTS (SELECT 1 FROM audit_events WHERE event_type IN
                    ('LEGAL_CORRECTION_PROPOSED', 'LEGAL_CORRECTION_DECIDED')) THEN
        RAISE EXCEPTION 'Legal correction history exists; refusing lossy downgrade';
      END IF; END $$""")
    op.execute(f"""DO $$ DECLARE definition text; BEGIN
      SELECT pg_get_constraintdef(oid) INTO definition FROM pg_constraint
      WHERE conrelid = 'audit_events'::regclass AND conname = 'ck_audit_events_event_type';
      ALTER TABLE audit_events DROP CONSTRAINT ck_audit_events_event_type;
      EXECUTE 'ALTER TABLE audit_events ADD CONSTRAINT ck_audit_events_event_type CHECK ('
        || substring(definition from 8 for length(definition)-8)
        || ' AND event_type NOT IN ({QUOTED}))'; END $$""")
    op.drop_table("legal_correction_decisions")
    op.drop_table("legal_corrections")
    op.execute("DROP FUNCTION protect_legal_correction()")
    op.drop_constraint("uq_legal_source_spans_lineage", "legal_source_spans", type_="unique")
