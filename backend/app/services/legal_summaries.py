"""Extractive, lossless cited summary profiles and approved exports. No model calls."""
from datetime import datetime, timezone
import io
import json
import textwrap
from uuid import UUID, uuid4
from xml.sax.saxutils import escape
import zipfile
from sqlalchemy import select
from app.db.models.legal_contract import ContractSummary, SummarySpan
from app.services import legal_review
from app.services.canonicalization import canonical_hash
from app.services.legal_contracts import ContractConflict, audit, scope, stored_sources, validate_citations
from app.services.legal_policy import LegalAccessDenied, ROLE_OPERATIONS, authorize_workspace


def authorize_target(db, ctx, target_id):
    from app.core.config import settings
    row = db.scalar(select(ContractSummary).where(ContractSummary.id == target_id,
        ContractSummary.workspace_id == ctx.workspace_id, ContractSummary.organization_id == ctx.organization_id))
    if row is None:
        raise LegalAccessDenied()
    citations = [c for s in row.content["statements"] for c in s["citations"]]
    operation = "review_legal" if ctx.role == "legal_reviewer" and ctx.actor_id != row.requester_id else "read"
    validate_citations(db, actor_id=ctx.actor_id, workspace_id=ctx.workspace_id, citations=citations,
        current_terms_version=settings.current_terms_version, operation=operation, requester_id=row.requester_id)


def on_approve(db, review):
    from app.core.config import settings
    row = db.get(ContractSummary, review.target_id)
    if row is None or row.workspace_id != review.workspace_id or row.requester_id != review.requester_id or (
        row.revision_sha256 != review.target_revision_sha256 or canonical_hash(row.content) != row.revision_sha256):
        raise ContractConflict("summary_review_revision_mismatch")
    validate_citations(db, actor_id=row.requester_id, workspace_id=row.workspace_id,
        citations=[c for s in row.content["statements"] for c in s["citations"]],
        current_terms_version=settings.current_terms_version, operation="propose")


legal_review.register_target("summary", authorize=authorize_target, on_approve=on_approve)


def create(db, *, request, actor_id, workspace_id, current_terms_version):
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version)
    if "propose" not in ROLE_OPERATIONS[ctx.role]:
        raise LegalAccessDenied()
    sources, uncertainties = [], ["extractive_summary_not_legal_interpretation"]
    for reference in request.sources:
        artifact, items = stored_sources(db, actor_id=actor_id, workspace_id=workspace_id,
            document_id=reference.document_id, version_id=reference.version_id, current_terms_version=current_terms_version)
        if artifact.status != "ready":
            uncertainties.append("source_requires_verification:" + str(reference.version_id))
        for item in items:
            if str(item["span_id"]) not in {s["span_id"] for s in sources}:
                sources.append(item)
    if len(sources) > 2000 or sum(len(s["quote"]) for s in sources) > 2_000_000:
        raise ContractConflict("summary_source_limit")
    validate_citations(db, actor_id=actor_id, workspace_id=workspace_id, citations=sources,
        current_terms_version=current_terms_version, operation="propose")
    from app.services.legal_contract_analysis import collision_proposals, INJECTION
    if any(INJECTION.search(s["quote"]) for s in sources):
        uncertainties.append("untrusted_document_instructions")
    version_groups = {}
    for source in sources:
        version_groups.setdefault(str(source["version_id"]), []).append(source)
    contradictions = []
    groups = list(version_groups.values())
    for index, group in enumerate(groups):
        for other in groups[index+1:]:
            contradictions.extend(collision_proposals(group, other))
    if contradictions:
        uncertainties.append("cross_document_conflict_requires_review")
    content = {"profile": request.profile, "audience": request.audience,
        "profile_version": "legal-summary-extractive-v1", "schema_version": "legal-summary-v1",
        "prompt_version": "no-model-deterministic-v1", "rule_version": "source-coverage-v1",
        "statements": [{"text": s["quote"].strip(), "category": "source_fact", "citations": [{
            k: str(s[k]) if k != "locator" else s[k] for k in
            ("span_id", "document_id", "version_id", "source_sha256", "extraction_id", "quote", "locator")}]} for s in sources],
        "coverage": {"total_spans": len(sources), "covered_spans": len(sources), "omitted_span_ids": []},
        "uncertainties": sorted(set(uncertainties)), "missing_information": ["Legal applicability and accepted duties require independent review."] +
            (["A second version is required to establish change."] if request.profile == "change" and len(groups) < 2 else []),
        "contradictions": contradictions, "review_required": True}
    digest = canonical_hash(content)
    row = db.scalar(select(ContractSummary).where(ContractSummary.workspace_id == workspace_id,
        ContractSummary.requester_id == actor_id, ContractSummary.revision_sha256 == digest))
    if row is None:
        row = ContractSummary(id=uuid4(), **scope(ctx), requester_id=actor_id, profile=request.profile,
            audience=request.audience, content=content, revision_sha256=digest)
        db.add(row)
        db.flush()
        for source in sources:
            db.add(SummarySpan(id=uuid4(), **scope(ctx), summary_id=row.id,
                extraction_id=UUID(str(source["extraction_id"])), span_id=UUID(source["span_id"])))
        db.flush()
        audit(db, ctx, "summary_proposed", row.id)
    review = legal_review.submit(db, workspace_id=workspace_id, target_type="summary", target_id=row.id,
        target_revision_sha256=digest, requester_id=actor_id, idempotency_key="summary:" + str(row.id),
        current_terms_version=current_terms_version)
    return {"summary_id": row.id, "revision_sha256": digest, "review_id": review.id,
        "outcome": legal_review.status(db, review), **content}


def get(db, *, summary_id, actor_id, workspace_id, current_terms_version):
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version)
    row = db.scalar(select(ContractSummary).where(ContractSummary.id == summary_id,
        ContractSummary.workspace_id == workspace_id, ContractSummary.organization_id == ctx.organization_id))
    if row is None:
        raise LegalAccessDenied()
    validate_citations(db, actor_id=actor_id, workspace_id=workspace_id,
        citations=[c for s in row.content["statements"] for c in s["citations"]], current_terms_version=current_terms_version)
    if canonical_hash(row.content) != row.revision_sha256:
        raise ContractConflict("summary_integrity_failed")
    approved = legal_review.is_approved(db, workspace_id=workspace_id, target_type="summary", target_id=row.id,
        target_revision_sha256=row.revision_sha256)
    return {"summary_id": row.id, "revision_sha256": row.revision_sha256, "outcome": "approved" if approved else "proposed", **row.content}


def list_summaries(db, **kwargs):
    ctx = authorize_workspace(db, kwargs["actor_id"], kwargs["workspace_id"], current_terms_version=kwargs["current_terms_version"])
    items = []
    for row in db.scalars(select(ContractSummary).where(ContractSummary.workspace_id == ctx.workspace_id,
        ContractSummary.organization_id == ctx.organization_id).order_by(ContractSummary.created_at.desc()).limit(200)):
        try:
            items.append(get(db, summary_id=row.id, **kwargs))
        except LegalAccessDenied:
            continue
    return {"items": items}


def export(db, *, summary_id, format, actor_id, workspace_id, current_terms_version):
    result = get(db, summary_id=summary_id, actor_id=actor_id, workspace_id=workspace_id, current_terms_version=current_terms_version)
    if result["outcome"] != "approved":
        raise ContractConflict("summary_not_approved")
    if format not in {"json", "pdf", "docx"}:
        raise ContractConflict("summary_export_format")
    from app.db.models.legal_review import LegalReview, LegalReviewDecision
    review = db.scalar(select(LegalReview).where(LegalReview.workspace_id == workspace_id,
        LegalReview.target_type == "summary", LegalReview.target_id == summary_id,
        LegalReview.target_revision_sha256 == result["revision_sha256"]))
    decision = db.scalar(select(LegalReviewDecision).where(LegalReviewDecision.review_id == review.id,
        LegalReviewDecision.decision == "approve"))
    bundle = {"summary": result, "manifest": {"schema_version": "legal-summary-export-v1",
        "summary_id": str(summary_id), "revision_sha256": result["revision_sha256"],
        "review_id": str(review.id), "decision_id": str(decision.id), "reviewer_id": str(decision.reviewer_id),
        "sources": [c for s in result["statements"] for c in s["citations"]]}}
    encoded = json.dumps(bundle, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    text = ["Approved extractive summary: " + result["profile"] + " / " + result["audience"],
        "Revision: " + result["revision_sha256"], "Review: " + str(review.id)]
    for statement in result["statements"]:
        text += [statement["category"] + ": " + statement["text"], "Sources: " + ", ".join(c["span_id"] for c in statement["citations"])]
    text += ["Uncertainty: " + s for s in result["uncertainties"]] + ["Missing information: " + s for s in result["missing_information"]]
    if format == "json":
        data, mime = encoded, "application/json"
    elif format == "docx":
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="json" ContentType="application/json"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
            archive.writestr("_rels/.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
            archive.writestr("word/document.xml", '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' +
                "".join('<w:p><w:r><w:t xml:space="preserve">' + escape(line) + '</w:t></w:r></w:p>' for line in text) + '</w:body></w:document>')
            archive.writestr("legal/manifest.json", encoded)
        data, mime = buffer.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        import pymupdf
        lines = [part for line in text for part in textwrap.wrap(line, 88, replace_whitespace=False)]
        if len(lines) > 5000:
            raise ContractConflict("summary_pdf_export_limit")
        buffer = io.BytesIO()
        writer = pymupdf.DocumentWriter(buffer)
        story = pymupdf.Story("<html><body>" + "".join("<p>" + escape(line) + "</p>" for line in text) + "</body></html>",
            user_css="body { font-family: sans-serif; font-size: 10pt; } p { margin-bottom: 8pt; }")
        story.write(writer, lambda page_number, filled: (pymupdf.Rect(0, 0, 595, 842), pymupdf.Rect(45, 45, 550, 795), None))
        writer.close()
        with pymupdf.open(stream=buffer.getvalue(), filetype="pdf") as pdf:
            pdf.embfile_add("legal-manifest.json", encoded, filename="legal-manifest.json", desc="Exact approved summary and review/source manifest")
            data, mime = pdf.tobytes(), "application/pdf"
    validate_citations(db, actor_id=actor_id, workspace_id=workspace_id,
        citations=bundle["manifest"]["sources"], current_terms_version=current_terms_version)
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version)
    audit(db, ctx, "summary_exported_" + format, summary_id)
    return data, mime
