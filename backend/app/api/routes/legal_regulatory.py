"""Session-protected regulatory proposals and permission-filtered source history."""
from datetime import date, datetime, timezone
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.legal_scope import unavailable
from app.core.config import settings
from app.db.models import User
from app.db.models.legal_regulatory import (RegulatorySource, RegulatoryDocument, RegulatoryVersion,
    RegulatoryChange, ApplicabilityDecision, RegulatoryWatchlist, RegulatoryCampaign)
from app.db.session import get_db
from app.schemas.legal_regulatory import (SourceRequest, DocumentRequest, VersionRequest, ChangeRequest,
    ApplicabilityRequest, WatchlistRequest)
from app.services import legal_regulatory as service
from app.services.legal_policy import LegalAccessDenied
from app.services.legal_regulatory_projection import historical_version, monitoring_status

router = APIRouter(prefix="/v1/workspaces/{workspace_id}/regulatory", tags=["legal regulatory"])
MODELS = {"sources": RegulatorySource, "documents": RegulatoryDocument, "versions": RegulatoryVersion,
          "changes": RegulatoryChange, "applicability": ApplicabilityDecision,
          "watchlists": RegulatoryWatchlist, "campaigns": RegulatoryCampaign}


def serialize(row):
    return jsonable_encoder({column.name: getattr(row, column.name) for column in row.__table__.columns})


def visible(db, ctx, resource, row):
    if resource == "versions":
        service.authorize_version(db, ctx, row, settings.current_terms_version)
    elif resource in ("changes", "applicability"):
        service._authorize_target(db, ctx, row.id, "regulatory_change" if resource == "changes" else "regulatory_applicability")
    elif resource == "campaigns":
        service._authorize_target(db, ctx, row.change_id, "regulatory_change")


@router.get("/versions/as-of")
def as_of(workspace_id: UUID, regulatory_document_id: UUID, effective_on: date,
          known_at: datetime, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if known_at.tzinfo is None:
        raise HTTPException(422, detail={"code": "aware_known_at_required"})
    try:
        ctx = service.context(db, user.id, workspace_id, settings.current_terms_version)
        service.scoped(db, RegulatoryDocument, ctx, regulatory_document_id)
        rows = list(db.scalars(select(RegulatoryVersion).where(RegulatoryVersion.workspace_id == workspace_id,
            RegulatoryVersion.regulatory_document_id == regulatory_document_id)))
        # A partial authorized timeline cannot establish the single version in force.
        for row in rows:
            service.authorize_version(db, ctx, row, settings.current_terms_version)
        return historical_version(rows, effective_on, known_at)
    except LegalAccessDenied:
        unavailable(db, user.id, workspace_id)


@router.get("/{resource}")
def listing(workspace_id: UUID,
            resource: Literal["sources", "documents", "versions", "changes", "applicability", "watchlists", "campaigns"],
            offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
            db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        ctx = service.context(db, user.id, workspace_id, settings.current_terms_version)
    except LegalAccessDenied:
        unavailable(db, user.id, workspace_id)
    model = MODELS[resource]
    rows = db.scalars(select(model).where(model.organization_id == ctx.organization_id,
        model.workspace_id == workspace_id).order_by(model.created_at, model.id))
    items = []
    permitted = 0
    for row in rows:
        try:
            visible(db, ctx, resource, row)
        except LegalAccessDenied:
            continue
        permitted += 1
        if permitted <= offset:
            continue
        item = serialize(row)
        if resource in ("sources", "changes", "applicability"):
            target = {"sources": "regulatory_source", "changes": "regulatory_change", "applicability": "regulatory_applicability"}[resource]
            item["review_state"] = "approved" if service.approved(db, row, target) else "not_approved"
        if resource == "watchlists":
            source = service.scoped(db, RegulatorySource, ctx, row.source_id)
            item.update(monitoring_status(datetime.now(timezone.utc), row.max_age_days, source.last_success_at, source.last_failure_at))
        items.append(item)
        if len(items) > limit:
            break
    return {"items": items[:limit], "has_more": len(items) > limit,
            "next_offset": offset + limit if len(items) > limit else None}


def create(db, user, workspace_id, request, fn, **kwargs):
    try:
        row = fn(db, actor_id=user.id, workspace_id=workspace_id, request=request,
                 current_terms_version=settings.current_terms_version, **kwargs)
        db.commit()
        return serialize(row)
    except LegalAccessDenied:
        db.rollback()
        unavailable(db, user.id, workspace_id, operation="regulatory_propose")
    except service.RegulatoryConflict as error:
        db.rollback()
        raise HTTPException(409, detail={"code": str(error)}) from error


@router.post("/sources", status_code=201)
def source(workspace_id: UUID, request: SourceRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create(db, user, workspace_id, request, service.create_source)


@router.post("/documents", status_code=201)
def document(workspace_id: UUID, request: DocumentRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create(db, user, workspace_id, request, service.create_document)


@router.post("/versions", status_code=201)
def version(workspace_id: UUID, request: VersionRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create(db, user, workspace_id, request, service.import_version, data_root=settings.data_root)


@router.post("/changes", status_code=201)
def change(workspace_id: UUID, request: ChangeRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create(db, user, workspace_id, request, service.create_change)


@router.post("/applicability", status_code=201)
def applicability(workspace_id: UUID, request: ApplicabilityRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create(db, user, workspace_id, request, service.create_applicability)


@router.post("/watchlists", status_code=201)
def watchlist(workspace_id: UUID, request: WatchlistRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create(db, user, workspace_id, request, service.create_watchlist)
