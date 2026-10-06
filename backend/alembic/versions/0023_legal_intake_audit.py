"""Extend audit vocabulary for secure legal intake without changing old envelopes."""
from alembic import op

revision = "0023_legal_intake_audit"
down_revision = "0022_legal_version_scope"
branch_labels = None
depends_on = None

EVENTS = ("LEGAL_DOCUMENT_RECEIVED", "LEGAL_INTAKE_REJECTED")
_SQL_LIST = ", ".join(f"'{event}'" for event in EVENTS)
_QUOTED_LIST = _SQL_LIST.replace("'", "''")  # inside EXECUTE string literal


def upgrade():
    op.execute(f"""DO $$ DECLARE definition text; BEGIN
      SELECT pg_get_constraintdef(oid) INTO definition FROM pg_constraint
      WHERE conrelid = 'audit_events'::regclass AND conname = 'ck_audit_events_event_type';
      ALTER TABLE audit_events DROP CONSTRAINT ck_audit_events_event_type;
      EXECUTE 'ALTER TABLE audit_events ADD CONSTRAINT ck_audit_events_event_type CHECK ('
        || substring(definition from 8 for length(definition)-8)
        || ' OR event_type IN ({_QUOTED_LIST}))';
    END $$""")


def downgrade():
    op.execute(f"""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM audit_events WHERE event_type IN ({_SQL_LIST})) THEN
        RAISE EXCEPTION 'Legal intake audit history exists; refusing lossy downgrade';
      END IF;
    END $$""")
    op.execute(f"""DO $$ DECLARE definition text; BEGIN
      SELECT pg_get_constraintdef(oid) INTO definition FROM pg_constraint
      WHERE conrelid = 'audit_events'::regclass AND conname = 'ck_audit_events_event_type';
      ALTER TABLE audit_events DROP CONSTRAINT ck_audit_events_event_type;
      EXECUTE 'ALTER TABLE audit_events ADD CONSTRAINT ck_audit_events_event_type CHECK ('
        || substring(definition from 8 for length(definition)-8)
        || ' AND event_type NOT IN ({_QUOTED_LIST}))';
    END $$""")
