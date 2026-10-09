"""Transactional legal outbox. emit() joins the caller's transaction; the worker dispatches.

Same key + same payload returns the existing row; same key + changed payload is a conflict.
Handlers run together in one transaction with the dispatched mark, so a commit is exactly-once;
on failure the work rolls back, attempts increase with backoff, then the event dead-letters.
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Callable
from uuid import UUID, uuid4

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.legal_review import LegalEvent
from app.db.models.legal_scope import Workspace

MAX_ATTEMPTS = 5
LEASE = timedelta(minutes=5)


class LegalEventConflict(ValueError):
    pass


_HANDLERS: dict[str, list[Callable]] = {}


def register_handler(event_type: str, handler: Callable[[Session, LegalEvent], None]):
    if handler not in _HANDLERS.setdefault(event_type, []):
        _HANDLERS[event_type].append(handler)


def _digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def emit(db: Session, *, workspace_id: UUID, event_type: str, payload: dict, idempotency_key: str) -> LegalEvent:
    if not 1 <= len(idempotency_key or "") <= 200 or not 1 <= len(event_type or "") <= 80:
        raise LegalEventConflict("event_request_invalid")
    payload = json.loads(json.dumps(payload, default=str, allow_nan=False))
    digest = _digest(payload)
    query = select(LegalEvent).where(LegalEvent.workspace_id == workspace_id, LegalEvent.event_type == event_type,
                                     LegalEvent.idempotency_key == idempotency_key)
    existing = db.scalar(query)
    if existing is None:
        organization_id = db.scalar(select(Workspace.organization_id).where(Workspace.id == workspace_id))
        if organization_id is None:
            raise LegalEventConflict("event_workspace_unknown")
        row = LegalEvent(id=uuid4(), organization_id=organization_id, workspace_id=workspace_id, event_type=event_type,
            idempotency_key=idempotency_key, payload=payload, payload_sha256=digest, status="pending", attempts=0)
        db.add(row)
        try:
            with db.begin_nested():
                db.flush()
            return row
        except IntegrityError:
            existing = db.scalar(query)  # concurrent emitter won the key
    if existing.payload_sha256 != digest:
        raise LegalEventConflict("event_retry_conflict")
    return existing


def audit_activity(db: Session, ctx, action: str, **details):
    """Scoped LEGAL_ACTIVITY_RECORDED audit in the caller's transaction (ctx = LegalContext).
    Pass identifiers/hashes/codes only, never source text or secrets. Failure must roll back the caller."""
    from app.services.audit import append_event
    if not 1 <= len(action) <= 80:
        raise ValueError("action must be 1-80 characters")
    return append_event(db, event_type="LEGAL_ACTIVITY_RECORDED", actor_id=ctx.actor_id, actor_kind="user", payload={
        "policy_version": "legal-activity-v1", "action": action, "organization_id": str(ctx.organization_id),
        "workspace_id": str(ctx.workspace_id), **details})


def _now():
    return datetime.now(timezone.utc)


def dispatch_one(db: Session, *, worker_id: str, now: datetime | None = None) -> LegalEvent | None:
    """Claim and dispatch one due event; returns it (or None when idle). Commits."""
    now = now or _now()
    row = db.scalar(select(LegalEvent).where(LegalEvent.status == "pending",
        or_(LegalEvent.next_attempt_at.is_(None), LegalEvent.next_attempt_at <= now),
        or_(LegalEvent.lease_expires_at.is_(None), LegalEvent.lease_expires_at <= now))
        .order_by(LegalEvent.created_at, LegalEvent.id).limit(1).with_for_update(skip_locked=True))
    if row is None:
        db.rollback()
        return None
    event_id = row.id
    row.lease_owner, row.lease_expires_at = worker_id, now + LEASE
    try:
        for handler in _HANDLERS.get(row.event_type, []):
            handler(db, row)
        row.status, row.dispatched_at, row.lease_owner, row.lease_expires_at = "dispatched", now, None, None
        row.last_error_code = None
        db.commit()
        return row
    except Exception as error:  # handler effects roll back; only the safe error class is kept
        db.rollback()
        row = db.scalar(select(LegalEvent).where(LegalEvent.id == event_id).with_for_update())
        row.attempts += 1
        row.last_error_code = type(error).__name__[:80]
        row.lease_owner, row.lease_expires_at = None, None
        if row.attempts >= MAX_ATTEMPTS:
            row.status = "dead_letter"
        else:
            row.next_attempt_at = now + timedelta(seconds=30 * 2 ** row.attempts)
        db.commit()
        return row


def dispatch_due(db: Session, *, worker_id: str, now: datetime | None = None, limit: int = 100) -> int:
    count = 0
    while count < limit and dispatch_one(db, worker_id=worker_id, now=now) is not None:
        count += 1
    return count
