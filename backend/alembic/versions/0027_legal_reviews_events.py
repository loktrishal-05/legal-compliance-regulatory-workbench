"""Legal exact-revision reviews, transactional outbox and scheduler receipts. Owner: agent A (parallel build 2026-10-09)."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0027_legal_reviews_events"
down_revision = "0026_legal_jobs"
branch_labels = None
depends_on = None
EVENTS = ("LEGAL_REVIEW_REQUESTED", "LEGAL_REVIEW_DECIDED", "LEGAL_ACTIVITY_RECORDED")
WS_FK = (["organization_id", "workspace_id"], ["legal_workspaces.organization_id", "legal_workspaces.id"])


def audit_vocabulary(events, add):
    """Widen/narrow the audit event CHECK without touching old rows (pattern from 0025)."""
    quoted = ", ".join(f"''{name}''" for name in events)
    joiner = "OR event_type IN" if add else "AND event_type NOT IN"
    op.execute(f"""DO $$ DECLARE definition text; BEGIN
      SELECT pg_get_constraintdef(oid) INTO definition FROM pg_constraint
      WHERE conrelid = 'audit_events'::regclass AND conname = 'ck_audit_events_event_type';
      ALTER TABLE audit_events DROP CONSTRAINT ck_audit_events_event_type;
      EXECUTE 'ALTER TABLE audit_events ADD CONSTRAINT ck_audit_events_event_type CHECK ('
        || substring(definition from 8 for length(definition)-8)
        || ' {joiner} ({quoted}))'; END $$""")


def ts(name):
    return sa.Column(name, sa.DateTime(timezone=True), nullable=True)


def upgrade():
    op.create_table("legal_reviews",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.String(60), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("target_revision_sha256", sa.String(64), nullable=False),
        sa.Column("requester_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.ForeignKeyConstraint(*WS_FK),
        sa.UniqueConstraint("workspace_id", "requester_id", "idempotency_key", name="uq_legal_reviews_retry"),
        sa.UniqueConstraint("workspace_id", "target_type", "target_id", "target_revision_sha256",
                            name="uq_legal_reviews_revision"),
        sa.UniqueConstraint("id", "organization_id", "workspace_id", "requester_id", name="uq_legal_reviews_scope"),
        sa.CheckConstraint("length(target_revision_sha256) = 64", name="revision_hash"),
        sa.CheckConstraint("length(idempotency_key) BETWEEN 1 AND 200", name="idempotency_key"))
    op.create_table("legal_review_decisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        *(sa.Column(name, sa.Uuid(), nullable=False) for name in
          ("organization_id", "workspace_id", "review_id", "requester_id")),
        sa.Column("reviewer_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("decision", sa.String(20), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["review_id", "organization_id", "workspace_id", "requester_id"],
            ["legal_reviews.id", "legal_reviews.organization_id", "legal_reviews.workspace_id",
             "legal_reviews.requester_id"], name="fk_legal_review_decisions_review"),
        sa.CheckConstraint("decision IN ('approve','reject','request_changes','escalate')", name="decision"),
        sa.CheckConstraint("length(rationale) BETWEEN 1 AND 2000", name="rationale"),
        sa.CheckConstraint("reviewer_id <> requester_id", name="independent_reviewer"))
    op.create_index("uq_legal_review_decisions_terminal", "legal_review_decisions", ["review_id"], unique=True,
                    postgresql_where=sa.text("decision <> 'escalate'"))
    op.create_table("legal_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column("payload_sha256", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        ts("next_attempt_at"), sa.Column("lease_owner", sa.String(100), nullable=True), ts("lease_expires_at"),
        sa.Column("last_error_code", sa.String(80), nullable=True), ts("dispatched_at"),
        sa.ForeignKeyConstraint(*WS_FK),
        sa.UniqueConstraint("workspace_id", "event_type", "idempotency_key", name="uq_legal_events_retry"),
        sa.CheckConstraint("status IN ('pending','dispatched','dead_letter')", name="status"),
        sa.CheckConstraint("attempts >= 0", name="attempts"))
    op.create_index("ix_legal_events_due", "legal_events", ["status", "next_attempt_at"])
    op.create_table("legal_scheduler_scans",
        sa.Column("name", sa.String(80), primary_key=True),
        ts("last_started_at"), ts("last_success_at"),
        sa.Column("last_count", sa.Integer(), nullable=False),
        sa.Column("last_error_code", sa.String(80), nullable=True),
        sa.Column("runs", sa.Integer(), nullable=False))
    op.execute("""CREATE FUNCTION protect_legal_review() RETURNS trigger AS $$ BEGIN
      RAISE EXCEPTION 'Legal review records are immutable'; END; $$ LANGUAGE plpgsql""")
    for table in ("legal_reviews", "legal_review_decisions"):
        op.execute(f"CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} "
                   "FOR EACH ROW EXECUTE FUNCTION protect_legal_review()")
        op.execute(f"CREATE TRIGGER immutable_truncate_{table} BEFORE TRUNCATE ON {table} "
                   "FOR EACH STATEMENT EXECUTE FUNCTION protect_legal_review()")
    op.execute("""CREATE FUNCTION protect_legal_event() RETURNS trigger AS $$ BEGIN
      IF TG_OP = 'DELETE' OR NEW.payload IS DISTINCT FROM OLD.payload
         OR NEW.payload_sha256 IS DISTINCT FROM OLD.payload_sha256 OR NEW.event_type IS DISTINCT FROM OLD.event_type
         OR NEW.idempotency_key IS DISTINCT FROM OLD.idempotency_key OR NEW.workspace_id IS DISTINCT FROM OLD.workspace_id
         OR NEW.organization_id IS DISTINCT FROM OLD.organization_id THEN
        RAISE EXCEPTION 'Legal event payload is immutable';
      END IF; RETURN NEW; END; $$ LANGUAGE plpgsql""")
    op.execute("CREATE TRIGGER immutable_legal_events BEFORE UPDATE OR DELETE ON legal_events "
               "FOR EACH ROW EXECUTE FUNCTION protect_legal_event()")
    audit_vocabulary(EVENTS, add=True)


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM legal_reviews) OR EXISTS (SELECT 1 FROM legal_events)
         OR EXISTS (SELECT 1 FROM audit_events WHERE event_type IN
                    ('LEGAL_REVIEW_REQUESTED', 'LEGAL_REVIEW_DECIDED', 'LEGAL_ACTIVITY_RECORDED')) THEN
        RAISE EXCEPTION 'Legal review/event history exists; refusing lossy downgrade';
      END IF; END $$""")
    audit_vocabulary(EVENTS, add=False)
    for table in ("legal_scheduler_scans", "legal_events", "legal_review_decisions", "legal_reviews"):
        op.drop_table(table)
    op.execute("DROP FUNCTION protect_legal_event()")
    op.execute("DROP FUNCTION protect_legal_review()")
