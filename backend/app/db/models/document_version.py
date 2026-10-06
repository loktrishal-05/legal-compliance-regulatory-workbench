"""Source revisions and durable ingestion state."""
import uuid
from sqlalchemy import CheckConstraint, ForeignKey, ForeignKeyConstraint, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, IdentityMixin, CreatedAtMixin


class DocumentVersion(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "document_versions"
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    # Dedupe namespace: legacy (NULL workspace) is global; legal versions are unique per workspace (0022).
    source_sha256: Mapped[str] = mapped_column(String(64))
    organization_id: Mapped[uuid.UUID | None] = mapped_column()
    workspace_id: Mapped[uuid.UUID | None] = mapped_column()
    status: Mapped[str] = mapped_column(String(40), default="processing")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    ingestion_metadata: Mapped[dict] = mapped_column(JSONB)
    warnings: Mapped[list] = mapped_column(JSONB, default=list)

    __table_args__ = (
        CheckConstraint("(organization_id IS NULL) = (workspace_id IS NULL)", name="legal_scope_pair"),
        ForeignKeyConstraint(["organization_id", "workspace_id", "document_id"],
            ["legal_document_scopes.organization_id", "legal_document_scopes.workspace_id",
             "legal_document_scopes.document_id"]),
        Index("ux_document_versions_legacy_source_sha256", "source_sha256", unique=True,
              postgresql_where=text("workspace_id IS NULL"), sqlite_where=text("workspace_id IS NULL")),
        Index("ux_document_versions_workspace_source_sha256", "organization_id", "workspace_id", "source_sha256",
              unique=True, postgresql_where=text("workspace_id IS NOT NULL"),
              sqlite_where=text("workspace_id IS NOT NULL")),
    )
