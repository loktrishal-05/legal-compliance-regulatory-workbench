"""Additive legal ownership. Unmapped legacy documents have no legal access."""
import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, IdentityMixin


class Organization(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_organizations"
    name: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class Workspace(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_workspaces"
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("legal_organizations.id"))
    name: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    __table_args__ = (UniqueConstraint("organization_id", "id"),)


class WorkspaceMembership(CreatedAtMixin, Base):
    __tablename__ = "legal_workspace_memberships"
    organization_id: Mapped[uuid.UUID] = mapped_column()
    workspace_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(40))
    clearance: Mapped[str] = mapped_column(String(20), default="public", server_default="public")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "workspace_id"],
                             ["legal_workspaces.organization_id", "legal_workspaces.id"]),
        UniqueConstraint("organization_id", "workspace_id", "user_id"),
        CheckConstraint("role IN ('analyst','legal_reviewer','compliance_reviewer','business_owner',"
                        "'auditor','workspace_admin','viewer')", name="role"),
        CheckConstraint("clearance IN ('public','internal','confidential','restricted')", name="clearance"),
    )


class Matter(IdentityMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_matters"
    organization_id: Mapped[uuid.UUID] = mapped_column()
    workspace_id: Mapped[uuid.UUID] = mapped_column()
    name: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "workspace_id"],
                             ["legal_workspaces.organization_id", "legal_workspaces.id"]),
        UniqueConstraint("organization_id", "workspace_id", "id"),
    )


class MatterAccess(CreatedAtMixin, Base):
    __tablename__ = "legal_matter_access"
    organization_id: Mapped[uuid.UUID] = mapped_column()
    workspace_id: Mapped[uuid.UUID] = mapped_column()
    matter_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "workspace_id", "matter_id"],
            ["legal_matters.organization_id", "legal_matters.workspace_id", "legal_matters.id"]),
        ForeignKeyConstraint(["organization_id", "workspace_id", "user_id"],
            ["legal_workspace_memberships.organization_id", "legal_workspace_memberships.workspace_id",
             "legal_workspace_memberships.user_id"]),
    )


class LegalDocumentScope(CreatedAtMixin, Base):
    __tablename__ = "legal_document_scopes"
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column()
    workspace_id: Mapped[uuid.UUID] = mapped_column()
    matter_id: Mapped[uuid.UUID | None] = mapped_column()
    classification: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    legal_hold: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "workspace_id"],
                             ["legal_workspaces.organization_id", "legal_workspaces.id"]),
        ForeignKeyConstraint(["organization_id", "workspace_id", "matter_id"],
            ["legal_matters.organization_id", "legal_matters.workspace_id", "legal_matters.id"]),
        UniqueConstraint("organization_id", "workspace_id", "document_id"),
        CheckConstraint("classification IN ('public','internal','confidential','restricted')", name="classification"),
    )


class DocumentAccess(CreatedAtMixin, Base):
    __tablename__ = "legal_document_access"
    organization_id: Mapped[uuid.UUID] = mapped_column()
    workspace_id: Mapped[uuid.UUID] = mapped_column()
    document_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    operation: Mapped[str] = mapped_column(String(30), primary_key=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "workspace_id", "document_id"],
            ["legal_document_scopes.organization_id", "legal_document_scopes.workspace_id",
             "legal_document_scopes.document_id"]),
        ForeignKeyConstraint(["organization_id", "workspace_id", "user_id"],
            ["legal_workspace_memberships.organization_id", "legal_workspace_memberships.workspace_id",
             "legal_workspace_memberships.user_id"]),
        CheckConstraint("operation IN ('read','propose','review_legal','review_compliance')", name="operation"),
    )
