"""Session/terms protected legal metadata, never a provisioning/intake endpoint."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.models import Document, User
from app.db.models.legal_scope import LegalDocumentScope, Workspace
from app.db.session import get_db
from app.schemas.legal_scope import LegalDocumentMetadata, WorkspaceMetadata
from app.services.audit import append_event
from app.services.legal_policy import LegalAccessDenied, authorize_document, authorize_workspace

router = APIRouter(prefix="/v1/workspaces", tags=["legal scope"])


def unavailable(db: Session, actor_id: UUID, workspace_id: UUID, document_id: UUID | None = None):
    # Requested IDs only, no source metadata/body or inferred tenant identity.
    append_event(db, event_type="SECURITY_POLICY_DENIED", actor_id=actor_id, actor_kind="user",
        payload={"policy_version": "legal-scope-v1", "requested_workspace_id": str(workspace_id),
                 "requested_document_id": str(document_id) if document_id else None, "operation": "read"})
    db.commit()
    raise HTTPException(404, detail={"code": "legal_resource_unavailable"})


@router.get("/{workspace_id}", response_model=WorkspaceMetadata)
def workspace_metadata(workspace_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        context = authorize_workspace(db, user.id, workspace_id, current_terms_version=settings.current_terms_version)
    except LegalAccessDenied:
        unavailable(db, user.id, workspace_id)
    row = db.execute(select(Workspace.id, Workspace.organization_id, Workspace.name)
                     .where(Workspace.id == context.workspace_id)).one()
    return WorkspaceMetadata(**row._mapping, role=context.role)


@router.get("/{workspace_id}/documents/{document_id}", response_model=LegalDocumentMetadata)
def document_metadata(workspace_id: UUID, document_id: UUID, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    try:
        authorize_document(db, user.id, workspace_id, document_id, current_terms_version=settings.current_terms_version)
    except LegalAccessDenied:
        unavailable(db, user.id, workspace_id, document_id)
    row = db.execute(select(
        Document.id, Document.filename, Document.document_type, Document.ingestion_status,
        LegalDocumentScope.workspace_id, LegalDocumentScope.matter_id, LegalDocumentScope.classification,
        LegalDocumentScope.legal_hold,
    ).join(LegalDocumentScope, LegalDocumentScope.document_id == Document.id)
        .where(Document.id == document_id, LegalDocumentScope.workspace_id == workspace_id)).one()
    return LegalDocumentMetadata(**row._mapping)
