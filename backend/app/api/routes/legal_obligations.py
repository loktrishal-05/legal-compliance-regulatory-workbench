"""Obligations, tasks, remediation, exceptions, notifications, comments, audit and exports (Steps 6/7).
Deny → uniform 404 `legal_resource_unavailable`; conflict → 409 `{"code": ...}`. Actor always from session."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.legal_review import review_response
from app.api.routes.legal_scope import unavailable
from app.core.config import settings
from app.db.models import User
from app.db.session import get_db
from app.services import legal_audit_export as audit_export
from app.services import legal_obligations as ob
from app.services import legal_review
from app.services.legal_policy import LegalAccessDenied

router = APIRouter(prefix="/v1/workspaces", tags=["legal workflow"])
TaskState = Literal["open", "in_progress", "submitted", "done", "cancelled"]


class Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConfirmDeadline(Body):
    timezone: str = Field(min_length=1, max_length=64)
    due_local: str = Field(min_length=10, max_length=32, description="YYYY-MM-DD (end of local day) or wall-clock ISO")
    owner_id: UUID
    notice_days: int = Field(0, ge=0, le=365)
    recurrence_rule: str | None = Field(None, max_length=100)


class TaskPatch(Body):
    status: TaskState | None = None
    owner_id: UUID | None = None
    due_at: datetime | None = None
    add_dependency: UUID | None = None
    evidence_request: str | None = Field(None, max_length=4000)


class BulkTriage(Body):
    task_ids: list[UUID] = Field(min_length=1, max_length=200)
    status: TaskState | None = None
    owner_id: UUID | None = None


class Closure(Body):
    evidence: list[dict] = Field(min_length=1, max_length=50)
    retest_required: bool = True


class Retest(Body):
    passed: bool


class ExceptionRequest(Body):
    subject_type: str = Field(min_length=1, max_length=40, pattern=r"^[a-z_]+$")
    subject_id: UUID
    rationale: str = Field(min_length=1, max_length=4000)
    expires_at: datetime


class CommentRequest(Body):
    subject_type: Literal["task", "obligation", "review", "remediation"]
    subject_id: UUID
    body: str = Field(min_length=1, max_length=4000)
    mentions: list[UUID] = Field(default_factory=list, max_length=20)


class EvidencePackRequest(Body):
    document_ids: list[UUID] = Field(default_factory=list, max_length=200)
    review_ids: list[UUID] = Field(default_factory=list, max_length=200)


def run(db, user, workspace_id, call, operation, commit=True):
    try:
        result = call()
    except LegalAccessDenied:
        db.rollback()
        unavailable(db, user.id, workspace_id, operation=operation)
    except (ob.ObligationConflict, legal_review.LegalReviewConflict, ValueError) as error:
        db.rollback()
        raise HTTPException(409, detail={"code": str(error)})
    if commit:
        db.commit()
    return result


def obligation_out(row):
    return {"obligation_id": row.id, "status": row.status, "document_id": row.document_id,
            "version_id": row.version_id, "source_sha256": row.source_sha256, "review_id": row.review_id,
            "proposal_id": row.proposal_id, "citations": row.citations, "actor": row.actor_text,
            "action": row.action_text, "obligation_type": row.obligation_type, "trigger": row.trigger_text,
            "conditions": row.conditions, "original_deadline_phrase": row.original_deadline_phrase,
            "uncertainties": row.uncertainties, "owner_id": row.owner_id, "timezone": row.timezone,
            "due_at": row.due_at, "date_only": row.date_only, "notice_days": row.notice_days,
            "recurrence_rule": row.recurrence_rule, "calendar_policy": row.calendar_policy,
            "confirmed_by": row.confirmed_by, "confirmed_at": row.confirmed_at}


def task_out(task):
    return {"task_id": task.id, "kind": task.kind, "title": task.title, "source_type": task.source_type,
            "source_id": task.source_id, "document_id": task.document_id, "owner_id": task.owner_id,
            "due_at": task.due_at, "status": task.status, "overdue": ob.is_overdue(task),
            "evidence_request": task.evidence_request}


def terms():
    return settings.current_terms_version


@router.get("/{workspace_id}/dashboard")
def dashboard(workspace_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Counts over objects the caller may currently read; never totals that include denied objects."""
    from app.services.legal_dashboard import dashboard as aggregates
    return run(db, user, workspace_id, lambda: aggregates(db, actor_id=user.id, workspace_id=workspace_id,
        current_terms_version=terms()), "dashboard", commit=False)


@router.get("/{workspace_id}/obligations")
def list_obligations(workspace_id: UUID, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0),
                     db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return run(db, user, workspace_id, lambda: {"items": [obligation_out(r) for r in ob.list_obligations(
        db, actor_id=user.id, workspace_id=workspace_id, current_terms_version=terms(), limit=limit, offset=offset)]},
        "obligation_list", commit=False)


@router.post("/{workspace_id}/obligations/{obligation_id}/deadline")
def confirm_deadline(workspace_id: UUID, obligation_id: UUID, body: ConfirmDeadline, db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    return run(db, user, workspace_id, lambda: obligation_out(ob.confirm_deadline(db, actor_id=user.id,
        workspace_id=workspace_id, obligation_id=obligation_id, timezone_name=body.timezone, due_local=body.due_local,
        owner_id=body.owner_id, notice_days=body.notice_days, recurrence_rule=body.recurrence_rule,
        current_terms_version=terms())), "obligation_confirm")


@router.get("/{workspace_id}/tasks")
def list_tasks(workspace_id: UUID, status: str | None = Query(None, max_length=20), mine: bool = False,
               limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0),
               db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return run(db, user, workspace_id, lambda: {"items": [task_out(t) for t in ob.list_tasks(db, actor_id=user.id,
        workspace_id=workspace_id, current_terms_version=terms(), status=status, mine=mine, limit=limit,
        offset=offset)]}, "task_list", commit=False)


@router.patch("/{workspace_id}/tasks/{task_id}")
def patch_task(workspace_id: UUID, task_id: UUID, body: TaskPatch, db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    return run(db, user, workspace_id, lambda: task_out(ob.update_task(db, actor_id=user.id, workspace_id=workspace_id,
        task_id=task_id, status=body.status, owner_id=body.owner_id, due_at=body.due_at,
        add_dependency=body.add_dependency, evidence_request=body.evidence_request, current_terms_version=terms())),
        "task_update")


@router.post("/{workspace_id}/tasks/bulk")
def bulk_triage(workspace_id: UUID, body: BulkTriage, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    return run(db, user, workspace_id, lambda: {"results": ob.bulk_triage(db, actor_id=user.id,
        workspace_id=workspace_id, task_ids=body.task_ids, status=body.status, owner_id=body.owner_id,
        current_terms_version=terms())}, "task_bulk")


@router.post("/{workspace_id}/remediations/{remediation_id}/closure", status_code=201)
def submit_closure(workspace_id: UUID, remediation_id: UUID, body: Closure, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    def call():
        review = ob.submit_closure(db, actor_id=user.id, workspace_id=workspace_id, remediation_id=remediation_id,
            evidence=body.evidence, retest_required=body.retest_required, current_terms_version=terms())
        return review_response(db, review)
    return run(db, user, workspace_id, call, "remediation_closure")


@router.post("/{workspace_id}/remediations/{remediation_id}/retest")
def record_retest(workspace_id: UUID, remediation_id: UUID, body: Retest, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    def call():
        row = ob.record_retest(db, actor_id=user.id, workspace_id=workspace_id, remediation_id=remediation_id,
                               passed=body.passed, current_terms_version=terms())
        return {"remediation_id": row.id, "status": row.status, "retest_passed": row.retest_passed,
                "reopen_count": row.reopen_count}
    return run(db, user, workspace_id, call, "remediation_retest")


@router.post("/{workspace_id}/exceptions", status_code=201)
def propose_exception(workspace_id: UUID, body: ExceptionRequest, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    def call():
        row, review = ob.propose_exception(db, actor_id=user.id, workspace_id=workspace_id,
            subject_type=body.subject_type, subject_id=body.subject_id, rationale=body.rationale,
            expires_at=body.expires_at, current_terms_version=terms())
        return {"exception_id": row.id, "status": row.status, "expires_at": row.expires_at,
                "exception_sha256": row.exception_sha256, "review": review_response(db, review)}
    return run(db, user, workspace_id, call, "exception_propose")


@router.get("/{workspace_id}/notifications")
def list_notifications(workspace_id: UUID, unread: bool = False, db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    return run(db, user, workspace_id, lambda: {"items": [{"notification_id": n.id, "kind": n.kind,
        "subject_type": n.subject_type, "subject_id": n.subject_id, "created_at": n.created_at, "read_at": n.read_at}
        for n in ob.list_notifications(db, actor_id=user.id, workspace_id=workspace_id, unread=unread,
                                       current_terms_version=terms())]}, "notification_list", commit=False)


@router.post("/{workspace_id}/notifications/{notification_id}/read")
def read_notification(workspace_id: UUID, notification_id: UUID, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    return run(db, user, workspace_id, lambda: {"notification_id": notification_id, "read_at": ob.mark_read(
        db, actor_id=user.id, workspace_id=workspace_id, notification_id=notification_id,
        current_terms_version=terms()).read_at}, "notification_read")


@router.post("/{workspace_id}/comments", status_code=201)
def add_comment(workspace_id: UUID, body: CommentRequest, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    def call():
        row = ob.add_comment(db, actor_id=user.id, workspace_id=workspace_id, subject_type=body.subject_type,
            subject_id=body.subject_id, body=body.body, mentions=body.mentions, current_terms_version=terms())
        return {"comment_id": row.id, "subject_type": row.subject_type, "subject_id": row.subject_id,
                "author_id": row.author_id, "body": row.body, "mentions": row.mentions}
    return run(db, user, workspace_id, call, "comment_add")


@router.get("/{workspace_id}/comments")
def list_comments(workspace_id: UUID, subject_type: Literal["task", "obligation", "review", "remediation"],
                  subject_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return run(db, user, workspace_id, lambda: {"items": [{"comment_id": c.id, "author_id": c.author_id,
        "body": c.body, "mentions": c.mentions, "created_at": c.created_at} for c in ob.list_comments(db,
        actor_id=user.id, workspace_id=workspace_id, subject_type=subject_type, subject_id=subject_id,
        current_terms_version=terms())]}, "comment_list", commit=False)


@router.get("/{workspace_id}/audit")
def audit(workspace_id: UUID, event_type: str | None = Query(None, max_length=60), since: datetime | None = None,
          until: datetime | None = None, limit: int = Query(200, ge=1, le=1000), db: Session = Depends(get_db),
          user: User = Depends(get_current_user)):
    return run(db, user, workspace_id, lambda: {"items": audit_export.audit_events(db, actor_id=user.id,
        workspace_id=workspace_id, event_type=event_type, since=since, until=until, limit=limit,
        current_terms_version=terms())}, "audit_read", commit=False)


@router.get("/{workspace_id}/audit/snapshot")
def audit_snapshot(workspace_id: UUID, as_of: datetime, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    return run(db, user, workspace_id, lambda: audit_export.snapshot(db, actor_id=user.id, workspace_id=workspace_id,
        as_of=as_of, current_terms_version=terms()), "audit_snapshot", commit=False)


@router.post("/{workspace_id}/evidence-packs", status_code=201)
def evidence_pack(workspace_id: UUID, body: EvidencePackRequest, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    def call():
        row = audit_export.create_evidence_pack(db, actor_id=user.id, workspace_id=workspace_id,
            document_ids=body.document_ids, review_ids=body.review_ids, current_terms_version=terms())
        return {"export_id": row.id, "kind": row.kind, "manifest_sha256": row.manifest_sha256}
    return run(db, user, workspace_id, call, "evidence_pack")


@router.post("/{workspace_id}/exports/findings", status_code=201)
def findings_export(workspace_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    def call():
        row = audit_export.create_findings_export(db, actor_id=user.id, workspace_id=workspace_id,
                                                  current_terms_version=terms())
        return {"export_id": row.id, "kind": row.kind, "manifest_sha256": row.manifest_sha256}
    return run(db, user, workspace_id, call, "findings_export")


@router.get("/{workspace_id}/exports/{export_id}")
def read_export(workspace_id: UUID, export_id: UUID, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    return run(db, user, workspace_id, lambda: audit_export.get_export(db, actor_id=user.id,
        workspace_id=workspace_id, export_id=export_id, current_terms_version=terms()), "export_read", commit=False)
