"""Session-protected compliance proposals, permission-filtered lists, current six-state projection and impact.
Deny -> uniform 404 `legal_resource_unavailable`; conflict -> 409. Approval only via /reviews."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.legal_regulatory import serialize
from app.api.routes.legal_scope import unavailable
from app.core.config import settings
from app.db.models import User
from app.db.models import legal_compliance as m
from app.db.session import get_db
from app.schemas import legal_compliance as schemas
from app.services import legal_compliance as service
from app.services import legal_regulatory as regulatory
from app.services.legal_policy import LegalAccessDenied

router = APIRouter(prefix="/v1/workspaces/{workspace_id}/compliance", tags=["legal compliance"])
REQUESTS = {"requirements": schemas.RequirementRequest, "interpretations": schemas.InterpretationRequest,
            "policies": schemas.PolicyRequest, "policy-versions": schemas.PolicyVersionRequest,
            "controls": schemas.ControlRequest, "evidence": schemas.EvidenceRequest,
            "evidence-versions": schemas.EvidenceVersionRequest, "mappings": schemas.MappingRequest,
            "rules": schemas.RuleRequest, "assessments": schemas.AssessmentRequest, "findings": schemas.FindingRequest}
REVIEW_TARGETS = {"interpretations": "requirement_interpretation", "rules": "compliance_rule",
                  "evidence-versions": "evidence_acceptance", "assessments": "assessment", "findings": "compliance_finding"}
Resource = Literal["requirements", "interpretations", "policies", "policy-versions", "controls", "evidence",
                   "evidence-versions", "mappings", "rules", "assessments", "findings", "reevaluations"]


def terms():
    return settings.current_terms_version


def context(db, user, workspace_id, write=False):
    try:
        return regulatory.context(db, user.id, workspace_id, terms(), write=write)
    except LegalAccessDenied:
        unavailable(db, user.id, workspace_id, operation="compliance")


def item(db, resource, row):
    out = serialize(row)
    if resource in REVIEW_TARGETS:
        out["review_state"] = "approved" if regulatory.approved(db, row, REVIEW_TARGETS[resource]) else "not_approved"
    return out


@router.get("/impact")
def impact(workspace_id: UUID, changed_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ctx = context(db, user, workspace_id)
    try:
        return {"changed_id": changed_id, "paths": service.impact_paths(db, ctx, changed_id, terms())}
    except LegalAccessDenied:
        unavailable(db, user.id, workspace_id, operation="compliance_impact")


@router.get("/assessments/{assessment_id}/current")
def current(workspace_id: UUID, assessment_id: UUID, db: Session = Depends(get_db),
            user: User = Depends(get_current_user)):
    """Stored snapshot stays immutable; this is the current projection with freshness/review dimensions."""
    ctx = context(db, user, workspace_id)
    try:
        row = service.get(db, m.Assessment, ctx, assessment_id, terms())
        return {"assessment": item(db, "assessments", row), "current": service.current_projection(db, ctx, row, terms())}
    except LegalAccessDenied:
        unavailable(db, user.id, workspace_id, operation="compliance_assessment")


@router.get("/{resource}")
def listing(workspace_id: UUID, resource: Resource, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
            db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ctx = context(db, user, workspace_id)
    model = service.MODELS[resource]
    items, permitted = [], 0
    for row in db.scalars(select(model).where(model.organization_id == ctx.organization_id,
                                              model.workspace_id == workspace_id).order_by(model.created_at, model.id)):
        try:
            service.get(db, model, ctx, row.id, terms())
        except LegalAccessDenied:
            continue  # denied objects never count toward paging
        permitted += 1
        if permitted <= offset:
            continue
        items.append(item(db, resource, row))
        if len(items) > limit:
            break
    return {"items": items[:limit], "has_more": len(items) > limit,
            "next_offset": offset + limit if len(items) > limit else None}


def _creator(resource, request_model):
    def create(workspace_id: UUID, request: request_model, db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
        try:
            row = service.create(db, resource=resource, actor_id=user.id, workspace_id=workspace_id, request=request,
                                 current_terms_version=terms())
            out = item(db, resource, row)
            db.commit()
            return out
        except LegalAccessDenied:
            db.rollback()
            unavailable(db, user.id, workspace_id, operation="compliance_propose")
        except (regulatory.RegulatoryConflict, ValueError) as error:
            db.rollback()
            raise HTTPException(409, detail={"code": str(error)}) from error
    create.__name__ = f"create_{resource.replace('-', '_')}"
    return create


for _resource, _request in REQUESTS.items():
    router.add_api_route(f"/{_resource}", _creator(_resource, _request), methods=["POST"], status_code=201)
