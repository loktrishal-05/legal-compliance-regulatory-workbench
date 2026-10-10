"""Authorized compliance graph, reviewed proof, frozen assessments and durable drift."""
import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select

from app.db.models import DocumentVersion
from app.db.models import legal_compliance as m
from app.db.models.legal_regulatory import ApplicabilityDecision, RegulatoryVersion, RegulatoryChange, RegulatoryCampaign
from app.db.models.legal_scope import WorkspaceMembership
from app.services import legal_regulatory as regulatory, legal_review, legal_events, legal_scheduler, legal_extraction
from app.services.audit import append_event
from app.services.canonicalization import canonical_hash
from app.services.compliance_assessment import impact
from app.services.legal_compliance_snapshot import evaluate_snapshot, projection
from app.services.legal_policy import LegalAccessDenied, authorize_document

MODELS = {"requirements": m.Requirement, "interpretations": m.InterpretationRevision,
    "policies": m.Policy, "policy-versions": m.PolicyVersion, "controls": m.Control, "evidence": m.Evidence,
    "evidence-versions": m.EvidenceVersion, "mappings": m.Mapping, "rules": m.RuleVersion,
    "assessments": m.Assessment, "findings": m.ComplianceFinding, "reevaluations": m.Reevaluation}
TARGETS = {"requirement_interpretation": m.InterpretationRevision, "compliance_rule": m.RuleVersion,
    "evidence_acceptance": m.EvidenceVersion, "assessment": m.Assessment, "compliance_finding": m.ComplianceFinding}


def now():
    return datetime.now(timezone.utc)


def utc(value):
    # SQLite fixtures return naive UTC; production DateTime(timezone=True) remains aware.
    return value.replace(tzinfo=timezone.utc) if value is not None and value.tzinfo is None else value


def audit(db, ctx, operation, row):
    append_event(db, event_type="LEGAL_ACTIVITY_RECORDED", actor_id=ctx.actor_id, actor_kind="user",
        payload={"organization_id": str(ctx.organization_id), "workspace_id": str(ctx.workspace_id),
                 "domain": "compliance", "operation": operation, "object_id": str(row.id)})


def source_version(db, ctx, document_id, version_id, terms, operation="read", requester_id=None):
    authorize_document(db, ctx.actor_id, ctx.workspace_id, document_id, current_terms_version=terms,
                       operation=operation, requester_id=requester_id)
    row = db.scalar(select(DocumentVersion).where(DocumentVersion.id == version_id,
        DocumentVersion.document_id == document_id, DocumentVersion.workspace_id == ctx.workspace_id,
        DocumentVersion.organization_id == ctx.organization_id))
    if row is None or row.status not in {"ready", "needs_verification"}:
        raise LegalAccessDenied()
    return row


def get(db, model, ctx, ident, terms, *, review_requester=None):
    row = regulatory.scoped(db, model, ctx, ident)
    operation = "review_compliance" if review_requester else "read"
    if isinstance(row, m.Requirement):
        version = regulatory.scoped(db, RegulatoryVersion, ctx, row.regulatory_version_id)
        regulatory.authorize_version(db, ctx, version, terms, operation, review_requester)
    elif isinstance(row, (m.InterpretationRevision, m.Assessment, m.Mapping)):
        get(db, m.Requirement, ctx, row.requirement_id, terms, review_requester=review_requester)
        if isinstance(row, m.Mapping):
            if row.evidence_version_id:
                get(db, m.EvidenceVersion, ctx, row.evidence_version_id, terms, review_requester=review_requester)
            if row.policy_version_id:
                get(db, m.PolicyVersion, ctx, row.policy_version_id, terms, review_requester=review_requester)
        if isinstance(row, m.Assessment):
            for comp in row.inputs["components"]:
                for evidence in comp["evidence"]:
                    get(db, m.EvidenceVersion, ctx, UUID(evidence["evidence_id"]), terms, review_requester=review_requester)
    elif isinstance(row, (m.PolicyVersion, m.EvidenceVersion)):
        source_version(db, ctx, row.document_id, row.version_id, terms, operation, review_requester)
    elif isinstance(row, m.RuleVersion):
        get(db, m.InterpretationRevision, ctx, row.interpretation_id, terms, review_requester=review_requester)
    elif isinstance(row, (m.ComplianceFinding, m.Reevaluation)):
        get(db, m.Assessment, ctx, row.assessment_id, terms, review_requester=review_requester)
    return row


def citations(db, ctx, document_id, version_id, span_ids, terms):
    result = [legal_extraction.resolve_span(db, actor_id=ctx.actor_id, workspace_id=ctx.workspace_id,
        document_id=document_id, version_id=version_id, span_id=span_id, current_terms_version=terms)
        for span_id in span_ids]
    return json.loads(json.dumps(result, default=str))


def create(db, *, resource, actor_id, workspace_id, request, current_terms_version):
    ctx = regulatory.context(db, actor_id, workspace_id, current_terms_version, write=True)
    terms, values = current_terms_version, request.model_dump()
    if resource == "requirements":
        version = regulatory.scoped(db, RegulatoryVersion, ctx, request.regulatory_version_id)
        regulatory.authorize_version(db, ctx, version, terms, "propose")
    elif resource == "interpretations":
        req = get(db, m.Requirement, ctx, request.requirement_id, terms)
        version = regulatory.scoped(db, RegulatoryVersion, ctx, req.regulatory_version_id)
        values["citations"] = citations(db, ctx, version.document_id, version.version_id, values.pop("span_ids"), terms)
    elif resource == "controls":
        owner = db.scalar(select(WorkspaceMembership).where(WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == request.owner_id, WorkspaceMembership.is_active.is_(True)))
        if owner is None:
            raise LegalAccessDenied()
    elif resource in ("policy-versions", "evidence-versions"):
        if resource == "policy-versions":
            get(db, m.Policy, ctx, request.policy_id, terms)
        else:
            get(db, m.Evidence, ctx, request.evidence_id, terms)
            if request.replaces_id:
                previous = get(db, m.EvidenceVersion, ctx, request.replaces_id, terms)
                if previous.evidence_id != request.evidence_id:
                    raise LegalAccessDenied()
            values["citations"] = citations(db, ctx, request.document_id, request.version_id, values.pop("span_ids"), terms)
        version = source_version(db, ctx, request.document_id, request.version_id, terms, "propose")
        values["source_sha256"] = version.source_sha256
    elif resource == "mappings":
        for field, model in (("requirement_id", m.Requirement), ("control_id", m.Control),
                ("policy_version_id", m.PolicyVersion), ("evidence_version_id", m.EvidenceVersion)):
            if values[field]:
                get(db, model, ctx, values[field], terms)
        existing = db.scalar(select(m.Mapping).where(m.Mapping.workspace_id == workspace_id,
            *(getattr(m.Mapping, key) == value for key, value in values.items())))
        if existing:
            return existing
    elif resource == "rules":
        get(db, m.Control, ctx, request.control_id, terms)
        interpretation = get(db, m.InterpretationRevision, ctx, request.interpretation_id, terms)
        if not regulatory.approved(db, interpretation, "requirement_interpretation"):
            raise LegalAccessDenied()
    elif resource == "assessments":
        req = get(db, m.Requirement, ctx, request.requirement_id, terms)
        applicability = regulatory.scoped(db, ApplicabilityDecision, ctx, request.applicability_id)
        if applicability.regulatory_version_id != req.regulatory_version_id:
            raise LegalAccessDenied()
        at = now()
        inputs = assemble(db, ctx, req, applicability, at, terms)
        result = evaluate_snapshot(inputs, at)
        values.update(evaluated_at=at, inputs=inputs, result=json.loads(json.dumps(result)), status=result["status"])
    elif resource == "findings":
        get(db, m.Assessment, ctx, request.assessment_id, terms)
    elif resource not in ("policies", "evidence"):
        raise ValueError("compliance_resource_invalid")
    model = MODELS[resource]
    if hasattr(model, "actor_id"):
        values["actor_id"] = actor_id
    if hasattr(model, "revision_sha256"):
        values["revision_sha256"] = canonical_hash(json.loads(json.dumps(values, default=str)))
    row = model(id=uuid4(), organization_id=ctx.organization_id, workspace_id=workspace_id, **values)
    db.add(row)
    audit(db, ctx, f"{resource}_proposed", row)
    db.flush()
    if resource == "mappings":
        invalidate(db, workspace_id, "mapping_changed", str(row.id), requirement_id=row.requirement_id)
    return row


def assemble(db, ctx, requirement, applicability, at, terms):
    app_approved = regulatory.approved(db, applicability, "regulatory_applicability")
    mappings = list(db.scalars(select(m.Mapping).where(m.Mapping.workspace_id == ctx.workspace_id,
        m.Mapping.requirement_id == requirement.id).order_by(m.Mapping.created_at, m.Mapping.id)))
    components = []
    pending = False
    for control_id in sorted({row.control_id for row in mappings}, key=str):
        control = get(db, m.Control, ctx, control_id, terms)
        candidates = db.scalars(select(m.RuleVersion).where(m.RuleVersion.control_id == control_id,
            m.RuleVersion.workspace_id == ctx.workspace_id).order_by(m.RuleVersion.created_at.desc(), m.RuleVersion.id.desc()))
        rule = next((row for row in candidates if regulatory.approved(db, row, "compliance_rule") and
            get(db, m.InterpretationRevision, ctx, row.interpretation_id, terms).requirement_id == requirement.id), None)
        evidence = []
        if rule is None:
            pending = True
            continue
        for mapping in mappings:
            if mapping.control_id != control_id:
                continue
            get(db, m.Mapping, ctx, mapping.id, terms)
            if not mapping.evidence_version_id:
                continue
            ev = get(db, m.EvidenceVersion, ctx, mapping.evidence_version_id, terms)
            replacements = db.scalars(select(m.EvidenceVersion).where(m.EvidenceVersion.replaces_id == ev.id,
                m.EvidenceVersion.workspace_id == ctx.workspace_id)).all()
            evidence.append({"evidence_id": str(ev.id), "accepted": regulatory.approved(db, ev, "evidence_acceptance"),
                "observed_at": utc(ev.observed_at).isoformat(), "valid_from": utc(ev.valid_from).isoformat(),
                "expires_at": utc(ev.expires_at).isoformat() if ev.expires_at else None, "facts": ev.facts,
                "superseded": any(regulatory.approved(db, replacement, "evidence_acceptance") for replacement in replacements),
                "citations": ev.citations})
        components.append({"control_id": str(control.id), "control_title": control.title,
            "control_description": control.description, "rule_id": str(rule.id), "rule_version": rule.revision_sha256,
            "checks": rule.checks, "evidence": evidence})
    version = regulatory.scoped(db, RegulatoryVersion, ctx, requirement.regulatory_version_id)
    siblings = list(db.scalars(select(RegulatoryVersion).where(RegulatoryVersion.regulatory_document_id == version.regulatory_document_id,
        RegulatoryVersion.workspace_id == ctx.workspace_id)))
    from app.services.regulatory_versions import RegulatoryVersion as EffectiveVersion, version_as_of
    effective = version_as_of([EffectiveVersion(str(v.id), v.source_sha256, v.effective_from, v.effective_until,
        v.published_at) for v in siblings], at.date())
    if effective.status != "effective" or effective.version.version_id != str(version.id):
        pending = True
    return {"requirement_id": str(requirement.id), "workspace_id": str(ctx.workspace_id),
        "regulatory_version_id": str(version.id), "source_sha256": version.source_sha256,
        "applicability": {"state": applicability.state if app_approved else "pending",
            "decision_id": str(applicability.id) if app_approved else None},
        "components": components, "pending_change_review": pending}


def current_projection(db, ctx, row, terms):
    get(db, m.Assessment, ctx, row.id, terms)
    req = get(db, m.Requirement, ctx, row.requirement_id, terms)
    app = regulatory.scoped(db, ApplicabilityDecision, ctx, row.applicability_id)
    result = projection(row.result, assemble(db, ctx, req, app, now(), terms), now())
    queued = list(db.scalars(select(m.Reevaluation.reason).where(m.Reevaluation.assessment_id == row.id)))
    if queued:
        result["freshness"] = "stale"
        result["reasons"] = sorted(set(result["reasons"] + queued))
    result["review_state"] = "approved" if regulatory.approved(db, row, "assessment") else "not_approved"
    return result


def invalidate(db, workspace_id, reason, cause_key, requirement_id=None):
    query = select(m.Assessment).where(m.Assessment.workspace_id == workspace_id)
    if requirement_id:
        query = query.where(m.Assessment.requirement_id == requirement_id)
    count = 0
    for row in db.scalars(query.with_for_update()):
        if db.scalar(select(m.Reevaluation.id).where(m.Reevaluation.assessment_id == row.id,
                m.Reevaluation.cause_key == cause_key)) is None:
            db.add(m.Reevaluation(id=uuid4(), organization_id=row.organization_id, workspace_id=workspace_id,
                assessment_id=row.id, reason=reason, cause_key=cause_key))
            count += 1
    db.flush()
    return count


def _authorize_target(db, ctx, ident, target):
    get(db, TARGETS[target], ctx, ident, legal_review._terms())


def _on_approve(db, review):
    row = db.get(TARGETS[review.target_type], review.target_id)
    if row is None or (row.workspace_id, row.actor_id, row.revision_sha256) != (
            review.workspace_id, review.requester_id, review.target_revision_sha256):
        raise LegalAccessDenied()
    decision = next((d for d in legal_review.decisions(db, review.id) if d.decision == "approve"), None)
    if decision is None:
        raise LegalAccessDenied()
    ctx = regulatory.context(db, decision.reviewer_id, review.workspace_id, legal_review._terms())
    get(db, type(row), ctx, row.id, legal_review._terms(), review_requester=row.actor_id)
    if isinstance(row, m.EvidenceVersion):
        invalidate(db, row.workspace_id, "evidence accepted or replaced", f"evidence:{row.id}")
    elif isinstance(row, m.RuleVersion):
        interpretation = get(db, m.InterpretationRevision, ctx, row.interpretation_id, legal_review._terms())
        if not regulatory.approved(db, interpretation, "requirement_interpretation"):
            raise LegalAccessDenied()
        invalidate(db, row.workspace_id, "approved rule changed", f"rule:{row.id}", interpretation.requirement_id)
    elif isinstance(row, m.ComplianceFinding):
        legal_events.emit(db, workspace_id=row.workspace_id, event_type="legal.compliance.finding_accepted",
            payload={"finding_id": str(row.id), "assessment_id": str(row.assessment_id)}, idempotency_key=str(row.id))
    audit(db, ctx, "review_approved", row)


def scan_expiry(db, at):
    count = 0
    for ev in db.scalars(select(m.EvidenceVersion).where(m.EvidenceVersion.expires_at <= at).with_for_update()):
        if not regulatory.approved(db, ev, "evidence_acceptance"):
            continue
        legal_events.emit(db, workspace_id=ev.workspace_id, event_type="legal.compliance.evidence_expired",
            payload={"evidence_id": str(ev.evidence_id), "evidence_version_id": str(ev.id),
                     "expires_at": utc(ev.expires_at).isoformat()}, idempotency_key=str(ev.id))
        count += invalidate(db, ev.workspace_id, "evidence expired", f"expiry:{ev.id}")
    return count


def graph(db, ctx, terms):
    nodes, links, kinds = {}, [], {}
    for row in db.scalars(select(m.Requirement).where(m.Requirement.workspace_id == ctx.workspace_id)):
        try:
            get(db, m.Requirement, ctx, row.id, terms)
        except LegalAccessDenied:
            continue
        nodes[str(row.id)] = nodes[str(row.regulatory_version_id)] = str(ctx.workspace_id)
        kinds[str(row.id)], kinds[str(row.regulatory_version_id)] = "requirement", "regulatory_version"
        links.append((str(row.regulatory_version_id), str(row.id)))
    for row in db.scalars(select(m.Mapping).where(m.Mapping.workspace_id == ctx.workspace_id)):
        try:
            get(db, m.Mapping, ctx, row.id, terms)
        except LegalAccessDenied:
            continue
        for ident, kind in ((row.control_id, "control"), (row.policy_version_id, "policy"), (row.evidence_version_id, "evidence")):
            if ident:
                nodes[str(ident)], kinds[str(ident)] = str(ctx.workspace_id), kind
                links.extend([(str(row.requirement_id), str(ident)), (str(ident), str(row.requirement_id))])
    return nodes, links, kinds


def impact_paths(db, ctx, changed_id, terms):
    nodes, links, kinds = graph(db, ctx, terms)
    if str(changed_id) not in nodes:
        raise LegalAccessDenied()
    return [{"id": ident, "kind": kinds[ident], "path": list(path)}
            for ident, path in sorted(impact(nodes, links, [str(changed_id)]).items())]


def on_regulatory_change(db, event):
    change = db.scalar(select(RegulatoryChange).where(RegulatoryChange.id == UUID(event.payload["change_id"]),
        RegulatoryChange.workspace_id == event.workspace_id).with_for_update())
    if change is None or not regulatory.approved(db, change, "regulatory_change"):
        raise LegalAccessDenied()
    for req in db.scalars(select(m.Requirement).where(m.Requirement.workspace_id == event.workspace_id,
            m.Requirement.regulatory_version_id.in_([change.from_version_id, change.to_version_id]))):
        invalidate(db, event.workspace_id, "accepted regulatory change", f"change:{change.id}", req.id)


for _target in TARGETS:
    legal_review.register_target(_target, on_approve=_on_approve, operation="review_compliance",
        authorize=lambda db, ctx, ident, target=_target: _authorize_target(db, ctx, ident, target))
legal_scheduler.register_scan("compliance_evidence_expiry", scan_expiry)
legal_events.register_handler("legal.regulatory.change_accepted", on_regulatory_change)
