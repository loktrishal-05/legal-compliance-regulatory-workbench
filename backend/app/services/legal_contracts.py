"""Contract analysis over authorized stored spans. Caller owns commit/rollback."""
from uuid import UUID, uuid4

from sqlalchemy import select

from app.db.models import DocumentVersion
from app.db.models.legal_contract import (Contract, ContractVersion, ContractAnalysis, ContractClause,
    ContractClauseSpan, ContractParty, ContractFact, ContractFinding, ObligationProposal)
from app.db.models.legal_extraction import LegalExtraction, LegalSourceSpan
from app.services.audit import append_event
from app.services.canonicalization import canonical_hash
from app.services.legal_contract_analysis import analyze_sources
from app.services.legal_extraction import ExtractionBlocked, resolve_span
from app.services.legal_policy import LegalAccessDenied, authorize_document, authorize_workspace

AUDIT_EVENT = "LEGAL_ACTIVITY_RECORDED"


class ContractConflict(ValueError):
    pass


def audit(db, ctx, kind, target_id):
    append_event(db, event_type=AUDIT_EVENT, actor_id=ctx.actor_id, actor_kind="user",
        payload={"workspace_id": str(ctx.workspace_id), "organization_id": str(ctx.organization_id),
                 "kind": kind, "target_id": str(target_id), "policy_version": "legal-contract-v1"})


def scope(ctx):
    return {"organization_id": ctx.organization_id, "workspace_id": ctx.workspace_id}


def version_source(db, *, actor_id, workspace_id, document_id, version_id, current_terms_version, operation="read"):
    ctx = authorize_document(db, actor_id, workspace_id, document_id,
        current_terms_version=current_terms_version, operation=operation)
    row = db.scalar(select(DocumentVersion).where(DocumentVersion.id == version_id,
        DocumentVersion.document_id == document_id, DocumentVersion.workspace_id == workspace_id,
        DocumentVersion.organization_id == ctx.organization_id).with_for_update()
        .execution_options(populate_existing=True))
    if row is None:
        raise LegalAccessDenied()
    if row.status == "quarantined" or row.ingestion_metadata.get("quarantine_reasons"):
        raise ExtractionBlocked("document_quarantined")
    return ctx, row


def create_contract(db, *, actor_id, workspace_id, document_id, version_id, title, current_terms_version):
    if not isinstance(title, str) or not title.strip() or len(title) > 200 or "\0" in title:
        raise ValueError("invalid_contract_title")
    ctx, source = version_source(db, actor_id=actor_id, workspace_id=workspace_id, document_id=document_id,
        version_id=version_id, current_terms_version=current_terms_version, operation="propose")
    contract = db.scalar(select(Contract).where(Contract.workspace_id == workspace_id, Contract.document_id == document_id))
    if contract is None:
        contract = Contract(id=uuid4(), **scope(ctx), document_id=document_id, title=title, requester_id=actor_id)
        db.add(contract)
        db.flush()
    elif contract.title != title:
        raise ContractConflict("contract_title_conflict")
    version = db.scalar(select(ContractVersion).where(ContractVersion.contract_id == contract.id,
        ContractVersion.version_id == version_id))
    if version is None:
        version = ContractVersion(id=uuid4(), **scope(ctx), contract_id=contract.id, document_id=document_id,
            version_id=version_id, source_sha256=source.source_sha256)
        db.add(version)
        db.flush()
        audit(db, ctx, "contract_version_created", version.id)
    authorize_document(db, actor_id, workspace_id, document_id, current_terms_version=current_terms_version, operation="propose")
    return {"contract_id": contract.id, "contract_version_id": version.id, "document_id": document_id,
            "version_id": version_id, "title": contract.title, "source_sha256": source.source_sha256}


def load_version(db, *, actor_id, workspace_id, contract_id, version_id, current_terms_version, operation="read"):
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version)
    row = db.execute(select(Contract, ContractVersion).join(ContractVersion, ContractVersion.contract_id == Contract.id)
        .where(Contract.id == contract_id, ContractVersion.id == version_id, Contract.workspace_id == workspace_id,
            Contract.organization_id == ctx.organization_id, ContractVersion.workspace_id == workspace_id,
            ContractVersion.organization_id == ctx.organization_id)).one_or_none()
    if row is None:
        raise LegalAccessDenied()
    contract, version = row
    ctx, source = version_source(db, actor_id=actor_id, workspace_id=workspace_id, document_id=version.document_id,
        version_id=version.version_id, current_terms_version=current_terms_version, operation=operation)
    if source.source_sha256 != version.source_sha256:
        raise ContractConflict("contract_source_mismatch")
    return ctx, contract, version


def stored_sources(db, *, actor_id, workspace_id, document_id, version_id, current_terms_version, extraction_id=None):
    ctx, version = version_source(db, actor_id=actor_id, workspace_id=workspace_id, document_id=document_id,
        version_id=version_id, current_terms_version=current_terms_version)
    query = select(LegalExtraction).where(LegalExtraction.version_id == version_id,
        LegalExtraction.document_id == document_id, LegalExtraction.workspace_id == workspace_id,
        LegalExtraction.organization_id == ctx.organization_id)
    if extraction_id is not None:
        query = query.where(LegalExtraction.id == extraction_id)
    artifact = db.scalar(query.order_by(LegalExtraction.created_at.desc(), LegalExtraction.id.desc()))
    if artifact is None:
        raise ExtractionBlocked("contract_extraction_required")
    if artifact.source_sha256 != version.source_sha256:
        raise ContractConflict("contract_source_mismatch")
    spans = list(db.scalars(select(LegalSourceSpan).where(LegalSourceSpan.extraction_id == artifact.id).order_by(LegalSourceSpan.start)))
    if not spans:
        raise ExtractionBlocked("contract_source_empty")
    sources = [resolve_span(db, actor_id=actor_id, workspace_id=workspace_id, document_id=document_id,
        version_id=version_id, span_id=s.id, current_terms_version=current_terms_version) for s in spans]
    return artifact, [{**s, "span_id": str(s["span_id"])} for s in sources]


def analysis_response(db, row, *, actor_id, workspace_id, current_terms_version):
    result = dict(row.result)
    result.update(analysis_id=row.id, revision_sha256=row.revision_sha256, contract_version_id=row.contract_version_id)
    result["clauses"] = [{"clause_id": c.id, **c.payload} for c in db.scalars(select(ContractClause)
        .where(ContractClause.analysis_id == row.id).order_by(ContractClause.ordinal))]
    for key, model, identifier in (("findings", ContractFinding, "finding_id"), ("obligations", ObligationProposal, "proposal_id")):
        result[key] = []
        for r in db.scalars(select(model).where(model.analysis_id == row.id).order_by(model.created_at, model.id)):
            try:
                validate_citations(db, actor_id=actor_id, workspace_id=workspace_id,
                    citations=r.payload["citations"], current_terms_version=current_terms_version)
            except LegalAccessDenied:
                continue
            result[key].append({identifier: r.id, "revision_sha256": r.revision_sha256,
                "outcome": proposal_outcome(db, r, "contract_finding" if key == "findings" else "contract_obligation"), **r.payload})
    return result


def analyze(db, *, actor_id, workspace_id, contract_id, version_id, current_terms_version, playbook_id=None, extraction_id=None):
    ctx, contract, version = load_version(db, actor_id=actor_id, workspace_id=workspace_id, contract_id=contract_id,
        version_id=version_id, current_terms_version=current_terms_version, operation="propose")
    artifact, sources = stored_sources(db, actor_id=actor_id, workspace_id=workspace_id, document_id=version.document_id,
        version_id=version.version_id, current_terms_version=current_terms_version, extraction_id=extraction_id)
    rules = []
    if playbook_id:
        from app.services.legal_playbooks import approved_rules
        rules = approved_rules(db, actor_id=actor_id, workspace_id=workspace_id, playbook_id=playbook_id,
            current_terms_version=current_terms_version)
    parsed = analyze_sources(sources, playbook_rules=rules, quality=artifact.status)
    digest = canonical_hash({"extraction": str(artifact.id), "artifact": artifact.artifact_sha256,
        "playbook_id": str(playbook_id) if playbook_id else None, "result": parsed})
    existing = db.scalar(select(ContractAnalysis).where(ContractAnalysis.contract_version_id == version.id,
        ContractAnalysis.workspace_id == workspace_id, ContractAnalysis.revision_sha256 == digest))
    if existing:
        return analysis_response(db, existing, actor_id=actor_id, workspace_id=workspace_id, current_terms_version=current_terms_version)
    row = ContractAnalysis(id=uuid4(), **scope(ctx), contract_version_id=version.id, extraction_id=artifact.id,
        requester_id=actor_id, profile_version=parsed["profile_version"], schema_version=parsed["schema_version"],
        prompt_version=parsed["prompt_version"], rule_version=parsed["rule_version"], revision_sha256=digest, result=parsed)
    db.add(row)
    db.flush()
    for item in parsed["clauses"]:
        clause = ContractClause(id=uuid4(), **scope(ctx), analysis_id=row.id, extraction_id=artifact.id,
            ordinal=item["ordinal"], clause_type=item["clause_type"], payload=item)
        db.add(clause)
        db.flush()
        for citation in item["citations"]:
            db.add(ContractClauseSpan(id=uuid4(), **scope(ctx), clause_id=clause.id, extraction_id=artifact.id,
                span_id=UUID(citation["span_id"])))
    for item in parsed["parties"]:
        db.add(ContractParty(id=uuid4(), **scope(ctx), analysis_id=row.id, name=item["name"], payload=item))
    for item in parsed["facts"]:
        db.add(ContractFact(id=uuid4(), **scope(ctx), analysis_id=row.id, kind=item["kind"], payload=item))
    for key, model in (("findings", ContractFinding), ("obligations", ObligationProposal)):
        for item in parsed[key]:
            db.add(model(id=uuid4(), **scope(ctx), analysis_id=row.id, requester_id=actor_id,
                revision_sha256=canonical_hash({"analysis": digest, "proposal": item}), payload=item))
    db.flush()
    authorize_document(db, actor_id, workspace_id, version.document_id, current_terms_version=current_terms_version, operation="propose")
    audit(db, ctx, "contract_analysis_proposed", row.id)
    return analysis_response(db, row, actor_id=actor_id, workspace_id=workspace_id, current_terms_version=current_terms_version)


def list_contracts(db, *, actor_id, workspace_id, current_terms_version):
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version)
    items = []
    for contract in db.scalars(select(Contract).where(Contract.workspace_id == workspace_id,
        Contract.organization_id == ctx.organization_id).order_by(Contract.created_at, Contract.id).limit(200)):
        try:
            authorize_document(db, actor_id, workspace_id, contract.document_id, current_terms_version=current_terms_version)
        except LegalAccessDenied:
            continue
        versions = []
        for v in db.scalars(select(ContractVersion).where(ContractVersion.contract_id == contract.id)):
            try:
                authorize_document(db, actor_id, workspace_id, v.document_id, current_terms_version=current_terms_version)
            except LegalAccessDenied:
                continue
            versions.append({"contract_version_id": v.id, "document_id": v.document_id,
                "version_id": v.version_id, "source_sha256": v.source_sha256})
        items.append({"contract_id": contract.id, "document_id": contract.document_id, "title": contract.title, "versions": versions})
    return {"items": items}


def proposal_outcome(db, row, target_type):
    from app.services import legal_review
    from app.db.models.legal_review import LegalReview
    review = db.scalar(select(LegalReview).where(LegalReview.workspace_id == row.workspace_id,
        LegalReview.target_type == target_type, LegalReview.target_id == row.id,
        LegalReview.target_revision_sha256 == row.revision_sha256))
    return legal_review.status(db, review) if review else "proposed"


def proposal_source(db, target_type, target_id, workspace_id):
    model = {"contract_finding": ContractFinding, "contract_obligation": ObligationProposal}.get(target_type)
    if model is None:
        raise ContractConflict("contract_target_invalid")
    row = db.scalar(select(model).where(model.id == target_id, model.workspace_id == workspace_id))
    if row is None:
        raise LegalAccessDenied()
    analysis = db.get(ContractAnalysis, row.analysis_id)
    version = db.get(ContractVersion, analysis.contract_version_id)
    return row, analysis, version


def validate_citations(db, *, actor_id, workspace_id, citations, current_terms_version, operation="read", requester_id=None):
    if not citations:
        raise ContractConflict("contract_citations_required")
    for citation in citations:
        document_id, version_id, span_id = (UUID(str(citation[k])) for k in ("document_id", "version_id", "span_id"))
        authorize_document(db, actor_id, workspace_id, document_id, current_terms_version=current_terms_version,
            operation=operation, requester_id=requester_id)
        version_source(db, actor_id=actor_id, workspace_id=workspace_id, document_id=document_id,
            version_id=version_id, current_terms_version=current_terms_version)
        source = resolve_span(db, actor_id=actor_id, workspace_id=workspace_id, document_id=document_id,
            version_id=version_id, span_id=span_id, current_terms_version=current_terms_version)
        if citation["quote"] != source["quote"] or citation.get("source_sha256") != source["source_sha256"]:
            raise ContractConflict("contract_citation_mismatch")


def authorize_proposal(db, ctx, target_id, target_type):
    from app.core.config import settings
    row, analysis, version = proposal_source(db, target_type, target_id, ctx.workspace_id)
    if row.organization_id != ctx.organization_id:
        raise LegalAccessDenied()
    operation = "review_legal" if ctx.role == "legal_reviewer" and ctx.actor_id != row.requester_id else "read"
    validate_citations(db, actor_id=ctx.actor_id, workspace_id=ctx.workspace_id, citations=row.payload["citations"],
        current_terms_version=settings.current_terms_version, operation=operation, requester_id=row.requester_id)


def approve_proposal(db, review):
    from app.services import legal_events
    row, analysis, version = proposal_source(db, review.target_type, review.target_id, review.workspace_id)
    if row.revision_sha256 != review.target_revision_sha256 or row.requester_id != review.requester_id:
        raise ContractConflict("contract_review_revision_mismatch")
    if review.target_type == "contract_obligation":
        legal_events.emit(db, workspace_id=review.workspace_id, event_type="legal.contract.obligation_accepted",
            idempotency_key="contract-obligation:" + str(row.id), payload={"proposal_id": str(row.id),
                "proposal_sha256": row.revision_sha256, "review_id": str(review.id), "requester_id": str(row.requester_id),
                "document_id": str(version.document_id), "version_id": str(version.version_id),
                "source_sha256": version.source_sha256, **row.payload})


def submit_proposal(db, *, actor_id, workspace_id, current_terms_version, target_type, target_id):
    from app.services import legal_review
    row, analysis, version = proposal_source(db, target_type, target_id, workspace_id)
    if row.requester_id != actor_id:
        raise LegalAccessDenied()
    authorize_document(db, actor_id, workspace_id, version.document_id, current_terms_version=current_terms_version, operation="propose")
    return legal_review.submit(db, workspace_id=workspace_id, target_type=target_type, target_id=row.id,
        target_revision_sha256=row.revision_sha256, requester_id=actor_id,
        idempotency_key=target_type + ":" + str(row.id), current_terms_version=current_terms_version)


from app.services import legal_review
for _kind in ("contract_finding", "contract_obligation"):
    legal_review.register_target(_kind, on_approve=approve_proposal,
        authorize=lambda db, ctx, tid, kind=_kind: authorize_proposal(db, ctx, tid, kind))


def get_analysis(db, *, actor_id, workspace_id, contract_id, version_id, current_terms_version):
    ctx, contract, version = load_version(db, actor_id=actor_id, workspace_id=workspace_id, contract_id=contract_id,
        version_id=version_id, current_terms_version=current_terms_version)
    row = db.scalar(select(ContractAnalysis).where(ContractAnalysis.contract_version_id == version.id,
        ContractAnalysis.workspace_id == workspace_id).order_by(ContractAnalysis.created_at.desc(), ContractAnalysis.id.desc()))
    if row is None:
        raise ExtractionBlocked("contract_analysis_required")
    result = analysis_response(db, row, actor_id=actor_id, workspace_id=workspace_id, current_terms_version=current_terms_version)
    validate_citations(db, actor_id=actor_id, workspace_id=workspace_id,
        citations=[c for clause in result["clauses"] for c in clause["citations"]], current_terms_version=current_terms_version)
    return result


def list_related(db, *, actor_id, workspace_id, current_terms_version, kind, analysis_id=None):
    from app.services.legal_search import readable_documents
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version)
    model = {"clauses": ContractClause, "contract-findings": ContractFinding, "obligation-proposals": ObligationProposal}[kind]
    query = select(model).join(ContractAnalysis, ContractAnalysis.id == model.analysis_id).join(ContractVersion,
        ContractVersion.id == ContractAnalysis.contract_version_id).where(model.workspace_id == workspace_id,
        model.organization_id == ctx.organization_id, ContractVersion.document_id.in_(readable_documents(ctx)))
    if analysis_id:
        query = query.where(model.analysis_id == analysis_id)
    items = []
    for row in db.scalars(query.order_by(model.created_at, model.id).limit(200)):
        try:
            validate_citations(db, actor_id=actor_id, workspace_id=workspace_id, citations=row.payload["citations"],
                current_terms_version=current_terms_version)
        except LegalAccessDenied:
            continue
        item = {"id": row.id, "analysis_id": row.analysis_id, **row.payload}
        if kind != "clauses":
            item.update(revision_sha256=row.revision_sha256, outcome=proposal_outcome(db, row,
                "contract_finding" if kind == "contract-findings" else "contract_obligation"))
        items.append(item)
    return {"items": items}


def redline(db, *, actor_id, workspace_id, contract_id, from_version_id, to_version_id, current_terms_version):
    from app.services.legal_contract_analysis import compare_sources
    groups = []
    for version_id in (from_version_id, to_version_id):
        ctx, contract, version = load_version(db, actor_id=actor_id, workspace_id=workspace_id, contract_id=contract_id,
            version_id=version_id, current_terms_version=current_terms_version)
        artifact, items = stored_sources(db, actor_id=actor_id, workspace_id=workspace_id, document_id=version.document_id,
            version_id=version.version_id, current_terms_version=current_terms_version)
        groups.append([{k: str(v) if isinstance(v, UUID) else v for k,v in s.items()} for s in items])
    return compare_sources(*groups)


def propose_collisions(db, *, request, actor_id, workspace_id, current_terms_version):
    from app.services.legal_contract_analysis import collision_proposals
    groups, left = [], None
    for cid, vid in ((request.left_contract_id, request.left_version_id), (request.right_contract_id, request.right_version_id)):
        ctx, contract, version = load_version(db, actor_id=actor_id, workspace_id=workspace_id, contract_id=cid,
            version_id=vid, current_terms_version=current_terms_version, operation="propose")
        result = analyze(db, actor_id=actor_id, workspace_id=workspace_id, contract_id=cid,
            version_id=vid, current_terms_version=current_terms_version)
        left = left or result["analysis_id"]
        artifact, items = stored_sources(db, actor_id=actor_id, workspace_id=workspace_id, document_id=version.document_id,
            version_id=version.version_id, current_terms_version=current_terms_version)
        groups.append(items)
    ids = []
    for payload in collision_proposals(*groups):
        digest = canonical_hash({"analysis": str(left), "collision": payload})
        row = db.scalar(select(ContractFinding).where(ContractFinding.analysis_id == left,
            ContractFinding.workspace_id == workspace_id, ContractFinding.revision_sha256 == digest))
        if row is None:
            row = ContractFinding(id=uuid4(), **scope(ctx), analysis_id=left, requester_id=actor_id,
                revision_sha256=digest, payload=payload)
            db.add(row)
            db.flush()
            audit(db, ctx, "contract_collision_proposed", row.id)
        ids.append(row.id)
    return {"finding_ids": ids, "status": "needs_review"}


def handle_document_extracted(db, event):
    from app.db.models import Document
    from app.core.config import settings
    from app.services import legal_events
    data = event.payload
    document = db.scalar(select(Document).where(Document.id == UUID(data["document_id"])))
    if document is None or document.document_type != "contract":
        return
    actor_id = UUID(data["actor_id"])
    existing = db.scalar(select(Contract).where(Contract.document_id == document.id, Contract.workspace_id == event.workspace_id))
    result = create_contract(db, actor_id=actor_id, workspace_id=event.workspace_id,
        document_id=document.id, version_id=UUID(data["version_id"]), title=existing.title if existing else document.filename,
        current_terms_version=settings.current_terms_version)
    legal_events.emit(db, workspace_id=event.workspace_id, event_type="legal.contract.analysis_requested",
        idempotency_key="analysis:" + data["extraction_id"], payload={"actor_id": str(actor_id),
            "contract_id": str(result["contract_id"]), "contract_version_id": str(result["contract_version_id"]),
            "extraction_id": data["extraction_id"]})


def handle_analysis_requested(db, event):
    from app.core.config import settings
    data = event.payload
    analyze(db, actor_id=UUID(data["actor_id"]), workspace_id=event.workspace_id,
        contract_id=UUID(data["contract_id"]), version_id=UUID(data["contract_version_id"]),
        extraction_id=UUID(data["extraction_id"]), current_terms_version=settings.current_terms_version)


from app.services import legal_events
legal_events.register_handler("legal.document.extracted", handle_document_extracted)
legal_events.register_handler("legal.contract.analysis_requested", handle_analysis_requested)


def add_version(db, *, contract_id, document_id, version_id, actor_id, workspace_id, current_terms_version):
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version)
    contract = db.scalar(select(Contract).where(Contract.id == contract_id, Contract.workspace_id == workspace_id,
        Contract.organization_id == ctx.organization_id).with_for_update())
    if contract is None:
        raise LegalAccessDenied()
    authorize_document(db, actor_id, workspace_id, contract.document_id, current_terms_version=current_terms_version, operation="propose")
    ctx, source = version_source(db, actor_id=actor_id, workspace_id=workspace_id, document_id=document_id,
        version_id=version_id, current_terms_version=current_terms_version, operation="propose")
    row = db.scalar(select(ContractVersion).where(ContractVersion.contract_id == contract_id,
        ContractVersion.version_id == version_id, ContractVersion.workspace_id == workspace_id))
    if row is None:
        row = ContractVersion(id=uuid4(), **scope(ctx), contract_id=contract_id, document_id=document_id,
            version_id=version_id, source_sha256=source.source_sha256)
        db.add(row)
        db.flush()
        audit(db, ctx, "contract_version_attached", row.id)
    return {"contract_id": contract_id, "contract_version_id": row.id, "document_id": document_id,
        "version_id": version_id, "source_sha256": row.source_sha256}
