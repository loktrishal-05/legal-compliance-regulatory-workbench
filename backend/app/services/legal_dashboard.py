"""Permission-filtered workspace dashboard aggregates. Every count is computed only over objects the caller
may currently read (same checks as the item APIs), so totals never reveal denied objects."""
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.db.models import Document
from app.db.models.legal_jobs import LegalJob
from app.db.models.legal_obligations import LegalDeadlineOccurrence
from app.db.models.legal_review import LegalReview
from app.services import legal_obligations as ob
from app.services import legal_review
from app.services.legal_policy import LegalAccessDenied, authorize_workspace
from app.services.legal_search import readable_documents

SIX = ("satisfied", "partially_satisfied", "unsatisfied", "insufficient_evidence", "not_applicable", "needs_review")


def _aware(value):
    return value if value is None or value.tzinfo else value.replace(tzinfo=timezone.utc)


def _visible(fn):
    try:
        fn()
        return True
    except LegalAccessDenied:
        return False


def dashboard(db, *, actor_id, workspace_id, current_terms_version, now=None) -> dict:
    now = now or datetime.now(timezone.utc)
    terms = current_terms_version
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=terms)
    readable = readable_documents(ctx)
    documents = dict(db.execute(select(Document.ingestion_status, func.count()).where(Document.id.in_(readable))
                                .group_by(Document.ingestion_status)).all())
    jobs = dict(db.execute(select(LegalJob.state, func.count()).where(LegalJob.workspace_id == workspace_id,
        LegalJob.document_id.in_(readable)).group_by(LegalJob.state)).all())
    reviews = Counter()
    for review in db.scalars(select(LegalReview).where(LegalReview.workspace_id == workspace_id)):
        if _visible(lambda r=review: legal_review.get(db, workspace_id=workspace_id, review_id=r.id, actor_id=actor_id,
                                                      current_terms_version=terms)):
            if legal_review.status(db, review) in ("pending", "escalated"):
                reviews[review.target_type] += 1
    tasks = Counter(task.status for task in ob.list_tasks(db, actor_id=actor_id, workspace_id=workspace_id,
                                                          current_terms_version=terms, limit=10_000))
    weeks = [0] * 8
    overdue = 0
    obligation_ids = [row.id for row in ob.list_obligations(db, actor_id=actor_id, workspace_id=workspace_id,
                                                             current_terms_version=terms, limit=10_000)]
    if obligation_ids:
        for occurrence in db.scalars(select(LegalDeadlineOccurrence).where(
                LegalDeadlineOccurrence.obligation_id.in_(obligation_ids),
                LegalDeadlineOccurrence.status == "scheduled")):
            due = _aware(occurrence.due_at)
            if due < now:
                overdue += 1
            elif due < now + timedelta(weeks=8):
                weeks[int((due - now).days // 7)] += 1
    out = {"workspace_id": str(workspace_id), "generated_at": now.isoformat(),
           "documents_by_status": documents, "jobs_by_state": jobs,
           "reviews_pending_by_target": dict(reviews), "tasks_by_status": dict(tasks),
           "obligations_due": {"weeks": [{"week_start": (now + timedelta(weeks=i)).date().isoformat(), "count": c}
                                         for i, c in enumerate(weeks)], "overdue": overdue}}
    out.update(_compliance(db, ctx, terms, now))
    out.update(_regulatory(db, ctx, now))
    return out


def _compliance(db, ctx, terms, now):
    from app.db.models import legal_compliance as cm
    from app.services import legal_compliance as compliance
    from app.services import legal_regulatory as regulatory

    def readable(model):
        return [row for row in db.scalars(select(model).where(model.workspace_id == ctx.workspace_id,
                                                              model.organization_id == ctx.organization_id))
                if _visible(lambda r=row: compliance.get(db, model, ctx, r.id, terms))]
    states = Counter({state: 0 for state in SIX})
    stale = 0
    for assessment in readable(cm.Assessment):
        states[assessment.status] += 1
        stale += bool(db.scalar(select(cm.Reevaluation.id).where(cm.Reevaluation.assessment_id == assessment.id).limit(1)))
    findings = Counter("approved" if regulatory.approved(db, row, "compliance_finding") else "pending_review"
                       for row in readable(cm.ComplianceFinding))
    expiry = {"expired": 0, "30": 0, "60": 0, "90": 0}
    for version in readable(cm.EvidenceVersion):
        expires = _aware(version.expires_at)
        if expires is None:
            continue
        days = (expires - now).total_seconds() / 86400
        key = "expired" if days < 0 else "30" if days <= 30 else "60" if days <= 60 else "90" if days <= 90 else None
        if key:
            expiry[key] += 1
    return {"assessments_by_state": dict(states), "assessments_stale": stale, "findings_by_status": dict(findings),
            "evidence_expiring": expiry}


def _regulatory(db, ctx, now):
    from app.db.models.legal_regulatory import RegulatorySource, RegulatoryWatchlist
    from app.services.legal_regulatory_projection import monitoring_status
    freshness = Counter()
    for watch, source in db.execute(select(RegulatoryWatchlist, RegulatorySource).join(
            RegulatorySource, RegulatorySource.id == RegulatoryWatchlist.source_id).where(
            RegulatoryWatchlist.workspace_id == ctx.workspace_id,
            RegulatoryWatchlist.organization_id == ctx.organization_id)):
        freshness[monitoring_status(now, watch.max_age_days, source.last_success_at, source.last_failure_at)["freshness"]] += 1
    return {"regulatory_sources_by_freshness": dict(freshness)}
