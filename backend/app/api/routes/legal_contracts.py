"""Agent B versioned APIs: server-owned identity, bounded commands, uniform denial."""
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.api.routes.legal_scope import unavailable
from app.core.config import settings
from app.db.models import User
from app.db.session import get_db
from app.schemas.legal_contract import (ContractRequest, AnalysisRequest, PlaybookRequest, SummaryRequest,
    QuestionRequest, ConversationRequest, CollisionRequest, ContractVersionRequest)
from app.services import legal_contracts, legal_playbooks, legal_summaries, legal_assistant, legal_review
from app.services.legal_policy import LegalAccessDenied
from app.services.legal_extraction import ExtractionBlocked
from app.services.legal_intake import IntakeIntegrityError

router = APIRouter(prefix="/v1/workspaces/{workspace_id}", tags=["legal contracts"])


def args(user, workspace_id):
    return {"actor_id": user.id, "workspace_id": workspace_id, "current_terms_version": settings.current_terms_version}


def execute(db, user, workspace_id, call):
    from fastapi import HTTPException
    try:
        result = call()
        db.commit()
        return result
    except LegalAccessDenied:
        db.rollback()
        unavailable(db, user.id, workspace_id, operation="contract_summary_assistant")
    except (legal_contracts.ContractConflict, legal_review.LegalReviewConflict, ExtractionBlocked) as error:
        db.rollback()
        raise HTTPException(409, detail={"code": str(error)})
    except IntakeIntegrityError:
        db.rollback()
        raise HTTPException(409, detail={"code": "source_integrity_failed"})


@router.post("/contracts", status_code=201)
def create_contract(workspace_id: UUID, request: ContractRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute(db, user, workspace_id, lambda: legal_contracts.create_contract(db, **args(user, workspace_id), **request.model_dump()))


@router.get("/contracts")
def contracts(workspace_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute(db, user, workspace_id, lambda: legal_contracts.list_contracts(db, **args(user, workspace_id)))


@router.post("/contracts/{contract_id}/versions", status_code=201)
def contract_version(workspace_id: UUID, contract_id: UUID, request: ContractVersionRequest,
                     db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute(db, user, workspace_id, lambda: legal_contracts.add_version(db, contract_id=contract_id,
        **request.model_dump(), **args(user, workspace_id)))


@router.post("/contracts/{contract_id}/versions/{version_id}/analysis", status_code=201)
def analyze(workspace_id: UUID, contract_id: UUID, version_id: UUID, request: AnalysisRequest,
            db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute(db, user, workspace_id, lambda: legal_contracts.analyze(db, **args(user, workspace_id),
        contract_id=contract_id, version_id=version_id, **request.model_dump()))


@router.get("/contracts/{contract_id}/versions/{version_id}/analysis")
def analysis(workspace_id: UUID, contract_id: UUID, version_id: UUID,
             db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute(db, user, workspace_id, lambda: legal_contracts.get_analysis(db, **args(user, workspace_id),
        contract_id=contract_id, version_id=version_id))


@router.get("/clauses")
@router.get("/contract-findings")
@router.get("/obligation-proposals")
def related(workspace_id: UUID, request: Request, analysis_id: UUID | None = None,
            db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute(db, user, workspace_id, lambda: legal_contracts.list_related(db, **args(user, workspace_id),
        kind=request.url.path.rsplit("/", 1)[1], analysis_id=analysis_id))


@router.post("/obligation-proposals/{proposal_id}/review", status_code=201)
def obligation_review(workspace_id: UUID, proposal_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    def run():
        row = legal_contracts.submit_proposal(db, **args(user, workspace_id), target_type="contract_obligation", target_id=proposal_id)
        return {"review_id": row.id, "target_id": row.target_id, "target_revision_sha256": row.target_revision_sha256,
            "status": legal_review.status(db, row)}
    return execute(db, user, workspace_id, run)


@router.post("/contract-findings/{finding_id}/review", status_code=201)
def finding_review(workspace_id: UUID, finding_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    def run():
        row = legal_contracts.submit_proposal(db, **args(user, workspace_id), target_type="contract_finding", target_id=finding_id)
        return {"review_id": row.id, "target_id": row.target_id, "target_revision_sha256": row.target_revision_sha256,
            "status": legal_review.status(db, row)}
    return execute(db, user, workspace_id, run)


@router.post("/contract-findings/collisions", status_code=201)
def collisions(workspace_id: UUID, request: CollisionRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute(db, user, workspace_id, lambda: legal_contracts.propose_collisions(db, request=request, **args(user, workspace_id)))


@router.get("/contracts/{contract_id}/redline")
def redline(workspace_id: UUID, contract_id: UUID, from_version: UUID = Query(alias="from"), to_version: UUID = Query(alias="to"),
            db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute(db, user, workspace_id, lambda: legal_contracts.redline(db, **args(user, workspace_id),
        contract_id=contract_id, from_version_id=from_version, to_version_id=to_version))


@router.post("/playbooks", status_code=201)
def playbook(workspace_id: UUID, request: PlaybookRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute(db, user, workspace_id, lambda: legal_playbooks.create(db, request=request, **args(user, workspace_id)))


@router.get("/playbooks")
def playbooks(workspace_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute(db, user, workspace_id, lambda: legal_playbooks.list_playbooks(db, **args(user, workspace_id)))


@router.post("/summaries", status_code=201)
def summary(workspace_id: UUID, request: SummaryRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute(db, user, workspace_id, lambda: legal_summaries.create(db, request=request, **args(user, workspace_id)))


@router.get("/summaries")
def summaries(workspace_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute(db, user, workspace_id, lambda: legal_summaries.list_summaries(db, **args(user, workspace_id)))


@router.get("/summaries/{summary_id}")
def summary_detail(workspace_id: UUID, summary_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute(db, user, workspace_id, lambda: legal_summaries.get(db, summary_id=summary_id, **args(user, workspace_id)))


@router.get("/summaries/{summary_id}/export")
def export_summary(workspace_id: UUID, summary_id: UUID, format: str = Query(pattern="^(pdf|docx|json)$"),
                   db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data, mime = execute(db, user, workspace_id, lambda: legal_summaries.export(db, summary_id=summary_id,
        format=format, **args(user, workspace_id)))
    return Response(data, media_type=mime, headers={"Content-Disposition": f'attachment; filename="summary-{summary_id}.{format}"',
        "Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})


@router.post("/assistant/questions", status_code=201)
def question(workspace_id: UUID, request: QuestionRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute(db, user, workspace_id, lambda: legal_assistant.question(db, request=request, **args(user, workspace_id)))


@router.post("/conversations", status_code=201)
def conversation(workspace_id: UUID, request: ConversationRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute(db, user, workspace_id, lambda: legal_assistant.create_conversation(db, **request.model_dump(), **args(user, workspace_id)))


@router.get("/conversations")
def conversations(workspace_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute(db, user, workspace_id, lambda: legal_assistant.list_conversations(db, **args(user, workspace_id)))


@router.get("/conversations/{conversation_id}")
def conversation_detail(workspace_id: UUID, conversation_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute(db, user, workspace_id, lambda: legal_assistant.get_conversation(db, conversation_id=conversation_id, **args(user, workspace_id)))


@router.delete("/conversations/{conversation_id}")
def delete_conversation(workspace_id: UUID, conversation_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute(db, user, workspace_id, lambda: legal_assistant.delete_conversation(db, conversation_id=conversation_id, **args(user, workspace_id)))
