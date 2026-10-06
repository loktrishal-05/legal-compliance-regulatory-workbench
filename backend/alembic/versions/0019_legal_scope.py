"""Add legal ownership/ACL tables without assigning or modifying legacy records."""
from alembic import op
import sqlalchemy as sa

revision = "0019_legal_scope"
down_revision = "0018_terms_acceptance"
branch_labels = None
depends_on = None


def _created_active():
    return [sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true())]


def upgrade():
    op.create_table("legal_organizations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False), *_created_active())
    op.create_table("legal_workspaces",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("legal_organizations.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False), *_created_active(),
        sa.UniqueConstraint("organization_id", "id"))
    op.create_table("legal_workspace_memberships",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("role", sa.String(40), nullable=False),
        sa.Column("clearance", sa.String(20), nullable=False, server_default="public"), *_created_active(),
        sa.ForeignKeyConstraint(["organization_id", "workspace_id"],
                                ["legal_workspaces.organization_id", "legal_workspaces.id"]),
        sa.UniqueConstraint("organization_id", "workspace_id", "user_id"),
        sa.CheckConstraint("role IN ('analyst','legal_reviewer','compliance_reviewer','business_owner',"
                           "'auditor','workspace_admin','viewer')", name="role"),
        sa.CheckConstraint("clearance IN ('public','internal','confidential','restricted')", name="clearance"))
    op.create_table("legal_matters",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False), *_created_active(),
        sa.ForeignKeyConstraint(["organization_id", "workspace_id"],
                                ["legal_workspaces.organization_id", "legal_workspaces.id"]),
        sa.UniqueConstraint("organization_id", "workspace_id", "id"))
    op.create_table("legal_matter_access",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("matter_id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), primary_key=True), *_created_active(),
        sa.ForeignKeyConstraint(["organization_id", "workspace_id", "matter_id"],
            ["legal_matters.organization_id", "legal_matters.workspace_id", "legal_matters.id"]),
        sa.ForeignKeyConstraint(["organization_id", "workspace_id", "user_id"],
            ["legal_workspace_memberships.organization_id", "legal_workspace_memberships.workspace_id",
             "legal_workspace_memberships.user_id"]))
    op.create_table("legal_document_scopes",
        sa.Column("document_id", sa.Uuid(), sa.ForeignKey("documents.id"), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("matter_id", sa.Uuid(), nullable=True),
        sa.Column("classification", sa.String(20), nullable=False),
        sa.Column("legal_hold", sa.Boolean(), nullable=False, server_default=sa.false()), *_created_active(),
        sa.ForeignKeyConstraint(["organization_id", "workspace_id"],
                                ["legal_workspaces.organization_id", "legal_workspaces.id"]),
        sa.ForeignKeyConstraint(["organization_id", "workspace_id", "matter_id"],
            ["legal_matters.organization_id", "legal_matters.workspace_id", "legal_matters.id"]),
        sa.UniqueConstraint("organization_id", "workspace_id", "document_id"),
        sa.CheckConstraint("classification IN ('public','internal','confidential','restricted')", name="classification"))
    op.create_table("legal_document_access",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), primary_key=True),
        sa.Column("operation", sa.String(30), primary_key=True), *_created_active(),
        sa.ForeignKeyConstraint(["organization_id", "workspace_id", "document_id"],
            ["legal_document_scopes.organization_id", "legal_document_scopes.workspace_id",
             "legal_document_scopes.document_id"]),
        sa.ForeignKeyConstraint(["organization_id", "workspace_id", "user_id"],
            ["legal_workspace_memberships.organization_id", "legal_workspace_memberships.workspace_id",
             "legal_workspace_memberships.user_id"]),
        sa.CheckConstraint("operation IN ('read','propose','review_legal','review_compliance')", name="operation"))


def downgrade():
    # Access/ownership history must not disappear just because schema rollback was requested.
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM legal_organizations) THEN
        RAISE EXCEPTION 'Legal ownership history exists; refusing lossy downgrade';
      END IF;
    END $$""")
    for table in ("legal_document_access", "legal_document_scopes", "legal_matter_access",
                  "legal_matters", "legal_workspace_memberships", "legal_workspaces", "legal_organizations"):
        op.drop_table(table)
