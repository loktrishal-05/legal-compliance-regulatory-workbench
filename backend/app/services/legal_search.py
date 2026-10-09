"""Authorized document listing and span search. Eligibility is filtered in SQL BEFORE ranking/paging,
mirroring legal_policy.authorize_document (scope + clearance + read grant + optional matter access),
then every returned document is re-authorized so a grant revoked mid-request never leaks a result.
Responses carry no totals, so counts cannot reveal denied objects.
"""
from uuid import UUID

from sqlalchemy import and_, exists, func, literal, or_, select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentVersion
from app.db.models.legal_extraction import LegalExtraction, LegalSourceSpan
from app.db.models.legal_scope import DocumentAccess, LegalDocumentScope, Matter, MatterAccess
from app.services.legal_policy import CLASSIFICATIONS, LegalAccessDenied, LegalContext, authorize_document

MAX_QUERY = 200


def _terms():
    from app.core.config import settings
    return settings.current_terms_version


def readable_documents(ctx: LegalContext):
    """Subquery of document IDs the actor may read right now in ctx's workspace."""
    levels = [name for name, level in CLASSIFICATIONS.items() if level <= CLASSIFICATIONS[ctx.clearance]]
    matter_ok = or_(LegalDocumentScope.matter_id.is_(None), exists().where(
        Matter.id == LegalDocumentScope.matter_id, Matter.workspace_id == ctx.workspace_id,
        Matter.organization_id == ctx.organization_id, Matter.is_active.is_(True),
        MatterAccess.matter_id == Matter.id, MatterAccess.workspace_id == Matter.workspace_id,
        MatterAccess.organization_id == Matter.organization_id, MatterAccess.user_id == ctx.actor_id,
        MatterAccess.is_active.is_(True)))
    return select(LegalDocumentScope.document_id).where(
        LegalDocumentScope.workspace_id == ctx.workspace_id, LegalDocumentScope.organization_id == ctx.organization_id,
        LegalDocumentScope.is_active.is_(True), LegalDocumentScope.classification.in_(levels),
        exists().where(DocumentAccess.document_id == LegalDocumentScope.document_id,
                       DocumentAccess.workspace_id == ctx.workspace_id,
                       DocumentAccess.organization_id == ctx.organization_id,
                       DocumentAccess.user_id == ctx.actor_id, DocumentAccess.operation == "read",
                       DocumentAccess.is_active.is_(True)),
        matter_ok)


def _still_readable(db, ctx, document_ids, terms):
    allowed = set()
    for document_id in set(document_ids):
        try:
            authorize_document(db, ctx.actor_id, ctx.workspace_id, document_id, current_terms_version=terms)
            allowed.add(document_id)
        except LegalAccessDenied:
            pass
    return allowed


def list_documents(db: Session, ctx: LegalContext, *, limit: int = 50, offset: int = 0, matter_id: UUID | None = None,
                   classification: str | None = None, status: str | None = None, filename: str | None = None,
                   current_terms_version: str | None = None) -> list[dict]:
    query = (select(Document.id, Document.filename, Document.document_type, Document.ingestion_status,
                    LegalDocumentScope.matter_id, LegalDocumentScope.classification, LegalDocumentScope.legal_hold,
                    Document.created_at)
             .join(LegalDocumentScope, LegalDocumentScope.document_id == Document.id)
             .where(Document.id.in_(readable_documents(ctx)), LegalDocumentScope.workspace_id == ctx.workspace_id))
    if matter_id:
        query = query.where(LegalDocumentScope.matter_id == matter_id)
    if classification:
        query = query.where(LegalDocumentScope.classification == classification)
    if status:
        query = query.where(Document.ingestion_status == status)
    if filename:
        escaped = filename.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.where(Document.filename.ilike(f"%{escaped}%", escape="\\"))
    rows = db.execute(query.order_by(Document.created_at.desc(), Document.id).limit(limit).offset(offset)).all()
    allowed = _still_readable(db, ctx, [row.id for row in rows], current_terms_version or _terms())
    return [{"document_id": row.id, **{k: v for k, v in row._mapping.items() if k != "id"}}
            for row in rows if row.id in allowed]


def search_spans(db: Session, ctx: LegalContext, q: str, limit: int = 20, *,
                 current_terms_version: str | None = None) -> list[dict]:
    """Public contract for the assistant (agent B): authorized full-text search over stored spans.

    PostgreSQL ranks with to_tsvector/plainto_tsquery; other dialects fall back to substring match.
    Only spans of currently readable, non-quarantined versions in ctx's workspace are eligible.
    Each row: span_id, locator, extraction_id, document_id, version_id, source_sha256, extraction_status, quote, rank.
    """
    q = (q or "").strip()
    if not q or len(q) > MAX_QUERY or "\0" in q:
        return []
    limit = max(1, min(limit, 50))
    quote = func.substr(LegalExtraction.text, LegalSourceSpan.start + 1, LegalSourceSpan.end - LegalSourceSpan.start)
    if db.get_bind().dialect.name == "postgresql":
        vector, query = func.to_tsvector("simple", quote), func.plainto_tsquery("simple", q)
        match, rank = vector.op("@@")(query), func.ts_rank(vector, query)
    else:  # ponytail: substring fallback for SQLite tests; dense/hybrid Qdrant path is an open gate
        match, rank = func.lower(quote).contains(q.lower()), literal(1.0)
    rows = db.execute(select(LegalSourceSpan.id.label("span_id"), LegalSourceSpan.locator, LegalExtraction.id.label(
        "extraction_id"), LegalExtraction.document_id, LegalExtraction.version_id, LegalExtraction.source_sha256,
        LegalExtraction.status.label("extraction_status"), quote.label("quote"), rank.label("rank"))
        .join(LegalExtraction, and_(LegalExtraction.id == LegalSourceSpan.extraction_id,
                                    LegalExtraction.workspace_id == LegalSourceSpan.workspace_id))
        .join(DocumentVersion, and_(DocumentVersion.id == LegalExtraction.version_id,
                                    DocumentVersion.workspace_id == ctx.workspace_id))
        .where(LegalSourceSpan.workspace_id == ctx.workspace_id, LegalExtraction.organization_id == ctx.organization_id,
               LegalExtraction.document_id.in_(readable_documents(ctx)), DocumentVersion.status != "quarantined",
               match)
        .order_by(rank.desc(), LegalSourceSpan.id).limit(limit)).all()  # ponytail: no FTS index; add GIN on span text at scale
    allowed = _still_readable(db, ctx, [row.document_id for row in rows], current_terms_version or _terms())
    return [dict(row._mapping) for row in rows if row.document_id in allowed]
