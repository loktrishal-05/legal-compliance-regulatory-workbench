"""Workspace-qualified regulatory registry and immutable source history."""
from alembic import op
import sqlalchemy as sa

revision = "0029_legal_regulatory"
down_revision = "0028_legal_contracts"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('legal_regulatory_sources',
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=False),
    sa.Column('actor_id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('jurisdiction', sa.String(length=100), nullable=False),
    sa.Column('authority_tier', sa.String(length=30), nullable=False),
    sa.Column('trust_state', sa.String(length=20), server_default='proposed', nullable=False),
    sa.Column('import_policy', sa.String(length=20), server_default='manual', nullable=False),
    sa.Column('revision_sha256', sa.String(length=64), nullable=False),
    sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_failure_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_check_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("authority_tier IN ('unverified','primary','secondary')", name=op.f('ck_legal_regulatory_sources_authority_tier')),
    sa.CheckConstraint("import_policy = 'manual'", name=op.f('ck_legal_regulatory_sources_import_policy')),
    sa.CheckConstraint("trust_state IN ('proposed','approved','rejected')", name=op.f('ck_legal_regulatory_sources_trust_state')),
    sa.CheckConstraint('length(revision_sha256) = 64', name=op.f('ck_legal_regulatory_sources_revision_hash')),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_legal_regulatory_sources_actor_id_users')),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'owner_id'], ['legal_workspace_memberships.organization_id', 'legal_workspace_memberships.workspace_id', 'legal_workspace_memberships.user_id'], name=op.f('fk_legal_regulatory_sources_organization_id_legal_workspace_memberships')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_regulatory_sources')),
    sa.UniqueConstraint('organization_id', 'workspace_id', 'id', name=op.f('uq_legal_regulatory_sources_organization_id'))
    )
    op.create_table('legal_regulatory_documents',
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('source_id', sa.Uuid(), nullable=False),
    sa.Column('title', sa.String(length=250), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'source_id'], ['legal_regulatory_sources.organization_id', 'legal_regulatory_sources.workspace_id', 'legal_regulatory_sources.id'], name=op.f('fk_legal_regulatory_documents_organization_id_legal_regulatory_sources')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_regulatory_documents')),
    sa.UniqueConstraint('organization_id', 'workspace_id', 'id', name=op.f('uq_legal_regulatory_documents_organization_id'))
    )
    op.create_table('legal_regulatory_versions',
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('regulatory_document_id', sa.Uuid(), nullable=False),
    sa.Column('document_id', sa.Uuid(), nullable=False),
    sa.Column('version_id', sa.Uuid(), nullable=False),
    sa.Column('extraction_id', sa.Uuid(), nullable=False),
    sa.Column('source_sha256', sa.String(length=64), nullable=False),
    sa.Column('actor_id', sa.Uuid(), nullable=False),
    sa.Column('published_at', sa.Date(), nullable=True),
    sa.Column('effective_from', sa.Date(), nullable=True),
    sa.Column('effective_until', sa.Date(), nullable=True),
    sa.Column('imported_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('amends_id', sa.Uuid(), nullable=True),
    sa.Column('supersedes_id', sa.Uuid(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('effective_until IS NULL OR effective_from IS NULL OR effective_until > effective_from', name=op.f('ck_legal_regulatory_versions_effective_interval')),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_legal_regulatory_versions_actor_id_users')),
    sa.ForeignKeyConstraint(['extraction_id', 'organization_id', 'workspace_id'], ['legal_extractions.id', 'legal_extractions.organization_id', 'legal_extractions.workspace_id'], name=op.f('fk_legal_regulatory_versions_extraction_id_legal_extractions')),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'document_id', 'version_id', 'source_sha256'], ['document_versions.organization_id', 'document_versions.workspace_id', 'document_versions.document_id', 'document_versions.id', 'document_versions.source_sha256'], name=op.f('fk_legal_regulatory_versions_organization_id_document_versions')),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'regulatory_document_id', 'amends_id'], ['legal_regulatory_versions.organization_id', 'legal_regulatory_versions.workspace_id', 'legal_regulatory_versions.regulatory_document_id', 'legal_regulatory_versions.id'], name='fk_regulatory_version_amends'),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'regulatory_document_id', 'supersedes_id'], ['legal_regulatory_versions.organization_id', 'legal_regulatory_versions.workspace_id', 'legal_regulatory_versions.regulatory_document_id', 'legal_regulatory_versions.id'], name='fk_regulatory_version_supersedes'),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'regulatory_document_id'], ['legal_regulatory_documents.organization_id', 'legal_regulatory_documents.workspace_id', 'legal_regulatory_documents.id'], name=op.f('fk_legal_regulatory_versions_organization_id_legal_regulatory_documents')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_regulatory_versions')),
    sa.UniqueConstraint('organization_id', 'workspace_id', 'id', name=op.f('uq_legal_regulatory_versions_organization_id')),
    sa.UniqueConstraint('organization_id', 'workspace_id', 'regulatory_document_id', 'id', name='uq_regulatory_version_document'),
    sa.UniqueConstraint('regulatory_document_id', 'version_id', name=op.f('uq_legal_regulatory_versions_regulatory_document_id'))
    )
    op.create_table('legal_regulatory_changes',
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('regulatory_document_id', sa.Uuid(), nullable=False),
    sa.Column('from_version_id', sa.Uuid(), nullable=False),
    sa.Column('to_version_id', sa.Uuid(), nullable=False),
    sa.Column('actor_id', sa.Uuid(), nullable=False),
    sa.Column('exact_diff', sa.JSON(), nullable=False),
    sa.Column('semantic_proposal', sa.JSON(), nullable=False),
    sa.Column('revision_sha256', sa.String(length=64), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('from_version_id <> to_version_id', name=op.f('ck_legal_regulatory_changes_different_versions')),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_legal_regulatory_changes_actor_id_users')),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'regulatory_document_id', 'from_version_id'], ['legal_regulatory_versions.organization_id', 'legal_regulatory_versions.workspace_id', 'legal_regulatory_versions.regulatory_document_id', 'legal_regulatory_versions.id'], name='fk_regulatory_change_from_version_id'),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'regulatory_document_id', 'to_version_id'], ['legal_regulatory_versions.organization_id', 'legal_regulatory_versions.workspace_id', 'legal_regulatory_versions.regulatory_document_id', 'legal_regulatory_versions.id'], name='fk_regulatory_change_to_version_id'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_regulatory_changes')),
    sa.UniqueConstraint('from_version_id', 'to_version_id', name=op.f('uq_legal_regulatory_changes_from_version_id')),
    sa.UniqueConstraint('organization_id', 'workspace_id', 'id', name=op.f('uq_legal_regulatory_changes_organization_id'))
    )
    op.create_table('legal_regulatory_applicability',
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('regulatory_version_id', sa.Uuid(), nullable=False),
    sa.Column('actor_id', sa.Uuid(), nullable=False),
    sa.Column('state', sa.String(length=20), nullable=False),
    sa.Column('jurisdiction', sa.String(length=100), nullable=False),
    sa.Column('entity', sa.String(length=200), nullable=False),
    sa.Column('product', sa.String(length=200), nullable=False),
    sa.Column('business_unit', sa.String(length=200), nullable=False),
    sa.Column('rationale', sa.Text(), nullable=False),
    sa.Column('effective_on', sa.Date(), nullable=False),
    sa.Column('revision_sha256', sa.String(length=64), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("state IN ('applicable','not_applicable')", name=op.f('ck_legal_regulatory_applicability_state')),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_legal_regulatory_applicability_actor_id_users')),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'regulatory_version_id'], ['legal_regulatory_versions.organization_id', 'legal_regulatory_versions.workspace_id', 'legal_regulatory_versions.id'], name=op.f('fk_legal_regulatory_applicability_organization_id_legal_regulatory_versions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_regulatory_applicability')),
    sa.UniqueConstraint('organization_id', 'workspace_id', 'id', name=op.f('uq_legal_regulatory_applicability_organization_id'))
    )
    op.create_table('legal_regulatory_watchlists',
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('source_id', sa.Uuid(), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=False),
    sa.Column('max_age_days', sa.Integer(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('max_age_days BETWEEN 1 AND 3650', name=op.f('ck_legal_regulatory_watchlists_max_age_days')),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'owner_id'], ['legal_workspace_memberships.organization_id', 'legal_workspace_memberships.workspace_id', 'legal_workspace_memberships.user_id'], name=op.f('fk_legal_regulatory_watchlists_organization_id_legal_workspace_memberships')),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'source_id'], ['legal_regulatory_sources.organization_id', 'legal_regulatory_sources.workspace_id', 'legal_regulatory_sources.id'], name=op.f('fk_legal_regulatory_watchlists_organization_id_legal_regulatory_sources')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_regulatory_watchlists')),
    sa.UniqueConstraint('source_id', 'owner_id', name=op.f('uq_legal_regulatory_watchlists_source_id'))
    )
    op.create_table('legal_regulatory_campaigns',
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('change_id', sa.Uuid(), nullable=False),
    sa.Column('affected', sa.JSON(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'change_id'], ['legal_regulatory_changes.organization_id', 'legal_regulatory_changes.workspace_id', 'legal_regulatory_changes.id'], name=op.f('fk_legal_regulatory_campaigns_organization_id_legal_regulatory_changes')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_regulatory_campaigns')),
    sa.UniqueConstraint('change_id', name=op.f('uq_legal_regulatory_campaigns_change_id'))
    )

    op.execute("""CREATE FUNCTION protect_legal_regulatory_history() RETURNS trigger AS $$ BEGIN
      RAISE EXCEPTION 'Regulatory history is immutable'; END; $$ LANGUAGE plpgsql""")
    for table in ("legal_regulatory_versions", "legal_regulatory_changes",
                  "legal_regulatory_applicability", "legal_regulatory_campaigns"):
        op.execute(f"CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} "
                   "FOR EACH ROW EXECUTE FUNCTION protect_legal_regulatory_history()")
        op.execute(f"CREATE TRIGGER immutable_truncate_{table} BEFORE TRUNCATE ON {table} "
                   "FOR EACH STATEMENT EXECUTE FUNCTION protect_legal_regulatory_history()")


def downgrade():
    tables = ("legal_regulatory_campaigns", "legal_regulatory_watchlists", "legal_regulatory_applicability",
              "legal_regulatory_changes", "legal_regulatory_versions", "legal_regulatory_documents", "legal_regulatory_sources")
    for table in tables:
        op.execute(f"""DO $$ BEGIN IF EXISTS (SELECT 1 FROM {table}) THEN
          RAISE EXCEPTION 'Regulatory history exists; refusing lossy downgrade'; END IF; END $$""")
    for table in tables:
        op.drop_table(table)
    op.execute("DROP FUNCTION protect_legal_regulatory_history()")
