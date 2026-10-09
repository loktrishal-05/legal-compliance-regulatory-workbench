"""Step 6/7 workflow: accepted obligations, deterministic deadlines, durable timers, tasks, remediation,
exceptions, in-app notifications and comments. Caller commits (handlers/scans run in worker transactions).

No LLM schedules anything. Dates stay `needs_confirmation` until a human legal reviewer confirms an IANA
timezone and a local date/time; nonexistent/ambiguous local times are refused, not guessed; no business-day
calendar is assumed. Recurrence follows RFC 5545 skipping (e.g. Feb 29 yearly only in leap years).
"""
import calendar
import hashlib
import json
import re
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.legal_obligations import (LegalComment, LegalDeadlineOccurrence, LegalDispatchReceipt,
    LegalException, LegalNotification, LegalObligation, LegalRemediation, LegalTask, LegalTaskDependency)
from app.db.models.legal_review import LegalReview, LegalReviewDecision
from app.db.models.legal_scope import WorkspaceMembership
from app.services import legal_events, legal_review, legal_scheduler
from app.services.audit import append_event
from app.services.legal_policy import LegalAccessDenied, ROLE_OPERATIONS, authorize_document, authorize_workspace

POLICY = "legal-deadline-v1"
MAX_OCCURRENCES = 24
RULE = re.compile(r"^FREQ=(DAILY|WEEKLY|MONTHLY|YEARLY)(;INTERVAL=([1-9][0-9]?))?;COUNT=([1-9][0-9]?)$")
TASK_STATES = ("open", "in_progress", "submitted", "done", "cancelled")
MANAGE_OPS = {"propose", "review_legal", "review_compliance"}


class ObligationConflict(ValueError):
    pass


def _terms():
    from app.core.config import settings
    return settings.current_terms_version


def _aware(value):
    return value if value is None or value.tzinfo else value.replace(tzinfo=timezone.utc)  # SQLite returns naive UTC


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _system_audit(db, workspace_id, organization_id, action, **details):
    append_event(db, event_type="LEGAL_ACTIVITY_RECORDED", actor_id=None, actor_kind="system", payload={
        "policy_version": "legal-activity-v1", "action": action, "organization_id": str(organization_id),
        "workspace_id": str(workspace_id), **details})


def _approved_any(db, workspace_id, target_type, target_id):
    return db.scalar(select(LegalReviewDecision.id).join(LegalReview, LegalReview.id == LegalReviewDecision.review_id)
        .where(LegalReview.workspace_id == workspace_id, LegalReview.target_type == target_type,
               LegalReview.target_id == target_id, LegalReviewDecision.decision == "approve")) is not None


def _receipt(db, key, workspace_id, organization_id, kind) -> bool:
    """True exactly once per key, across workers and restarts."""
    if db.get(LegalDispatchReceipt, key) is not None:
        return False
    try:
        with db.begin_nested():
            db.add(LegalDispatchReceipt(receipt_key=key, organization_id=organization_id, workspace_id=workspace_id,
                                        kind=kind))
            db.flush()
        return True
    except IntegrityError:
        return False


def notify(db, *, workspace_id, organization_id, recipient_id, kind, subject_type, subject_id, dedupe_key):
    if recipient_id is None or db.scalar(select(LegalNotification.id).where(
            LegalNotification.workspace_id == workspace_id, LegalNotification.recipient_id == recipient_id,
            LegalNotification.dedupe_key == dedupe_key)):
        return None
    row = LegalNotification(id=uuid4(), organization_id=organization_id, workspace_id=workspace_id,
        recipient_id=recipient_id, kind=kind, subject_type=subject_type, subject_id=subject_id, dedupe_key=dedupe_key)
    db.add(row)
    db.flush()
    return row


def _task(db, *, workspace_id, organization_id, kind, title, source_type, source_id, document_id=None, owner_id=None,
          due_at=None, evidence_request=None):
    existing = db.scalar(select(LegalTask).where(LegalTask.workspace_id == workspace_id,
        LegalTask.source_type == source_type, LegalTask.source_id == source_id, LegalTask.kind == kind))
    if existing:
        return existing
    row = LegalTask(id=uuid4(), organization_id=organization_id, workspace_id=workspace_id, kind=kind, title=title[:300],
        source_type=source_type, source_id=source_id, document_id=document_id, owner_id=owner_id, due_at=due_at,
        status="open", evidence_request=evidence_request)
    db.add(row)
    db.flush()
    return row


# --- event handlers (registered at import; run by the worker inside the dispatch transaction) -------------

def on_obligation_accepted(db: Session, event):
    p = event.payload
    proposal_id = UUID(p["proposal_id"])
    if not _approved_any(db, event.workspace_id, "contract_obligation", proposal_id):
        raise ObligationConflict("obligation_not_independently_approved")  # accepted only; retried then dead-lettered
    existing = db.scalar(select(LegalObligation).where(LegalObligation.workspace_id == event.workspace_id,
        LegalObligation.proposal_id == proposal_id, LegalObligation.proposal_sha256 == p["proposal_sha256"]))
    if existing:
        return existing

    def text(key):
        return str(p.get(key) or "")[:4000]
    row = LegalObligation(id=uuid4(), organization_id=event.organization_id, workspace_id=event.workspace_id,
        proposal_id=proposal_id, proposal_sha256=p["proposal_sha256"], review_id=UUID(p["review_id"]),
        source_event_id=event.id, document_id=UUID(p["document_id"]), version_id=UUID(p["version_id"]),
        source_sha256=p["source_sha256"], citations=list(p.get("citations") or []), actor_text=text("actor"),
        action_text=text("action"), obligation_type=str(p.get("obligation_type") or "duty")[:40],
        trigger_text=text("trigger"), conditions=list(p.get("conditions") or []),
        original_deadline_phrase=text("original_deadline_phrase"), uncertainties=list(p.get("uncertainties") or []),
        status="needs_confirmation", notice_days=0, date_only=False, calendar_policy=POLICY)
    db.add(row)
    db.flush()
    _task(db, workspace_id=row.workspace_id, organization_id=row.organization_id, kind="obligation",
          title="Confirm owner, timezone and deadline for accepted obligation", source_type="obligation",
          source_id=row.id, document_id=row.document_id)
    _system_audit(db, row.workspace_id, row.organization_id, "obligation_created", obligation_id=str(row.id),
                  proposal_id=str(proposal_id), review_id=p["review_id"], source_sha256=row.source_sha256)
    return row


def on_finding_accepted(db: Session, event):
    p = event.payload
    finding_id = UUID(p["finding_id"])
    if not _approved_any(db, event.workspace_id, "compliance_finding", finding_id):
        raise ObligationConflict("finding_not_independently_approved")
    if db.scalar(select(LegalRemediation.id).where(LegalRemediation.workspace_id == event.workspace_id,
                                                   LegalRemediation.finding_id == finding_id)):
        return None
    task = _task(db, workspace_id=event.workspace_id, organization_id=event.organization_id, kind="remediation",
                 title="Remediate accepted compliance finding", source_type="compliance_finding", source_id=finding_id)
    row = LegalRemediation(id=uuid4(), organization_id=event.organization_id, workspace_id=event.workspace_id,
        finding_id=finding_id, assessment_id=UUID(p["assessment_id"]) if p.get("assessment_id") else None,
        task_id=task.id, status="open", closure_evidence=[], retest_required=True, reopen_count=0)
    db.add(row)
    db.flush()
    _system_audit(db, row.workspace_id, row.organization_id, "remediation_created", remediation_id=str(row.id),
                  finding_id=str(finding_id))
    return row


def on_evidence_expired(db: Session, event):
    p = event.payload
    _task(db, workspace_id=event.workspace_id, organization_id=event.organization_id, kind="evidence_expired",
          title="Replace expired compliance evidence", source_type="evidence_version",
          source_id=UUID(p["evidence_version_id"]),
          evidence_request="Provide current evidence replacing the expired version")


def on_regulatory_change(db: Session, event):
    change_id = UUID(event.payload["change_id"])
    if not _approved_any(db, event.workspace_id, "regulatory_change", change_id):
        raise ObligationConflict("change_not_independently_approved")
    _task(db, workspace_id=event.workspace_id, organization_id=event.organization_id, kind="regulatory_change",
          title="Assess impact of accepted regulatory change", source_type="regulatory_change", source_id=change_id)


legal_events.register_handler("legal.contract.obligation_accepted", on_obligation_accepted)
legal_events.register_handler("legal.compliance.finding_accepted", on_finding_accepted)
legal_events.register_handler("legal.compliance.evidence_expired", on_evidence_expired)
legal_events.register_handler("legal.regulatory.change_accepted", on_regulatory_change)


# --- deterministic deadlines -----------------------------------------------------------------------------

def _localize(naive: datetime, zone: ZoneInfo) -> datetime:
    first, second = naive.replace(tzinfo=zone, fold=0), naive.replace(tzinfo=zone, fold=1)
    if first.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) != naive:
        raise ObligationConflict("local_time_nonexistent")  # DST spring-forward gap
    if first.utcoffset() != second.utcoffset():
        raise ObligationConflict("local_time_ambiguous")  # DST fall-back overlap needs a human choice
    return first.astimezone(timezone.utc)


def _add_months(value: datetime, months: int) -> datetime | None:
    month0 = value.month - 1 + months
    year, month = value.year + month0 // 12, month0 % 12 + 1
    if value.day > calendar.monthrange(year, month)[1]:
        return None  # RFC 5545: invalid dates are skipped, never clamped
    return value.replace(year=year, month=month)


def occurrences(local_due: datetime, zone: ZoneInfo, rule: str | None) -> list[datetime]:
    if not rule:
        return [_localize(local_due, zone)]
    match = RULE.match(rule)
    if not match:
        raise ObligationConflict("recurrence_rule_unsupported")
    freq, interval, count = match.group(1), int(match.group(3) or 1), min(int(match.group(4)), MAX_OCCURRENCES)
    out, step = [], 0
    while len(out) < count and step < count * 12:
        if freq in ("DAILY", "WEEKLY"):
            candidate = local_due + timedelta(days=step * interval * (7 if freq == "WEEKLY" else 1))
        else:
            candidate = _add_months(local_due, step * interval * (12 if freq == "YEARLY" else 1))
        if candidate is not None:
            out.append(_localize(candidate, zone))  # wall-clock time is preserved across DST
        step += 1
    return out


def _obligation_ctx(db, actor_id, workspace_id, obligation_id, terms):
    row = db.scalar(select(LegalObligation).where(LegalObligation.id == obligation_id,
                                                  LegalObligation.workspace_id == workspace_id))
    if row is None:
        raise LegalAccessDenied()
    if row.owner_id == actor_id:
        return authorize_workspace(db, actor_id, workspace_id, current_terms_version=terms), row
    return authorize_document(db, actor_id, workspace_id, row.document_id, current_terms_version=terms), row


def _active_member(db, workspace_id, user_id):
    member = db.get(WorkspaceMembership, (workspace_id, user_id))
    if member is None or not member.is_active:
        raise LegalAccessDenied()
    return member


def confirm_deadline(db: Session, *, actor_id: UUID, workspace_id: UUID, obligation_id: UUID, timezone_name: str | None,
                     due_local: str | None, owner_id: UUID, notice_days: int = 0, recurrence_rule: str | None = None,
                     current_terms_version: str | None = None) -> LegalObligation:
    """Human legal reviewer confirms owner + IANA timezone + local due date/time. Date-only = end of local day."""
    terms = current_terms_version or _terms()
    ctx, row = _obligation_ctx(db, actor_id, workspace_id, obligation_id, terms)
    if "review_legal" not in ROLE_OPERATIONS[ctx.role]:
        raise LegalAccessDenied()
    if not timezone_name:
        raise ObligationConflict("timezone_required")
    if not due_local:
        raise ObligationConflict("due_date_required")
    try:
        zone = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        raise ObligationConflict("timezone_unknown")
    if not 0 <= notice_days <= 365:
        raise ObligationConflict("notice_days_invalid")
    try:
        date_only = len(due_local) == 10
        local = (datetime.combine(date.fromisoformat(due_local), time(23, 59, 59)) if date_only
                 else datetime.fromisoformat(due_local))
    except ValueError:
        raise ObligationConflict("due_date_invalid")
    if local.tzinfo is not None:
        raise ObligationConflict("due_local_must_be_wall_clock")
    _active_member(db, workspace_id, owner_id)
    authorize_document(db, owner_id, workspace_id, row.document_id, current_terms_version=terms)  # owner sees source
    times = occurrences(local, zone, recurrence_rule)
    if row.status != "needs_confirmation":
        raise ObligationConflict("obligation_already_confirmed")
    row.timezone, row.due_at, row.date_only, row.notice_days = timezone_name, times[0], date_only, notice_days
    row.recurrence_rule, row.owner_id, row.status = recurrence_rule, owner_id, "active"
    row.confirmed_by, row.confirmed_at = actor_id, datetime.now(timezone.utc)
    for sequence, due in enumerate(times, start=1):
        db.add(LegalDeadlineOccurrence(id=uuid4(), organization_id=row.organization_id, workspace_id=workspace_id,
                                       obligation_id=row.id, sequence=sequence, due_at=due, status="scheduled"))
    task = db.scalar(select(LegalTask).where(LegalTask.workspace_id == workspace_id,
        LegalTask.source_type == "obligation", LegalTask.source_id == row.id))
    if task:
        task.owner_id, task.due_at = owner_id, times[0]
    db.flush()
    legal_events.audit_activity(db, ctx, "obligation_deadline_confirmed", obligation_id=str(row.id),
        timezone=timezone_name, due_at=times[0].isoformat(), date_only=date_only, occurrences=len(times),
        recurrence_rule=recurrence_rule, owner_id=str(owner_id), calendar_policy=POLICY)
    notify(db, workspace_id=workspace_id, organization_id=row.organization_id, recipient_id=owner_id,
           kind="obligation_assigned", subject_type="obligation", subject_id=row.id, dedupe_key=f"assigned:{row.id}")
    return row


def scan_deadlines(db: Session, now: datetime) -> int:
    """Reminders (due - notice) and overdue escalations, each exactly once via receipts; catches up after downtime."""
    effects = 0
    rows = db.execute(select(LegalDeadlineOccurrence, LegalObligation).join(LegalObligation,
        LegalObligation.id == LegalDeadlineOccurrence.obligation_id).where(
        LegalDeadlineOccurrence.status == "scheduled", LegalObligation.status == "active",
        LegalDeadlineOccurrence.due_at <= now + timedelta(days=366))).all()
    for occ, obligation in rows:
        due = _aware(occ.due_at)
        plan = []
        if obligation.notice_days and now >= due - timedelta(days=obligation.notice_days):
            plan.append(("reminder", f"reminder:{occ.id}"))
        if now >= due:
            plan.append(("overdue_escalation", f"escalation:{occ.id}"))
        for kind, key in plan:
            if _receipt(db, key, occ.workspace_id, occ.organization_id, kind):
                notify(db, workspace_id=occ.workspace_id, organization_id=occ.organization_id,
                       recipient_id=obligation.owner_id, kind=kind, subject_type="obligation",
                       subject_id=obligation.id, dedupe_key=key)
                effects += 1
    return effects


def scan_exception_expiry(db: Session, now: datetime) -> int:
    count = 0
    for row in db.scalars(select(LegalException).where(LegalException.status == "active",
                                                       LegalException.expires_at <= now)):
        if _receipt(db, f"exception-expired:{row.id}", row.workspace_id, row.organization_id, "exception_expired"):
            row.status = "expired"
            member = db.get(WorkspaceMembership, (row.workspace_id, row.requester_id))
            _task(db, workspace_id=row.workspace_id, organization_id=row.organization_id, kind="exception_expired",
                  title="Risk acceptance expired: re-assess or renew", source_type="exception", source_id=row.id,
                  owner_id=row.requester_id if member and member.is_active else None)
            if member and member.is_active:
                notify(db, workspace_id=row.workspace_id, organization_id=row.organization_id,
                       recipient_id=row.requester_id, kind="exception_expired", subject_type="exception",
                       subject_id=row.id, dedupe_key=f"exception-expired:{row.id}")
            _system_audit(db, row.workspace_id, row.organization_id, "exception_expired", exception_id=str(row.id))
            count += 1
    return count


legal_scheduler.register_scan("legal-deadlines", scan_deadlines)
legal_scheduler.register_scan("legal-exception-expiry", scan_exception_expiry)


# --- tasks ------------------------------------------------------------------------------------------------

def task_visible(db, ctx, task, terms) -> bool:
    if task.owner_id == ctx.actor_id:
        return True
    if task.document_id is not None:
        try:
            authorize_document(db, ctx.actor_id, ctx.workspace_id, task.document_id, current_terms_version=terms)
            return True
        except LegalAccessDenied:
            return False
    return bool(ROLE_OPERATIONS[ctx.role] & MANAGE_OPS)


def _task_for(db, actor_id, workspace_id, task_id, terms, lock=False):
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=terms)
    query = select(LegalTask).where(LegalTask.id == task_id, LegalTask.workspace_id == workspace_id,
                                    LegalTask.organization_id == ctx.organization_id)
    task = db.scalar(query.with_for_update() if lock else query)
    if task is None or not task_visible(db, ctx, task, terms):
        raise LegalAccessDenied()
    return ctx, task


def list_tasks(db, *, actor_id, workspace_id, current_terms_version=None, status=None, mine=False, limit=100, offset=0):
    terms = current_terms_version or _terms()
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=terms)
    query = select(LegalTask).where(LegalTask.workspace_id == workspace_id)
    if status:
        query = query.where(LegalTask.status == status)
    if mine:
        query = query.where(LegalTask.owner_id == actor_id)
    visible = [t for t in db.scalars(query.order_by(LegalTask.due_at.is_(None), LegalTask.due_at, LegalTask.id))
               if task_visible(db, ctx, t, terms)]
    return visible[offset:offset + limit]  # ponytail: per-object auth in Python; push into SQL when queues grow


def _would_cycle(db, task_id, depends_on_id):
    stack, seen = [depends_on_id], set()
    while stack:
        current = stack.pop()
        if current == task_id:
            return True
        if current in seen:
            continue
        seen.add(current)
        stack.extend(db.scalars(select(LegalTaskDependency.depends_on_id).where(LegalTaskDependency.task_id == current)))
    return False


def update_task(db, *, actor_id, workspace_id, task_id, status=None, owner_id=None, due_at=None,
                add_dependency=None, evidence_request=None, current_terms_version=None) -> LegalTask:
    terms = current_terms_version or _terms()
    ctx, task = _task_for(db, actor_id, workspace_id, task_id, terms, lock=True)
    can_manage = bool(ROLE_OPERATIONS[ctx.role] & MANAGE_OPS)
    changes = {}
    if status is not None:
        if status not in TASK_STATES:
            raise ObligationConflict("task_status_invalid")
        if task.kind == "remediation" and status == "done":
            raise ObligationConflict("remediation_closure_requires_review")  # progress is not authoritative closure
        if not can_manage and not (task.owner_id == actor_id and status in ("in_progress", "submitted")):
            raise LegalAccessDenied()
        if status == "done" and any(db.get(LegalTask, d).status != "done" for d in db.scalars(
                select(LegalTaskDependency.depends_on_id).where(LegalTaskDependency.task_id == task.id))):
            raise ObligationConflict("task_dependencies_open")
        changes["status"], task.status = status, status
    if owner_id is not None:
        if not can_manage:
            raise LegalAccessDenied()
        _active_member(db, workspace_id, owner_id)
        if task.document_id is not None:  # reassignment to someone without a current grant is denied
            authorize_document(db, owner_id, workspace_id, task.document_id, current_terms_version=terms)
        else:
            authorize_workspace(db, owner_id, workspace_id, current_terms_version=terms)
        changes["owner_id"], task.owner_id = str(owner_id), owner_id
        notify(db, workspace_id=workspace_id, organization_id=task.organization_id, recipient_id=owner_id,
               kind="task_assigned", subject_type="task", subject_id=task.id,
               dedupe_key=f"task-assigned:{task.id}:{owner_id}")
    if due_at is not None:
        if not can_manage:
            raise LegalAccessDenied()
        if due_at.tzinfo is None:
            raise ObligationConflict("due_at_requires_timezone")
        changes["due_at"], task.due_at = due_at.isoformat(), due_at
    if evidence_request is not None:
        if not can_manage:
            raise LegalAccessDenied()
        changes["evidence_request"], task.evidence_request = "set", evidence_request[:4000]
    if add_dependency is not None:
        if not can_manage:
            raise LegalAccessDenied()
        _task_for(db, actor_id, workspace_id, add_dependency, terms)
        if add_dependency == task.id or _would_cycle(db, task.id, add_dependency):
            raise ObligationConflict("task_dependency_cycle")
        if db.get(LegalTaskDependency, (task.id, add_dependency)) is None:
            db.add(LegalTaskDependency(organization_id=task.organization_id, workspace_id=workspace_id,
                                       task_id=task.id, depends_on_id=add_dependency))
        changes["depends_on"] = str(add_dependency)
    db.flush()
    legal_events.audit_activity(db, ctx, "task_updated", task_id=str(task.id), **changes)
    return task


def bulk_triage(db, *, actor_id, workspace_id, task_ids, status=None, owner_id=None, current_terms_version=None):
    """FR-047: each object is authorized on its own; denied and unknown IDs both report 'unavailable'."""
    results = {}
    for task_id in task_ids[:200]:
        try:
            with db.begin_nested():
                update_task(db, actor_id=actor_id, workspace_id=workspace_id, task_id=task_id, status=status,
                            owner_id=owner_id, current_terms_version=current_terms_version)
            results[str(task_id)] = "ok"
        except LegalAccessDenied:
            results[str(task_id)] = "unavailable"
        except ObligationConflict as error:
            results[str(task_id)] = f"conflict:{error}"
    return results


def is_overdue(task, now=None):
    return task.due_at is not None and task.status not in ("done", "cancelled") and _aware(task.due_at) < (
        now or datetime.now(timezone.utc))


def list_obligations(db, *, actor_id, workspace_id, current_terms_version=None, limit=100, offset=0):
    terms = current_terms_version or _terms()
    authorize_workspace(db, actor_id, workspace_id, current_terms_version=terms)
    out = []
    for row in db.scalars(select(LegalObligation).where(LegalObligation.workspace_id == workspace_id)
                          .order_by(LegalObligation.due_at.is_(None), LegalObligation.due_at, LegalObligation.id)):
        try:
            _obligation_ctx(db, actor_id, workspace_id, row.id, terms)
            out.append(row)
        except LegalAccessDenied:
            continue
    return out[offset:offset + limit]


# --- remediation and exceptions ---------------------------------------------------------------------------

def _remediation(db, actor_id, workspace_id, remediation_id, terms, lock=False):
    query = select(LegalRemediation).where(LegalRemediation.id == remediation_id,
                                           LegalRemediation.workspace_id == workspace_id)
    row = db.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise LegalAccessDenied()
    ctx, _ = _task_for(db, actor_id, workspace_id, row.task_id, terms)
    return ctx, row


def submit_closure(db, *, actor_id, workspace_id, remediation_id, evidence: list[dict], retest_required: bool = True,
                   current_terms_version=None):
    """Closure evidence + exact closure revision; returns the review the independent reviewer must decide."""
    terms = current_terms_version or _terms()
    ctx, row = _remediation(db, actor_id, workspace_id, remediation_id, terms, lock=True)
    if "propose" not in ROLE_OPERATIONS[ctx.role]:
        raise LegalAccessDenied()
    if not evidence or len(evidence) > 50 or not all(isinstance(e, dict) and e.get("evidence_id") for e in evidence):
        raise ObligationConflict("closure_evidence_required")
    if row.status == "closed":
        raise ObligationConflict("remediation_already_closed")
    digest = _digest({"remediation_id": str(row.id), "evidence": evidence, "retest_required": retest_required,
                      "reopen_count": row.reopen_count})
    row.closure_evidence, row.closure_sha256, row.retest_required = evidence, digest, retest_required
    row.status, row.retest_passed = "submitted", None
    db.get(LegalTask, row.task_id).status = "submitted"
    db.flush()
    review = legal_review.submit(db, workspace_id=workspace_id, target_type="remediation_closure", target_id=row.id,
        target_revision_sha256=digest, requester_id=actor_id, idempotency_key=f"remediation-closure:{digest}",
        current_terms_version=terms)
    legal_events.audit_activity(db, ctx, "remediation_closure_submitted", remediation_id=str(row.id),
                                closure_sha256=digest, review_id=str(review.id))
    return review


def _approve_closure(db, review):
    row = db.scalar(select(LegalRemediation).where(LegalRemediation.id == review.target_id).with_for_update())
    if row is None or row.closure_sha256 != review.target_revision_sha256 or row.status != "submitted":
        raise ObligationConflict("closure_revision_stale")
    row.status, row.closed_review_id = "closed", review.id
    db.get(LegalTask, row.task_id).status = "done"
    db.flush()


def _closure_authorize(db, ctx, remediation_id):
    _remediation(db, ctx.actor_id, ctx.workspace_id, remediation_id, _terms())


legal_review.register_target("remediation_closure", on_approve=_approve_closure, authorize=_closure_authorize)


def record_retest(db, *, actor_id, workspace_id, remediation_id, passed: bool, current_terms_version=None):
    terms = current_terms_version or _terms()
    ctx, row = _remediation(db, actor_id, workspace_id, remediation_id, terms, lock=True)
    if "review_compliance" not in ROLE_OPERATIONS[ctx.role]:
        raise LegalAccessDenied()
    row.retest_passed = passed
    if not passed:  # failed retest (or drift) reopens; a new closure revision and review are required
        row.status, row.reopen_count, row.closed_review_id = "reopened", row.reopen_count + 1, None
        task = db.get(LegalTask, row.task_id)
        task.status = "open"
        notify(db, workspace_id=workspace_id, organization_id=row.organization_id, recipient_id=task.owner_id,
               kind="remediation_reopened", subject_type="remediation", subject_id=row.id,
               dedupe_key=f"reopened:{row.id}:{row.reopen_count}")
    db.flush()
    legal_events.audit_activity(db, ctx, "remediation_retest_recorded", remediation_id=str(row.id), passed=passed,
                                reopen_count=row.reopen_count)
    return row


def propose_exception(db, *, actor_id, workspace_id, subject_type, subject_id, rationale, expires_at: datetime,
                      current_terms_version=None):
    terms = current_terms_version or _terms()
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=terms)
    if "propose" not in ROLE_OPERATIONS[ctx.role]:
        raise LegalAccessDenied()
    now = datetime.now(timezone.utc)
    if expires_at is None or expires_at.tzinfo is None:
        raise ObligationConflict("exception_expiry_required")
    if not now < expires_at <= now + timedelta(days=366):
        raise ObligationConflict("exception_expiry_out_of_range")
    if not rationale or not rationale.strip() or len(rationale) > 4000:
        raise ObligationConflict("exception_rationale_required")
    digest = _digest({"subject_type": subject_type, "subject_id": str(subject_id), "rationale": rationale,
                      "expires_at": expires_at.isoformat(), "requester_id": str(actor_id)})
    row = LegalException(id=uuid4(), organization_id=ctx.organization_id, workspace_id=workspace_id,
        subject_type=subject_type[:40], subject_id=subject_id, rationale=rationale, expires_at=expires_at,
        requester_id=actor_id, exception_sha256=digest, status="proposed", created_at=now)
    db.add(row)
    db.flush()
    review = legal_review.submit(db, workspace_id=workspace_id, target_type="exception", target_id=row.id,
        target_revision_sha256=digest, requester_id=actor_id, idempotency_key=f"exception:{digest}",
        current_terms_version=terms)
    legal_events.audit_activity(db, ctx, "exception_proposed", exception_id=str(row.id), exception_sha256=digest,
                                expires_at=expires_at.isoformat(), review_id=str(review.id))
    return row, review


def _approve_exception(db, review):
    row = db.get(LegalException, review.target_id)
    if row is None or row.exception_sha256 != review.target_revision_sha256 or row.status != "proposed":
        raise ObligationConflict("exception_revision_stale")
    if _aware(row.expires_at) <= datetime.now(timezone.utc):
        raise ObligationConflict("exception_already_expired")
    row.status = "active"
    db.flush()


legal_review.register_target("exception", on_approve=_approve_exception)


# --- notifications and comments ---------------------------------------------------------------------------

def list_notifications(db, *, actor_id, workspace_id, unread=False, current_terms_version=None, limit=100):
    authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version or _terms())
    query = select(LegalNotification).where(LegalNotification.workspace_id == workspace_id,
                                            LegalNotification.recipient_id == actor_id)
    if unread:
        query = query.where(LegalNotification.read_at.is_(None))
    return list(db.scalars(query.order_by(LegalNotification.created_at.desc(), LegalNotification.id).limit(limit)))


def mark_read(db, *, actor_id, workspace_id, notification_id, current_terms_version=None):
    authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version or _terms())
    row = db.scalar(select(LegalNotification).where(LegalNotification.id == notification_id,
        LegalNotification.workspace_id == workspace_id, LegalNotification.recipient_id == actor_id))
    if row is None:
        raise LegalAccessDenied()
    row.read_at = row.read_at or datetime.now(timezone.utc)
    db.flush()
    return row


def _subject_visible(db, user_id, workspace_id, subject_type, subject_id, terms):
    if subject_type == "task":
        _task_for(db, user_id, workspace_id, subject_id, terms)
    elif subject_type == "obligation":
        _obligation_ctx(db, user_id, workspace_id, subject_id, terms)
    elif subject_type == "review":
        legal_review.get(db, workspace_id=workspace_id, review_id=subject_id, actor_id=user_id,
                         current_terms_version=terms)
    elif subject_type == "remediation":
        _remediation(db, user_id, workspace_id, subject_id, terms)
    else:
        raise LegalAccessDenied()


def add_comment(db, *, actor_id, workspace_id, subject_type, subject_id, body, mentions=(), current_terms_version=None):
    """Append-only. Every mentioned recipient must currently be allowed to see the subject."""
    terms = current_terms_version or _terms()
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=terms)
    _subject_visible(db, actor_id, workspace_id, subject_type, subject_id, terms)
    if not body or not body.strip() or "\0" in body or len(body) > 4000 or len(mentions) > 20:
        raise ObligationConflict("comment_invalid")
    for recipient in mentions:
        try:
            _subject_visible(db, recipient, workspace_id, subject_type, subject_id, terms)
        except LegalAccessDenied:
            raise ObligationConflict("mention_recipient_not_authorized")
    row = LegalComment(id=uuid4(), organization_id=ctx.organization_id, workspace_id=workspace_id,
        subject_type=subject_type, subject_id=subject_id, author_id=actor_id, body=body,
        mentions=[str(m) for m in mentions])
    db.add(row)
    db.flush()
    for recipient in mentions:
        notify(db, workspace_id=workspace_id, organization_id=ctx.organization_id, recipient_id=recipient,
               kind="mention", subject_type=subject_type, subject_id=subject_id, dedupe_key=f"mention:{row.id}")
    legal_events.audit_activity(db, ctx, "comment_added", comment_id=str(row.id), subject_type=subject_type,
                                subject_id=str(subject_id), mention_count=len(mentions))
    return row


def list_comments(db, *, actor_id, workspace_id, subject_type, subject_id, current_terms_version=None):
    terms = current_terms_version or _terms()
    authorize_workspace(db, actor_id, workspace_id, current_terms_version=terms)
    _subject_visible(db, actor_id, workspace_id, subject_type, subject_id, terms)
    return list(db.scalars(select(LegalComment).where(LegalComment.workspace_id == workspace_id,
        LegalComment.subject_type == subject_type, LegalComment.subject_id == subject_id)
        .order_by(LegalComment.created_at, LegalComment.id)))
