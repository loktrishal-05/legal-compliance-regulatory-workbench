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
            Contract.organization_id == ctx.organization_id, ContractVersion.document_id == Contract.document_id)).one_or_none()
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


def analysis_response(db, row):
    result = dict(row.result)
    result.update(analysis_id=row.id, revision_sha256=row.revision_sha256, contract_version_id=row.contract_version_id)
    result["clauses"] = [{"clause_id": c.id, **c.payload} for c in db.scalars(select(ContractClause)
        .where(ContractClause.analysis_id == row.id).order_by(ContractClause.ordinal))]
    for key, model, identifier in (("findings", ContractFinding, "finding_id"), ("obligations", ObligationProposal, "proposal_id")):
        result[key] = [{identifier: r.id, "revision_sha256": r.revision_sha256, "outcome": "proposed", **r.payload}
            for r in db.scalars(select(model).where(model.analysis_id == row.id).order_by(model.created_at, model.id))]
    return result


def analyze(db, *, actor_id, workspace_id, contract_id, version_id, current_terms_version, playbook_id=None):
    ctx, contract, version = load_version(db, actor_id=actor_id, workspace_id=workspace_id, contract_id=contract_id,
        version_id=version_id, current_terms_version=current_terms_version, operation="propose")
    artifact, sources = stored_sources(db, actor_id=actor_id, workspace_id=workspace_id, document_id=version.document_id,
        version_id=version.version_id, current_terms_version=current_terms_version)
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
        return analysis_response(db, existing)
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
    authorize_document(db, actor_id, workspace_id, contract.document_id, current_terms_version=current_terms_version, operation="propose")
    audit(db, ctx, "contract_analysis_proposed", row.id)
    return analysis_response(db, row)


def list_contracts(db, *, actor_id, workspace_id, current_terms_version):
    ctx = authorize_workspace(db, actor_id, workspace_id, current_terms_version=current_terms_version)
    items = []
    for contract in db.scalars(select(Contract).where(Contract.workspace_id == workspace_id,
        Contract.organization_id == ctx.organization_id).order_by(Contract.created_at, Contract.id).limit(200)):
        try:
            authorize_document(db, actor_id, workspace_id, contract.document_id, current_terms_version=current_terms_version)
        except LegalAccessDenied:
            continue
        items.append({"contract_id": contract.id, "document_id": contract.document_id, "title": contract.title,
            "versions": [{"contract_version_id": v.id, "version_id": v.version_id, "source_sha256": v.source_sha256}
                for v in db.scalars(select(ContractVersion).where(ContractVersion.contract_id == contract.id))]})
    return {"items": items}
