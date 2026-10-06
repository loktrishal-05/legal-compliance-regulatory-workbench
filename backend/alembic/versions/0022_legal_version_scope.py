"""Workspace-scoped source dedupe: legacy versions keep global uniqueness, legal versions are per workspace.

No backfill: existing versions stay legacy (NULL workspace). A scoped version must belong to a document
scoped to the same workspace (composite FK). Downgrade refuses once any scoped version exists.
"""
from alembic import op
import sqlalchemy as sa

revision = "0022_legal_version_scope"
down_revision = "0021_legal_provisioning_audit"
branch_labels = None
depends_on = None

LEGACY = "ux_document_versions_legacy_source_sha256"
SCOPED = "ux_document_versions_workspace_source_sha256"


def upgrade():
    op.add_column("document_versions", sa.Column("organization_id", sa.Uuid(), nullable=True))
    op.add_column("document_versions", sa.Column("workspace_id", sa.Uuid(), nullable=True))
    op.create_check_constraint("ck_document_versions_legal_scope_pair", "document_versions",
                               "(organization_id IS NULL) = (workspace_id IS NULL)")
    op.create_foreign_key("fk_document_versions_organization_id_legal_document_scopes", "document_versions",
                          "legal_document_scopes", ["organization_id", "workspace_id", "document_id"],
                          ["organization_id", "workspace_id", "document_id"])
    op.drop_constraint("uq_document_versions_source_sha256", "document_versions", type_="unique")
    op.create_index(LEGACY, "document_versions", ["source_sha256"], unique=True,
                    postgresql_where=sa.text("workspace_id IS NULL"))
    op.create_index(SCOPED, "document_versions", ["organization_id", "workspace_id", "source_sha256"], unique=True,
                    postgresql_where=sa.text("workspace_id IS NOT NULL"))


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM document_versions WHERE workspace_id IS NOT NULL) THEN
        RAISE EXCEPTION 'Workspace-scoped document versions exist; refusing lossy downgrade';
      END IF;
    END $$""")
    op.drop_index(SCOPED, table_name="document_versions")
    op.drop_index(LEGACY, table_name="document_versions")
    op.create_unique_constraint("uq_document_versions_source_sha256", "document_versions", ["source_sha256"])
    op.drop_constraint("fk_document_versions_organization_id_legal_document_scopes", "document_versions",
                       type_="foreignkey")
    op.drop_constraint("ck_document_versions_legal_scope_pair", "document_versions", type_="check")
    op.drop_column("document_versions", "workspace_id")
    op.drop_column("document_versions", "organization_id")
