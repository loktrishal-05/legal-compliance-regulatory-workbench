"""Audited, independent legal provisioning (Phase D). Never exposed as an HTTP endpoint.

Workspace admins grant/revoke memberships and object grants for OTHER users only, never above their
own clearance; nobody provisions themselves. Bootstrap and legacy-document mapping are explicit
operator actions (scripts/legal_provisioning_cli.py) audited as `system`. Every state change shares
the caller's transaction with its audit event; callers commit, failures roll both back.
"""
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.db.models import Document, User
from app.db.models.legal_scope import (
    DocumentAccess, LegalDocumentScope, Matter, MatterAccess, Organization, Workspace, WorkspaceMembership,
)
from app.services.audit import append_event
from app.services.legal_policy import CLASSIFICATIONS, ROLE_OPERATIONS, LegalAccessDenied, authorize_workspace

POLICY_VERSION = "legal-provisioning-v1"
OBJECT_OPERATIONS = {"read", "propose", "review_legal", "review_compliance"}


def _admin(db, admin_id, workspace_id, terms, target_user_id):
    ctx = authorize_workspace(db, admin_id, workspace_id, current_terms_version=terms)
    if ctx.role != "workspace_admin" or admin_id == target_user_id:
        raise LegalAccessDenied()
    return ctx


def _audit(db, event_type, actor_id, workspace, **payload):
    append_event(db, event_type=event_type, actor_id=actor_id, actor_kind="user" if actor_id else "system",
                 payload={"policy_version": POLICY_VERSION, "organization_id": str(workspace.organization_id),
                          "workspace_id": str(workspace.id), **{k: str(v) if isinstance(v, UUID) else v
                                                                for k, v in payload.items()}})


def _member(db, workspace_id, user_id):
    member = db.get(WorkspaceMembership, (workspace_id, user_id))
    user = db.get(User, user_id)
    if member is None or not member.is_active or user is None or not user.is_active:
        raise LegalAccessDenied()
    return member


def grant_membership(db: Session, *, admin_id: UUID, workspace_id: UUID, user_id: UUID, role: str,
                     clearance: str, current_terms_version: str) -> WorkspaceMembership:
    if role not in ROLE_OPERATIONS or clearance not in CLASSIFICATIONS:
        raise ValueError("unknown role or clearance")
    ctx = _admin(db, admin_id, workspace_id, current_terms_version, user_id)
    if CLASSIFICATIONS[clearance] > CLASSIFICATIONS[ctx.clearance]:
        raise LegalAccessDenied()
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise LegalAccessDenied()
    member = db.get(WorkspaceMembership, (workspace_id, user_id))
    if member is None:
        member = WorkspaceMembership(organization_id=ctx.organization_id, workspace_id=workspace_id,
                                     user_id=user_id, role=role, clearance=clearance)
        db.add(member)
    else:
        member.role, member.clearance, member.is_active = role, clearance, True
    db.flush()
    _audit(db, "LEGAL_ACCESS_GRANTED", admin_id, db.get(Workspace, workspace_id), grant="membership",
           target_user_id=user_id, role=role, clearance=clearance)
    return member


def revoke_membership(db: Session, *, admin_id: UUID, workspace_id: UUID, user_id: UUID,
                      current_terms_version: str) -> None:
    """Membership revocation removes all legal access at once: policy requires an active membership."""
    _admin(db, admin_id, workspace_id, current_terms_version, user_id)
    member = _member(db, workspace_id, user_id)
    member.is_active = False
    db.flush()
    _audit(db, "LEGAL_ACCESS_REVOKED", admin_id, db.get(Workspace, workspace_id), grant="membership",
           target_user_id=user_id)


def set_document_access(db: Session, *, admin_id: UUID, workspace_id: UUID, document_id: UUID, user_id: UUID,
                        operation: str, active: bool, current_terms_version: str) -> None:
    if operation not in OBJECT_OPERATIONS:
        raise ValueError("unknown operation")
    ctx = _admin(db, admin_id, workspace_id, current_terms_version, user_id)
    scope = db.get(LegalDocumentScope, document_id)
    if scope is None or scope.workspace_id != workspace_id or not scope.is_active:
        raise LegalAccessDenied()
    member = _member(db, workspace_id, user_id)
    if active and operation not in ROLE_OPERATIONS[member.role]:
        raise LegalAccessDenied()  # a grant never widens what the scoped role may do
    grant = db.get(DocumentAccess, (document_id, user_id, operation))
    if grant is None:
        if not active:
            raise LegalAccessDenied()
        db.add(DocumentAccess(organization_id=ctx.organization_id, workspace_id=workspace_id,
                              document_id=document_id, user_id=user_id, operation=operation))
    else:
        grant.is_active = active
    db.flush()
    _audit(db, "LEGAL_ACCESS_GRANTED" if active else "LEGAL_ACCESS_REVOKED", admin_id,
           db.get(Workspace, workspace_id), grant="document", document_id=document_id,
           target_user_id=user_id, operation=operation)


def set_matter_access(db: Session, *, admin_id: UUID, workspace_id: UUID, matter_id: UUID, user_id: UUID,
                      active: bool, current_terms_version: str) -> None:
    ctx = _admin(db, admin_id, workspace_id, current_terms_version, user_id)
    matter = db.get(Matter, matter_id)
    if matter is None or matter.workspace_id != workspace_id or not matter.is_active:
        raise LegalAccessDenied()
    _member(db, workspace_id, user_id)
    grant = db.get(MatterAccess, (matter_id, user_id))
    if grant is None:
        if not active:
            raise LegalAccessDenied()
        db.add(MatterAccess(organization_id=ctx.organization_id, workspace_id=workspace_id,
                            matter_id=matter_id, user_id=user_id))
    else:
        grant.is_active = active
    db.flush()
    _audit(db, "LEGAL_ACCESS_GRANTED" if active else "LEGAL_ACCESS_REVOKED", admin_id,
           db.get(Workspace, workspace_id), grant="matter", matter_id=matter_id, target_user_id=user_id)


def bootstrap_workspace(db: Session, *, operator_label: str, organization_name: str, workspace_name: str,
                        admin_user_id: UUID, admin_clearance: str = "internal") -> Workspace:
    """Operator-only: new organization + workspace + first workspace_admin (no review authority)."""
    if not operator_label.strip() or admin_clearance not in CLASSIFICATIONS:
        raise ValueError("operator label and valid clearance required")
    user = db.get(User, admin_user_id)
    if user is None or not user.is_active:
        raise LegalAccessDenied()
    org = Organization(id=uuid4(), name=organization_name)
    db.add(org)
    db.flush()
    workspace = Workspace(id=uuid4(), organization_id=org.id, name=workspace_name)
    db.add(workspace)
    db.flush()
    db.add(WorkspaceMembership(organization_id=org.id, workspace_id=workspace.id, user_id=admin_user_id,
                               role="workspace_admin", clearance=admin_clearance))
    db.flush()
    _audit(db, "LEGAL_WORKSPACE_BOOTSTRAPPED", None, workspace, operator_label=operator_label,
           target_user_id=admin_user_id, role="workspace_admin", clearance=admin_clearance)
    return workspace


def map_legacy_document(db: Session, *, operator_label: str, workspace_id: UUID, document_id: UUID,
                        classification: str, matter_id: UUID | None = None) -> LegalDocumentScope:
    """Operator-only explicit legacy ownership. Never inferred; an already-scoped document is refused."""
    if not operator_label.strip() or classification not in CLASSIFICATIONS:
        raise ValueError("operator label and valid classification required")
    workspace = db.get(Workspace, workspace_id)
    if workspace is None or not workspace.is_active or db.get(Document, document_id) is None:
        raise LegalAccessDenied()
    if db.get(LegalDocumentScope, document_id) is not None:
        raise ValueError("document already has legal ownership")
    if matter_id is not None:
        matter = db.get(Matter, matter_id)
        if matter is None or matter.workspace_id != workspace_id:
            raise LegalAccessDenied()
    scope = LegalDocumentScope(document_id=document_id, organization_id=workspace.organization_id,
                               workspace_id=workspace_id, matter_id=matter_id, classification=classification)
    db.add(scope)
    db.flush()
    _audit(db, "LEGAL_LEGACY_DOCUMENT_MAPPED", None, workspace, operator_label=operator_label,
           document_id=document_id, matter_id=matter_id, classification=classification)
    return scope
