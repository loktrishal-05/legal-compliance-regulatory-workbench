"""Extend audit vocabulary for legal access denials without changing old envelopes."""
from alembic import op

revision = "0020_legal_policy_audit"
down_revision = "0019_legal_scope"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""DO $$ DECLARE definition text; BEGIN
      SELECT pg_get_constraintdef(oid) INTO definition FROM pg_constraint
      WHERE conrelid = 'audit_events'::regclass AND conname = 'ck_audit_events_event_type';
      ALTER TABLE audit_events DROP CONSTRAINT ck_audit_events_event_type;
      EXECUTE 'ALTER TABLE audit_events ADD CONSTRAINT ck_audit_events_event_type CHECK ('
        || substring(definition from 8 for length(definition)-8)
        || ' OR event_type = ''SECURITY_POLICY_DENIED'')';
    END $$""")


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM audit_events WHERE event_type = 'SECURITY_POLICY_DENIED') THEN
        RAISE EXCEPTION 'Legal policy audit history exists; refusing lossy downgrade';
      END IF;
    END $$""")
    op.execute("""DO $$ DECLARE definition text; BEGIN
      SELECT pg_get_constraintdef(oid) INTO definition FROM pg_constraint
      WHERE conrelid = 'audit_events'::regclass AND conname = 'ck_audit_events_event_type';
      ALTER TABLE audit_events DROP CONSTRAINT ck_audit_events_event_type;
      EXECUTE 'ALTER TABLE audit_events ADD CONSTRAINT ck_audit_events_event_type CHECK ('
        || substring(definition from 8 for length(definition)-8)
        || ' AND event_type <> ''SECURITY_POLICY_DENIED'')';
    END $$""")
