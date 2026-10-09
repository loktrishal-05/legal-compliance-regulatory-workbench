"""Scoped exact-revision review queue; uniform unavailable responses as in legal_scope."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.legal_scope import unavailable
from app.core.config import settings
from app.db.models import User
from app.db.models.legal_review import LegalReview
from app.db.session import get_db
from app.schemas.legal_review import ReviewDecisionRequest, ReviewDecisionResponse, ReviewRequest, ReviewResponse
from app.services import legal_review
from app.services.legal_policy import LegalAccessDenied, authorize_workspace

router = APIRouter(prefix="/v1/workspaces", tags=["legal reviews"])


def review_response(db, review) -> ReviewResponse:
    return ReviewResponse(review_id=review.id, target_type=review.target_type, target_id=review.target_id,
        target_revision_sha256=review.target_revision_sha256, requester_id=review.requester_id,
        status=legal_review.status(db, review), created_at=review.created_at,
        decisions=[ReviewDecisionResponse(decision_id=row.id, reviewer_id=row.reviewer_id, decision=row.decision,
                   rationale=row.rationale, created_at=row.created_at) for row in legal_review.decisions(db, review.id)])


def command(db, user, workspace_id, call, operation):
    try:
        result = call()
    except LegalAccessDenied:
        db.rollback()
        unavailable(db, user.id, workspace_id, operation=operation)
    except legal_review.LegalReviewConflict as error:
        db.rollback()
        raise HTTPException(409, detail={"code": str(error)})
    response = review_response(db, result)
    db.commit()
    return response


@router.post("/{workspace_id}/reviews", response_model=ReviewResponse, status_code=201)
def submit_review(workspace_id: UUID, request: ReviewRequest, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    return command(db, user, workspace_id, lambda: legal_review.submit(db, workspace_id=workspace_id,
        target_type=request.target_type, target_id=request.target_id,
        target_revision_sha256=request.target_revision_sha256, requester_id=user.id,
        idempotency_key=request.idempotency_key, current_terms_version=settings.current_terms_version), "review_submit")


@router.post("/{workspace_id}/reviews/{review_id}/decisions", response_model=ReviewResponse, status_code=201)
def decide_review(workspace_id: UUID, review_id: UUID, request: ReviewDecisionRequest, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    def call():
        legal_review.decide(db, workspace_id=workspace_id, review_id=review_id, reviewer_id=user.id,
            decision=request.decision, rationale=request.rationale, current_terms_version=settings.current_terms_version)
        return legal_review.get(db, workspace_id=workspace_id, review_id=review_id, actor_id=user.id,
                                current_terms_version=settings.current_terms_version)
    return command(db, user, workspace_id, call, "review_decide")


@router.get("/{workspace_id}/reviews/{review_id}", response_model=ReviewResponse)
def read_review(workspace_id: UUID, review_id: UUID, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    return command(db, user, workspace_id, lambda: legal_review.get(db, workspace_id=workspace_id,
        review_id=review_id, actor_id=user.id, current_terms_version=settings.current_terms_version), "review_read")


@router.get("/{workspace_id}/reviews", response_model=list[ReviewResponse])
def list_reviews(workspace_id: UUID, status: str | None = Query(None, max_length=30),
                 target_type: str | None = Query(None, max_length=60), limit: int = Query(50, ge=1, le=200),
                 offset: int = Query(0, ge=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Objects the actor may not see are skipped before paging, so totals never reveal them."""
    terms = settings.current_terms_version
    try:
        authorize_workspace(db, user.id, workspace_id, current_terms_version=terms)
    except LegalAccessDenied:
        unavailable(db, user.id, workspace_id, operation="review_list")
    query = select(LegalReview.id).where(LegalReview.workspace_id == workspace_id)
    if target_type:
        query = query.where(LegalReview.target_type == target_type)
    visible = []
    for review_id in db.scalars(query.order_by(LegalReview.created_at.desc(), LegalReview.id)):
        try:
            review = legal_review.get(db, workspace_id=workspace_id, review_id=review_id, actor_id=user.id,
                                      current_terms_version=terms)
        except LegalAccessDenied:
            continue
        response = review_response(db, review)
        if status is None or response.status == status:
            visible.append(response)
    return visible[offset:offset + limit]  # ponytail: in-memory filter after per-object auth; SQL paging when queues grow large
