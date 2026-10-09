"""Durable legal document jobs and anchored blank-region transcriptions. Owner: agent A (parallel build 2026-10-09)."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0026_legal_jobs"
down_revision = "0025_legal_corrections"
branch_labels = None
depends_on = None


def ts(name, nullable=True):
    return sa.Column(name, sa.DateTime(timezone=True), nullable=nullable)


def upgrade():
    op.create_table("legal_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        *(sa.Column(name, sa.Uuid(), nullable=False) for name in
          ("organization_id", "workspace_id", "document_id", "version_id")),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("operation", sa.String(20), nullable=False),
        sa.Column("profile", sa.String(60), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("lease_owner", sa.String(100), nullable=True),
        ts("lease_expires_at"), ts("next_retry_at"),
        sa.Column("failure_code", sa.String(80), nullable=True),
        sa.Column("extraction_id", sa.Uuid(), nullable=True),
        ts("finished_at"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id", "workspace_id", "document_id", "version_id", "source_sha256"],
            ["document_versions.organization_id", "document_versions.workspace_id", "document_versions.document_id",
             "document_versions.id", "document_versions.source_sha256"], name="fk_legal_jobs_source_version"),
        sa.UniqueConstraint("workspace_id", "actor_id", "idempotency_key", name="uq_legal_jobs_retry"),
        sa.CheckConstraint("state IN ('queued','running','succeeded','failed','dead_letter')", name="state"),
        sa.CheckConstraint("operation IN ('extract','ocr')", name="operation"),
        sa.CheckConstraint("attempts >= 0 AND max_attempts BETWEEN 1 AND 10", name="attempts"),
        sa.CheckConstraint("length(source_sha256) = 64", name="source_hash"))
    op.create_index("ix_legal_jobs_claim", "legal_jobs", ["state", "next_retry_at"])
    op.create_index("ix_legal_jobs_workspace_state", "legal_jobs", ["workspace_id", "state"])
    op.create_table("legal_region_transcriptions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        *(sa.Column(name, sa.Uuid(), nullable=False) for name in ("organization_id", "workspace_id", "extraction_id")),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("bbox", JSONB(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("transcription_sha256", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["extraction_id", "organization_id", "workspace_id"],
            ["legal_extractions.id", "legal_extractions.organization_id", "legal_extractions.workspace_id"],
            name="fk_legal_region_transcriptions_extraction"),
        sa.UniqueConstraint("workspace_id", "actor_id", "idempotency_key", name="uq_legal_region_transcriptions_retry"),
        sa.CheckConstraint("page BETWEEN 1 AND 10000", name="page"),
        sa.CheckConstraint("length(text) BETWEEN 1 AND 64000 AND length(rationale) BETWEEN 1 AND 2000", name="text_bounds"),
        sa.CheckConstraint("length(transcription_sha256) = 64", name="hash"))
    op.execute("""CREATE FUNCTION protect_legal_region_transcription() RETURNS trigger AS $$ BEGIN
      RAISE EXCEPTION 'Legal region transcriptions are immutable'; END; $$ LANGUAGE plpgsql""")
    op.execute("CREATE TRIGGER immutable_legal_region_transcriptions BEFORE UPDATE OR DELETE ON "
               "legal_region_transcriptions FOR EACH ROW EXECUTE FUNCTION protect_legal_region_transcription()")
    op.execute("CREATE TRIGGER immutable_truncate_legal_region_transcriptions BEFORE TRUNCATE ON "
               "legal_region_transcriptions FOR EACH STATEMENT EXECUTE FUNCTION protect_legal_region_transcription()")


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM legal_jobs) OR EXISTS (SELECT 1 FROM legal_region_transcriptions) THEN
        RAISE EXCEPTION 'Legal job/transcription history exists; refusing lossy downgrade';
      END IF; END $$""")
    op.drop_table("legal_region_transcriptions")
    op.drop_table("legal_jobs")
    op.execute("DROP FUNCTION protect_legal_region_transcription()")
