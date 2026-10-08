"""Database-derived legal authorization; HTTP callers must first verify the session.

No content loading, writes, settings import, global-role bypass or cached authority.
This is a policy prerequisite, not an approval/release service.
"""
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import and_, exists, select
from sqlalchemy.orm import Session

from app.db.models import AuditEvent, DocumentVersion, User
from app.db.models.legal_scope import (
    Organization, Workspace, WorkspaceMembership, Matter, MatterAccess, LegalDocumentScope, DocumentAccess,
)


class LegalAccessDenied(LookupError):
    def __init__(self):
        super().__init__("Legal resource unavailable.")


@dataclass(frozen=True)
class LegalContext:
    actor_id: UUID
    organization_id: UUID
    workspace_id: UUID
    role: str
    clearance: str
    platform_role: str


# Legal audit is scoped (Phase J); the root industrial audit log never lists these.
LEGAL_AUDIT_EVENT_TYPES = ("SECURITY_POLICY_DENIED", "LEGAL_WORKSPACE_BOOTSTRAPPED", "LEGAL_ACCESS_GRANTED",
                           "LEGAL_ACCESS_REVOKED", "LEGAL_LEGACY_DOCUMENT_MAPPED", "LEGAL_DOCUMENT_RECEIVED",
                           "LEGAL_INTAKE_REJECTED", "LEGAL_DOCUMENT_EXTRACTED", "LEGAL_EXTRACTION_FAILED",
                           "LEGAL_CORRECTION_PROPOSED", "LEGAL_CORRECTION_DECIDED")
CLASSIFICATIONS = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}
ROLE_OPERATIONS = {
    "analyst": {"read", "propose"},
    "legal_reviewer": {"read", "propose", "review_legal"},
    "compliance_reviewer": {"read", "propose", "review_compliance"},
    "business_owner": {"read"}, "auditor": {"read"}, "workspace_admin": {"read"}, "viewer": {"read"},
}


def authorize_workspace(db: Session, actor_id: UUID, workspace_id: UUID, *, current_terms_version: str) -> LegalContext:
    """actor_id comes from the verified session; terms version from server policy."""
    row = db.execute(select(
        Workspace.organization_id, WorkspaceMembership.role, WorkspaceMembership.clearance,
        User.role.label("platform_role"),
    ).select_from(Workspace).join(Organization, Organization.id == Workspace.organization_id)
        .join(WorkspaceMembership, (WorkspaceMembership.workspace_id == Workspace.id)
              & (WorkspaceMembership.organization_id == Workspace.organization_id))
        .join(User, User.id == WorkspaceMembership.user_id)
        .where(Workspace.id == workspace_id, User.id == actor_id, User.is_active.is_(True),
            User.signup_pending.is_(False), User.terms_version == current_terms_version,
            User.terms_accepted_at.is_not(None), Organization.is_active.is_(True),
            Workspace.is_active.is_(True), WorkspaceMembership.is_active.is_(True))).one_or_none()
    if row is None or not current_terms_version or row.role not in ROLE_OPERATIONS or row.clearance not in CLASSIFICATIONS:
        raise LegalAccessDenied()
    return LegalContext(actor_id, row.organization_id, workspace_id, row.role, row.clearance, row.platform_role)


def authorize_document(db: Session, actor_id: UUID, workspace_id: UUID, document_id: UUID, *,
                       current_terms_version: str, operation: str = "read",
                       requester_id: UUID | None = None) -> LegalContext:
    """Recheck stored grants for each operation. Review needs a stored proposal requester.

    Grant + role + clearance + optional matter access are all required. A grant for
    propose/review cannot replace the read grant. Delete is never supported here.
    """
    context = authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version)
    if operation not in ROLE_OPERATIONS[context.role]:
        raise LegalAccessDenied()
    if operation.startswith("review_") and (
        context.platform_role not in {"reviewer", "admin"} or requester_id is None or requester_id == actor_id
    ):
        raise LegalAccessDenied()
    row = db.execute(select(LegalDocumentScope.matter_id, LegalDocumentScope.classification)
        .where(LegalDocumentScope.document_id == document_id,
            LegalDocumentScope.workspace_id == workspace_id,
            LegalDocumentScope.organization_id == context.organization_id,
            LegalDocumentScope.is_active.is_(True))).one_or_none()
    if row is None or row.classification not in CLASSIFICATIONS or (
        CLASSIFICATIONS[row.classification] > CLASSIFICATIONS[context.clearance]
    ):
        raise LegalAccessDenied()
    operations = set(db.scalars(select(DocumentAccess.operation).where(
        DocumentAccess.document_id == document_id, DocumentAccess.workspace_id == workspace_id,
        DocumentAccess.organization_id == context.organization_id, DocumentAccess.user_id == actor_id,
        DocumentAccess.is_active.is_(True))))
    if not {"read", operation}.issubset(operations):
        raise LegalAccessDenied()
    if row.matter_id is not None:
        matter_access = db.scalar(select(Matter.id).join(MatterAccess,
            (MatterAccess.matter_id == Matter.id) & (MatterAccess.workspace_id == Matter.workspace_id)
            & (MatterAccess.organization_id == Matter.organization_id)).where(
                Matter.id == row.matter_id, Matter.workspace_id == workspace_id,
                Matter.organization_id == context.organization_id, Matter.is_active.is_(True),
                MatterAccess.user_id == actor_id, MatterAccess.is_active.is_(True)))
        if matter_access is None:
            raise LegalAccessDenied()
    return context


def legacy_version_clause():
    """SQL condition for OLD industrial paths: version and its document have no legal ownership.

    Legal content is reachable only through the scoped `/v1` APIs; every legacy read/dedupe/index
    path filters with this so a mapped or legally ingested document can never leak through it.
    """
    return and_(DocumentVersion.workspace_id.is_(None),
                ~exists().where(LegalDocumentScope.document_id == DocumentVersion.document_id))


def is_legacy_version(db: Session, version) -> bool:
    return (version is not None and version.workspace_id is None
            and db.get(LegalDocumentScope, version.document_id) is None)


def without_legal_audit(query):
    """Root industrial audit reads exclude legal events; legal audit is scoped (Phase J)."""
    return query.where(AuditEvent.event_type.not_in(LEGAL_AUDIT_EVENT_TYPES))


def is_legacy_document(db: Session, document_id) -> bool:
    return db.get(LegalDocumentScope, document_id) is None
