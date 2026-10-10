"""Legal obligations, deadlines, tasks, remediation, exceptions, notifications, comments and evidence packs.
Owner: agent A (parallel build 2026-10-09)."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0031_legal_obligations"
down_revision = "0030_legal_compliance"
branch_labels = None
depends_on = None
TABLES = ("legal_evidence_packs", "legal_comments", "legal_dispatch_receipts", "legal_notifications",
          "legal_exceptions", "legal_remediations", "legal_task_dependencies", "legal_tasks",
          "legal_deadline_occurrences", "legal_obligations")
APPEND_ONLY = ("legal_evidence_packs", "legal_comments", "legal_dispatch_receipts")


def ident():
    return [sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("organization_id", sa.Uuid(), nullable=False),
            sa.Column("workspace_id", sa.Uuid(), nullable=False)]


def ws_fk():
    return sa.ForeignKeyConstraint(["organization_id", "workspace_id"],
                                   ["legal_workspaces.organization_id", "legal_workspaces.id"])


def member_fk(column, name):
    return sa.ForeignKeyConstraint(["organization_id", "workspace_id", column],
        ["legal_workspace_memberships.organization_id", "legal_workspace_memberships.workspace_id",
         "legal_workspace_memberships.user_id"], name=name)


def scoped_fk(column, table, name):
    return sa.ForeignKeyConstraint([column, "organization_id", "workspace_id"],
        [f"{table}.id", f"{table}.organization_id", f"{table}.workspace_id"], name=name)


def ts(name, nullable=True):
    return sa.Column(name, sa.DateTime(timezone=True), nullable=nullable)


def upgrade():
    op.create_table("legal_obligations", *ident(),
        *(sa.Column(n, sa.Uuid(), nullable=False) for n in
          ("proposal_id", "review_id", "source_event_id", "document_id", "version_id")),
        sa.Column("proposal_sha256", sa.String(64), nullable=False),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.Column("citations", JSONB(), nullable=False),
        *(sa.Column(n, sa.Text(), nullable=False) for n in
          ("actor_text", "action_text", "trigger_text", "original_deadline_phrase")),
        sa.Column("obligation_type", sa.String(40), nullable=False),
        sa.Column("conditions", JSONB(), nullable=False),
        sa.Column("uncertainties", JSONB(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=True),
        sa.Column("timezone", sa.String(64), nullable=True),
        ts("due_at"),
        sa.Column("date_only", sa.Boolean(), nullable=False),
        sa.Column("notice_days", sa.Integer(), nullable=False),
        sa.Column("recurrence_rule", sa.String(100), nullable=True),
        sa.Column("calendar_policy", sa.String(40), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("confirmed_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        ts("confirmed_at"),
        ws_fk(), member_fk("owner_id", "fk_legal_obligations_owner"),
        sa.UniqueConstraint("workspace_id", "proposal_id", "proposal_sha256", name="uq_legal_obligations_proposal"),
        sa.UniqueConstraint("id", "organization_id", "workspace_id", name="uq_legal_obligations_scope"),
        sa.CheckConstraint("status IN ('needs_confirmation','active','completed','impact_review')", name="status"),
        sa.CheckConstraint("notice_days BETWEEN 0 AND 365", name="notice_days"),
        sa.CheckConstraint("status = 'needs_confirmation' OR (timezone IS NOT NULL AND due_at IS NOT NULL)",
                           name="confirmed_deadline"))
    op.create_table("legal_deadline_occurrences", *ident(),
        sa.Column("obligation_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        ts("due_at", nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        scoped_fk("obligation_id", "legal_obligations", "fk_legal_deadline_occurrences_obligation"),
        sa.UniqueConstraint("obligation_id", "sequence", name="uq_legal_deadline_occurrences_key"),
        sa.CheckConstraint("status IN ('scheduled','done','cancelled')", name="status"))
    op.create_index("ix_legal_deadline_occurrences_due", "legal_deadline_occurrences", ["status", "due_at"])
    op.create_table("legal_tasks", *ident(),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=True),
        ts("due_at"),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("evidence_request", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        ws_fk(), member_fk("owner_id", "fk_legal_tasks_owner"),
        sa.UniqueConstraint("workspace_id", "source_type", "source_id", "kind", name="uq_legal_tasks_source"),
        sa.UniqueConstraint("id", "organization_id", "workspace_id", name="uq_legal_tasks_scope"),
        sa.CheckConstraint("kind IN ('obligation','remediation','evidence_request','evidence_expired',"
                           "'regulatory_change','exception_expired')", name="kind"),
        sa.CheckConstraint("status IN ('open','in_progress','submitted','done','cancelled')", name="status"))
    op.create_table("legal_task_dependencies",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), primary_key=True),
        sa.Column("depends_on_id", sa.Uuid(), primary_key=True),
        scoped_fk("task_id", "legal_tasks", "fk_legal_task_dependencies_task"),
        scoped_fk("depends_on_id", "legal_tasks", "fk_legal_task_dependencies_depends_on"),
        sa.CheckConstraint("task_id <> depends_on_id", name="no_self_dependency"))
    op.create_table("legal_remediations", *ident(),
        sa.Column("finding_id", sa.Uuid(), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=True),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("closure_evidence", JSONB(), nullable=False),
        sa.Column("closure_sha256", sa.String(64), nullable=True),
        sa.Column("retest_required", sa.Boolean(), nullable=False),
        sa.Column("retest_passed", sa.Boolean(), nullable=True),
        sa.Column("closed_review_id", sa.Uuid(), nullable=True),
        sa.Column("reopen_count", sa.Integer(), nullable=False),
        ws_fk(), scoped_fk("task_id", "legal_tasks", "fk_legal_remediations_task"),
        sa.UniqueConstraint("workspace_id", "finding_id", name="uq_legal_remediations_finding"),
        sa.CheckConstraint("status IN ('open','in_progress','submitted','closed','reopened')", name="status"),
        sa.CheckConstraint("status <> 'closed' OR (closure_sha256 IS NOT NULL AND closed_review_id IS NOT NULL)",
                           name="closure_needs_review"))
    op.create_table("legal_exceptions", *ident(),
        sa.Column("subject_type", sa.String(40), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        ts("expires_at", nullable=False),
        sa.Column("requester_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("exception_sha256", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        ws_fk(),
        sa.CheckConstraint("status IN ('proposed','active','expired','rejected')", name="status"),
        sa.CheckConstraint("length(rationale) BETWEEN 1 AND 4000", name="rationale"),
        sa.CheckConstraint("expires_at > created_at", name="future_expiry"))
    op.create_table("legal_notifications", *ident(),
        sa.Column("recipient_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("subject_type", sa.String(40), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("dedupe_key", sa.String(200), nullable=False),
        ts("read_at"),
        member_fk("recipient_id", "fk_legal_notifications_recipient"),
        sa.UniqueConstraint("workspace_id", "recipient_id", "dedupe_key", name="uq_legal_notifications_dedupe"))
    op.create_table("legal_dispatch_receipts",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("receipt_key", sa.String(200), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        ws_fk())
    op.create_table("legal_comments", *ident(),
        sa.Column("subject_type", sa.String(40), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("mentions", JSONB(), nullable=False),
        ws_fk(), sa.CheckConstraint("length(body) BETWEEN 1 AND 4000", name="body"))
    op.create_table("legal_evidence_packs", *ident(),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("manifest", JSONB(), nullable=False),
        sa.Column("manifest_sha256", sa.String(64), nullable=False),
        ws_fk(), sa.CheckConstraint("kind IN ('evidence_pack','findings_export')", name="kind"))
    op.execute("""CREATE FUNCTION protect_legal_append_only() RETURNS trigger AS $$ BEGIN
      RAISE EXCEPTION 'Legal comments, receipts and evidence packs are append-only'; END; $$ LANGUAGE plpgsql""")
    for table in APPEND_ONLY:
        op.execute(f"CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} "
                   "FOR EACH ROW EXECUTE FUNCTION protect_legal_append_only()")
        op.execute(f"CREATE TRIGGER immutable_truncate_{table} BEFORE TRUNCATE ON {table} "
                   "FOR EACH STATEMENT EXECUTE FUNCTION protect_legal_append_only()")


def downgrade():
    checks = " OR ".join(f"EXISTS (SELECT 1 FROM {table})" for table in TABLES)
    op.execute(f"""DO $$ BEGIN IF {checks} THEN
        RAISE EXCEPTION 'Legal obligation/workflow history exists; refusing lossy downgrade';
      END IF; END $$""")
    for table in TABLES:
        op.drop_table(table)
    op.execute("DROP FUNCTION protect_legal_append_only()")
