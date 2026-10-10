"""Durable periodic legal scans with last-run receipts. Scans must be idempotent (unique receipt keys).

A scan claims its receipt row with SKIP LOCKED so concurrent workers never run it twice at once;
each scan commits independently, so one failing scan does not block the others.
"""
from datetime import datetime, timedelta, timezone
from typing import Callable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.legal_review import LegalSchedulerScan

_SCANS: dict[str, Callable[[Session, datetime], int]] = {}
MIN_INTERVAL = timedelta(seconds=60)


def register_scan(name: str, fn: Callable[[Session, datetime], int]):
    if not 1 <= len(name) <= 80:
        raise ValueError("Scan name must be 1-80 characters")
    _SCANS[name] = fn


def _claim(db, name, now, force):
    if db.get(LegalSchedulerScan, name) is None:  # receipt row commits first so a failing scan keeps its record
        try:
            db.add(LegalSchedulerScan(name=name, runs=0, last_count=0))
            db.commit()
        except IntegrityError:
            db.rollback()
    row = db.scalar(select(LegalSchedulerScan).where(LegalSchedulerScan.name == name)
                    .with_for_update(skip_locked=True).execution_options(populate_existing=True))
    if row is None:
        return None  # another worker holds it
    started = row.last_started_at
    if started is not None and started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)  # SQLite returns naive UTC
    if not force and started is not None and now - started < MIN_INTERVAL:
        return None
    return row


def run_due(db: Session, now: datetime | None = None, *, force: bool = False) -> dict[str, int | str]:
    """Run each registered scan at most once per interval; returns {name: count | 'error:<code>'}."""
    now = now or datetime.now(timezone.utc)
    results = {}
    for name, fn in list(_SCANS.items()):
        row = _claim(db, name, now, force)
        if row is None:
            db.rollback()
            continue
        try:
            count = int(fn(db, now))
            row.last_started_at, row.last_success_at, row.last_count = now, now, count
            row.last_error_code, row.runs = None, row.runs + 1
            db.commit()
            results[name] = count
        except Exception as error:
            db.rollback()
            row = db.get(LegalSchedulerScan, name)
            row.last_started_at, row.last_error_code, row.runs = now, type(error).__name__[:80], row.runs + 1
            db.commit()
            results[name] = "error:" + row.last_error_code
    return results
