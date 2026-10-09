"""Legal compliance requirements, policies, controls, evidence, mappings, rules, assessments and findings.
Owner: agent C (parallel build 2026-10-09); filled from C's models by agent A. Append-only history tables are
trigger-protected like 0024/0025; downgrade refuses to remove compliance data."""
from alembic import op
import sqlalchemy as sa

revision = "0030_legal_compliance"
down_revision = "0029_legal_regulatory"
branch_labels = None
depends_on = None
TABLES = ['legal_compliance_evidence', 'legal_compliance_policies', 'legal_compliance_controls', 'legal_compliance_evidence_versions', 'legal_compliance_policy_versions', 'legal_compliance_requirements', 'legal_compliance_assessments', 'legal_compliance_interpretations', 'legal_compliance_mappings', 'legal_compliance_findings', 'legal_compliance_reevaluations', 'legal_compliance_rules']
IMMUTABLE = ['legal_compliance_requirements', 'legal_compliance_interpretations', 'legal_compliance_policy_versions', 'legal_compliance_evidence_versions', 'legal_compliance_mappings', 'legal_compliance_rules', 'legal_compliance_assessments', 'legal_compliance_findings', 'legal_compliance_reevaluations']


def upgrade():
    op.create_table('legal_compliance_evidence',
    sa.Column('title', sa.String(length=250), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id'], ['legal_workspaces.organization_id', 'legal_workspaces.id'], name=op.f('fk_legal_compliance_evidence_organization_id_legal_workspaces')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_compliance_evidence')),
    sa.UniqueConstraint('organization_id', 'workspace_id', 'id', name=op.f('uq_legal_compliance_evidence_organization_id'))
    )
    op.create_table('legal_compliance_policies',
    sa.Column('title', sa.String(length=250), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id'], ['legal_workspaces.organization_id', 'legal_workspaces.id'], name=op.f('fk_legal_compliance_policies_organization_id_legal_workspaces')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_compliance_policies')),
    sa.UniqueConstraint('organization_id', 'workspace_id', 'id', name=op.f('uq_legal_compliance_policies_organization_id'))
    )
    op.create_table('legal_compliance_controls',
    sa.Column('title', sa.String(length=250), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'owner_id'], ['legal_workspace_memberships.organization_id', 'legal_workspace_memberships.workspace_id', 'legal_workspace_memberships.user_id'], name=op.f('fk_legal_compliance_controls_organization_id_legal_workspace_memberships')),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id'], ['legal_workspaces.organization_id', 'legal_workspaces.id'], name=op.f('fk_legal_compliance_controls_organization_id_legal_workspaces')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_compliance_controls')),
    sa.UniqueConstraint('organization_id', 'workspace_id', 'id', name=op.f('uq_legal_compliance_controls_organization_id'))
    )
    op.create_table('legal_compliance_evidence_versions',
    sa.Column('evidence_id', sa.Uuid(), nullable=False),
    sa.Column('actor_id', sa.Uuid(), nullable=False),
    sa.Column('document_id', sa.Uuid(), nullable=False),
    sa.Column('version_id', sa.Uuid(), nullable=False),
    sa.Column('source_sha256', sa.String(length=64), nullable=False),
    sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('replaces_id', sa.Uuid(), nullable=True),
    sa.Column('facts', sa.JSON(), nullable=False),
    sa.Column('citations', sa.JSON(), nullable=False),
    sa.Column('revision_sha256', sa.String(length=64), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('expires_at IS NULL OR expires_at > valid_from', name=op.f('ck_legal_compliance_evidence_versions_valid_interval')),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_legal_compliance_evidence_versions_actor_id_users')),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'document_id', 'version_id', 'source_sha256'], ['document_versions.organization_id', 'document_versions.workspace_id', 'document_versions.document_id', 'document_versions.id', 'document_versions.source_sha256'], name=op.f('fk_legal_compliance_evidence_versions_organization_id_document_versions')),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'evidence_id'], ['legal_compliance_evidence.organization_id', 'legal_compliance_evidence.workspace_id', 'legal_compliance_evidence.id'], name='fk_legal_compliance_evidence_evidence_id'),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'replaces_id'], ['legal_compliance_evidence_versions.organization_id', 'legal_compliance_evidence_versions.workspace_id', 'legal_compliance_evidence_versions.id'], name='fk_legal_compliance_evidence_versions_replaces_id'),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id'], ['legal_workspaces.organization_id', 'legal_workspaces.id'], name=op.f('fk_legal_compliance_evidence_versions_organization_id_legal_workspaces')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_compliance_evidence_versions')),
    sa.UniqueConstraint('organization_id', 'workspace_id', 'id', name=op.f('uq_legal_compliance_evidence_versions_organization_id'))
    )
    op.create_table('legal_compliance_policy_versions',
    sa.Column('policy_id', sa.Uuid(), nullable=False),
    sa.Column('document_id', sa.Uuid(), nullable=False),
    sa.Column('version_id', sa.Uuid(), nullable=False),
    sa.Column('source_sha256', sa.String(length=64), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'document_id', 'version_id', 'source_sha256'], ['document_versions.organization_id', 'document_versions.workspace_id', 'document_versions.document_id', 'document_versions.id', 'document_versions.source_sha256'], name=op.f('fk_legal_compliance_policy_versions_organization_id_document_versions')),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'policy_id'], ['legal_compliance_policies.organization_id', 'legal_compliance_policies.workspace_id', 'legal_compliance_policies.id'], name='fk_legal_compliance_policies_policy_id'),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id'], ['legal_workspaces.organization_id', 'legal_workspaces.id'], name=op.f('fk_legal_compliance_policy_versions_organization_id_legal_workspaces')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_compliance_policy_versions')),
    sa.UniqueConstraint('organization_id', 'workspace_id', 'id', name=op.f('uq_legal_compliance_policy_versions_organization_id')),
    sa.UniqueConstraint('policy_id', 'version_id', name=op.f('uq_legal_compliance_policy_versions_policy_id'))
    )
    op.create_table('legal_compliance_requirements',
    sa.Column('regulatory_version_id', sa.Uuid(), nullable=False),
    sa.Column('title', sa.String(length=250), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'regulatory_version_id'], ['legal_regulatory_versions.organization_id', 'legal_regulatory_versions.workspace_id', 'legal_regulatory_versions.id'], name='fk_legal_regulatory_versions_regulatory_version_id'),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id'], ['legal_workspaces.organization_id', 'legal_workspaces.id'], name=op.f('fk_legal_compliance_requirements_organization_id_legal_workspaces')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_compliance_requirements')),
    sa.UniqueConstraint('organization_id', 'workspace_id', 'id', name=op.f('uq_legal_compliance_requirements_organization_id'))
    )
    op.create_table('legal_compliance_assessments',
    sa.Column('requirement_id', sa.Uuid(), nullable=False),
    sa.Column('applicability_id', sa.Uuid(), nullable=False),
    sa.Column('actor_id', sa.Uuid(), nullable=False),
    sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('inputs', sa.JSON(), nullable=False),
    sa.Column('result', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('revision_sha256', sa.String(length=64), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("status IN ('satisfied','partially_satisfied','unsatisfied','insufficient_evidence','not_applicable','needs_review')", name=op.f('ck_legal_compliance_assessments_status')),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_legal_compliance_assessments_actor_id_users')),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'applicability_id'], ['legal_regulatory_applicability.organization_id', 'legal_regulatory_applicability.workspace_id', 'legal_regulatory_applicability.id'], name='fk_legal_regulatory_applicability_applicability_id'),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'requirement_id'], ['legal_compliance_requirements.organization_id', 'legal_compliance_requirements.workspace_id', 'legal_compliance_requirements.id'], name='fk_legal_compliance_requirements_requirement_id'),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id'], ['legal_workspaces.organization_id', 'legal_workspaces.id'], name=op.f('fk_legal_compliance_assessments_organization_id_legal_workspaces')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_compliance_assessments')),
    sa.UniqueConstraint('organization_id', 'workspace_id', 'id', name=op.f('uq_legal_compliance_assessments_organization_id'))
    )
    op.create_table('legal_compliance_interpretations',
    sa.Column('requirement_id', sa.Uuid(), nullable=False),
    sa.Column('actor_id', sa.Uuid(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('citations', sa.JSON(), nullable=False),
    sa.Column('revision_sha256', sa.String(length=64), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_legal_compliance_interpretations_actor_id_users')),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'requirement_id'], ['legal_compliance_requirements.organization_id', 'legal_compliance_requirements.workspace_id', 'legal_compliance_requirements.id'], name='fk_legal_compliance_requirements_requirement_id'),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id'], ['legal_workspaces.organization_id', 'legal_workspaces.id'], name=op.f('fk_legal_compliance_interpretations_organization_id_legal_workspaces')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_compliance_interpretations')),
    sa.UniqueConstraint('organization_id', 'workspace_id', 'id', name=op.f('uq_legal_compliance_interpretations_organization_id'))
    )
    op.create_table('legal_compliance_mappings',
    sa.Column('requirement_id', sa.Uuid(), nullable=False),
    sa.Column('control_id', sa.Uuid(), nullable=False),
    sa.Column('policy_version_id', sa.Uuid(), nullable=True),
    sa.Column('evidence_version_id', sa.Uuid(), nullable=True),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'control_id'], ['legal_compliance_controls.organization_id', 'legal_compliance_controls.workspace_id', 'legal_compliance_controls.id'], name='fk_legal_compliance_controls_control_id'),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'evidence_version_id'], ['legal_compliance_evidence_versions.organization_id', 'legal_compliance_evidence_versions.workspace_id', 'legal_compliance_evidence_versions.id'], name='fk_legal_compliance_evidence_versions_evidence_version_id'),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'policy_version_id'], ['legal_compliance_policy_versions.organization_id', 'legal_compliance_policy_versions.workspace_id', 'legal_compliance_policy_versions.id'], name='fk_legal_compliance_policy_versions_policy_version_id'),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'requirement_id'], ['legal_compliance_requirements.organization_id', 'legal_compliance_requirements.workspace_id', 'legal_compliance_requirements.id'], name='fk_legal_compliance_requirements_requirement_id'),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id'], ['legal_workspaces.organization_id', 'legal_workspaces.id'], name=op.f('fk_legal_compliance_mappings_organization_id_legal_workspaces')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_compliance_mappings')),
    sa.UniqueConstraint('organization_id', 'workspace_id', 'id', name=op.f('uq_legal_compliance_mappings_organization_id'))
    )
    op.create_table('legal_compliance_findings',
    sa.Column('assessment_id', sa.Uuid(), nullable=False),
    sa.Column('actor_id', sa.Uuid(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('revision_sha256', sa.String(length=64), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_legal_compliance_findings_actor_id_users')),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'assessment_id'], ['legal_compliance_assessments.organization_id', 'legal_compliance_assessments.workspace_id', 'legal_compliance_assessments.id'], name='fk_legal_compliance_assessments_assessment_id'),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id'], ['legal_workspaces.organization_id', 'legal_workspaces.id'], name=op.f('fk_legal_compliance_findings_organization_id_legal_workspaces')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_compliance_findings')),
    sa.UniqueConstraint('organization_id', 'workspace_id', 'id', name=op.f('uq_legal_compliance_findings_organization_id'))
    )
    op.create_table('legal_compliance_reevaluations',
    sa.Column('assessment_id', sa.Uuid(), nullable=False),
    sa.Column('reason', sa.String(length=200), nullable=False),
    sa.Column('cause_key', sa.String(length=200), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'assessment_id'], ['legal_compliance_assessments.organization_id', 'legal_compliance_assessments.workspace_id', 'legal_compliance_assessments.id'], name='fk_legal_compliance_assessments_assessment_id'),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id'], ['legal_workspaces.organization_id', 'legal_workspaces.id'], name=op.f('fk_legal_compliance_reevaluations_organization_id_legal_workspaces')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_compliance_reevaluations')),
    sa.UniqueConstraint('assessment_id', 'cause_key', name=op.f('uq_legal_compliance_reevaluations_assessment_id')),
    sa.UniqueConstraint('organization_id', 'workspace_id', 'id', name=op.f('uq_legal_compliance_reevaluations_organization_id'))
    )
    op.create_table('legal_compliance_rules',
    sa.Column('control_id', sa.Uuid(), nullable=False),
    sa.Column('interpretation_id', sa.Uuid(), nullable=False),
    sa.Column('actor_id', sa.Uuid(), nullable=False),
    sa.Column('checks', sa.JSON(), nullable=False),
    sa.Column('revision_sha256', sa.String(length=64), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_legal_compliance_rules_actor_id_users')),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'control_id'], ['legal_compliance_controls.organization_id', 'legal_compliance_controls.workspace_id', 'legal_compliance_controls.id'], name='fk_legal_compliance_controls_control_id'),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id', 'interpretation_id'], ['legal_compliance_interpretations.organization_id', 'legal_compliance_interpretations.workspace_id', 'legal_compliance_interpretations.id'], name='fk_legal_compliance_interpretations_interpretation_id'),
    sa.ForeignKeyConstraint(['organization_id', 'workspace_id'], ['legal_workspaces.organization_id', 'legal_workspaces.id'], name=op.f('fk_legal_compliance_rules_organization_id_legal_workspaces')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_compliance_rules')),
    sa.UniqueConstraint('organization_id', 'workspace_id', 'id', name=op.f('uq_legal_compliance_rules_organization_id'))
    )
    # ### end Alembic commands ###
    op.execute("""CREATE FUNCTION protect_legal_compliance() RETURNS trigger AS $$ BEGIN
      RAISE EXCEPTION 'Compliance history is immutable'; END; $$ LANGUAGE plpgsql""")
    for table in IMMUTABLE:
        op.execute(f"CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} "
                   "FOR EACH ROW EXECUTE FUNCTION protect_legal_compliance()")
        op.execute(f"CREATE TRIGGER immutable_truncate_{table} BEFORE TRUNCATE ON {table} "
                   "FOR EACH STATEMENT EXECUTE FUNCTION protect_legal_compliance()")


def downgrade():
    checks = " OR ".join(f"EXISTS (SELECT 1 FROM {table})" for table in TABLES)
    op.execute(f"""DO $$ BEGIN IF {checks} THEN
        RAISE EXCEPTION 'Legal compliance history exists; refusing lossy downgrade';
      END IF; END $$""")
    for table in reversed(TABLES):
        op.drop_table(table)
    op.execute("DROP FUNCTION protect_legal_compliance()")
