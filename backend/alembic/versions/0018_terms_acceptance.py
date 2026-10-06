"""Explicit terms acceptance and its mandatory audit event."""
from alembic import op
import sqlalchemy as sa

revision = "0018_terms_acceptance"
down_revision = "0017_accounts_recovery"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("terms_version", sa.String(40)))
    op.add_column("users", sa.Column("terms_accepted_at", sa.DateTime(timezone=True)))
    op.add_column("users", sa.Column("terms_request_host", sa.String(255)))
    op.create_check_constraint("terms_acceptance_complete", "users",
        "(terms_version IS NULL AND terms_accepted_at IS NULL AND terms_request_host IS NULL) OR "
        "(terms_version IS NOT NULL AND terms_accepted_at IS NOT NULL)")
    # Extend the installed vocabulary without importing mutable application models.
    op.execute("""DO $$ DECLARE definition text; BEGIN
      SELECT pg_get_constraintdef(oid) INTO definition FROM pg_constraint
      WHERE conrelid = 'audit_events'::regclass AND conname = 'ck_audit_events_event_type';
      ALTER TABLE audit_events DROP CONSTRAINT ck_audit_events_event_type;
      EXECUTE 'ALTER TABLE audit_events ADD CONSTRAINT ck_audit_events_event_type CHECK ('
        || substring(definition from 8 for length(definition)-8)
        || ' OR event_type = ''TERMS_ACCEPTED'')';
    END $$""")


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM users WHERE terms_version IS NOT NULL)
      OR EXISTS (SELECT 1 FROM audit_events WHERE event_type = 'TERMS_ACCEPTED') THEN
        RAISE EXCEPTION 'Terms acceptance history exists; refusing lossy downgrade';
      END IF;
    END $$""")
    op.execute("""DO $$ DECLARE definition text; BEGIN
      SELECT pg_get_constraintdef(oid) INTO definition FROM pg_constraint
      WHERE conrelid = 'audit_events'::regclass AND conname = 'ck_audit_events_event_type';
      ALTER TABLE audit_events DROP CONSTRAINT ck_audit_events_event_type;
      EXECUTE 'ALTER TABLE audit_events ADD CONSTRAINT ck_audit_events_event_type CHECK ('
        || substring(definition from 8 for length(definition)-8)
        || ' AND event_type <> ''TERMS_ACCEPTED'')';
    END $$""")
    op.drop_constraint(op.f("ck_users_terms_acceptance_complete"), "users", type_="check")
    for column in ("terms_request_host", "terms_accepted_at", "terms_version"):
        op.drop_column("users", column)
