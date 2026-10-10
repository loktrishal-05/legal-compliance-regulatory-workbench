"""Synthetic demo seed (operator-run). Refuses unless LEGAL_DEMO_MODE=true. Idempotent: an existing demo
organization means "already seeded" and nothing changes.

Everything goes through the real, audited services (provisioning, intake, extraction, contracts, reviews,
outbox, obligations, regulatory, compliance). Fixture bytes are labelled "synthetic fixture, operator-seeded,
not malware-scanned" in their recorded scan policy; real uploads still require a configured scanner.

Users (independent review needs a proposer plus distinct legal and compliance reviewers):
  demo-admin (workspace admin), demo-counsel (legal reviewer), demo-compliance (compliance reviewer),
  demo-analyst (analyst/proposer), demo-owner (business owner), demo-auditor (auditor, read-only).
Passwords come only from DEMO_<ROLE>_PASSWORD env vars (no hardcoded secrets). Terms acceptance for these
synthetic accounts is recorded at seed time by the operator.

Usage: LEGAL_DEMO_MODE=true DEMO_ADMIN_PASSWORD=... (all six) python -m scripts.legal_demo_seed
"""
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

ORG = "LRA Demo Organization (synthetic)"
ROLES = {"admin": ("workspace_admin", "admin"), "counsel": ("legal_reviewer", "reviewer"),
         "compliance": ("compliance_reviewer", "reviewer"), "analyst": ("analyst", "requester"),
         "owner": ("business_owner", "requester"), "auditor": ("auditor", "requester")}
PROVENANCE = "synthetic-fixture-operator-seeded-not-malware-scanned"
FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "legal_contracts"
REGULATION_V1 = b"1. SYNTHETIC Records Regulation: retain transaction records for five years.\n2. Report annually to the synthetic authority.\n"
REGULATION_V2 = b"1. SYNTHETIC Records Regulation: retain transaction records for seven years.\n2. Report annually to the synthetic authority.\n"


class SeedRefused(RuntimeError):
    pass


class FixtureScanner:
    """Not a malware scanner: records honest provenance for operator-seeded synthetic fixtures only."""
    policy_version = PROVENANCE

    def __call__(self, data):
        return True, "operator-seeded-synthetic-fixture"


def passwords_from_env(env=os.environ):
    if env.get("LEGAL_DEMO_MODE", "").lower() != "true":
        raise SeedRefused("LEGAL_DEMO_MODE=true is required; refusing to seed demo data")
    values = {role: env.get(f"DEMO_{role.upper()}_PASSWORD", "") for role in ROLES}
    missing = [f"DEMO_{role.upper()}_PASSWORD" for role, value in values.items() if len(value) < 12]
    if missing:
        raise SeedRefused("Missing or short (<12 chars) demo passwords: " + ", ".join(missing))
    return values


def seed(db, *, data_root: Path, passwords: dict, terms: str, now=None) -> dict:
    from app.core.security import hash_password
    from app.db.models import User
    from app.db.models.legal_scope import Matter, Organization
    from app.services import legal_provisioning as prov
    if db.scalar(select(Organization.id).where(Organization.name == ORG)):
        return {"status": "already_seeded"}
    now = now or datetime.now(timezone.utc)
    users = {}
    for role, (_, platform) in ROLES.items():
        user = db.scalar(select(User).where(User.username == f"demo-{role}"))
        if user is None:
            user = User(id=uuid4(), username=f"demo-{role}", role=platform, display_name=f"Demo {role} (synthetic)")
            db.add(user)
        user.password_hash = hash_password(passwords[role])
        user.terms_version, user.terms_accepted_at = terms, now
        users[role] = user
    db.commit()
    ws = prov.bootstrap_workspace(db, operator_label="legal-demo-seed", organization_name=ORG,
                                  workspace_name="Demo workspace (synthetic)", admin_user_id=users["admin"].id)
    db.commit()
    admin = users["admin"].id
    for role, (membership, _) in ROLES.items():
        if role != "admin":
            prov.grant_membership(db, admin_id=admin, workspace_id=ws.id, user_id=users[role].id, role=membership,
                                  clearance="internal", current_terms_version=terms)
    db.commit()
    matter = Matter(id=uuid4(), organization_id=ws.organization_id, workspace_id=ws.id, name="Demo matter (synthetic)")
    db.add(matter)
    db.commit()
    c = _Ctx(db, ws, users, terms, data_root, admin)
    summary = {"status": "seeded", "workspace_id": str(ws.id), "matter_id": str(matter.id)}
    summary.update(_contracts(c))
    summary.update(_regulatory_and_compliance(c, now))
    return summary


class _Ctx:
    def __init__(self, db, ws, users, terms, data_root, admin):
        self.db, self.ws, self.users, self.terms, self.data_root, self.admin = db, ws, users, terms, data_root, admin

    def grant(self, document_id, role, *operations):
        from app.services import legal_provisioning as prov
        for operation in ("read",) + operations:
            prov.set_document_access(self.db, admin_id=self.admin, workspace_id=self.ws.id, document_id=document_id,
                user_id=self.users[role].id, operation=operation, active=True, current_terms_version=self.terms)
        self.db.commit()

    def receive(self, data, filename, document_type):
        from app.services import legal_extraction, legal_intake
        received = legal_intake.receive(self.db, actor_id=self.users["analyst"].id, workspace_id=self.ws.id,
            filename=filename, document_type=document_type, classification="internal", data=data,
            current_terms_version=self.terms, data_root=self.data_root, scanner=FixtureScanner())
        self.db.commit()
        self.grant(received.document_id, "analyst", "propose")
        for role in ("counsel", "compliance", "owner", "auditor"):
            self.grant(received.document_id, role)
        self.grant(received.document_id, "counsel", "review_legal")
        self.grant(received.document_id, "compliance", "review_compliance")
        artifact = legal_extraction.process(self.db, actor_id=self.users["analyst"].id, workspace_id=self.ws.id,
            document_id=received.document_id, version_id=received.version_id, current_terms_version=self.terms,
            data_root=self.data_root)
        self.db.commit()
        return received, artifact

    def review(self, target_type, target_id, revision, reviewer):
        from app.services import legal_review
        review = legal_review.submit(self.db, workspace_id=self.ws.id, target_type=target_type, target_id=target_id,
            target_revision_sha256=revision, requester_id=self.users["analyst"].id,
            idempotency_key=f"demo:{target_type}:{target_id}", current_terms_version=self.terms)
        self.db.commit()
        legal_review.decide(self.db, workspace_id=self.ws.id, review_id=review.id, reviewer_id=self.users[reviewer].id,
            decision="approve", rationale="Synthetic demo review", current_terms_version=self.terms)
        self.db.commit()
        return review


def _contracts(c):
    from app.db.models.legal_obligations import LegalObligation
    from app.services import legal_contracts, legal_events, legal_obligations, legal_review
    analyses = []
    for name in ("msa.txt", "nda.txt"):
        received, _ = c.receive((FIXTURES / name).read_bytes(), name, "contract")
        contract = legal_contracts.create_contract(c.db, actor_id=c.users["analyst"].id, workspace_id=c.ws.id,
            document_id=received.document_id, version_id=received.version_id, title=f"Synthetic {name[:-4].upper()}",
            current_terms_version=c.terms)
        c.db.commit()
        analyses.append(legal_contracts.analyze(c.db, actor_id=c.users["analyst"].id, workspace_id=c.ws.id,
            contract_id=contract["contract_id"], version_id=contract["contract_version_id"], current_terms_version=c.terms))
        c.db.commit()
    proposal = next(o for a in analyses for o in a["obligations"])
    review = legal_contracts.submit_proposal(c.db, actor_id=c.users["analyst"].id, workspace_id=c.ws.id,
        current_terms_version=c.terms, target_type="contract_obligation", target_id=proposal["proposal_id"])
    c.db.commit()
    legal_review.decide(c.db, workspace_id=c.ws.id, review_id=review.id, reviewer_id=c.users["counsel"].id,
        decision="approve", rationale="Synthetic demo review", current_terms_version=c.terms)
    c.db.commit()
    legal_events.dispatch_due(c.db, worker_id="legal-demo-seed")
    obligation = c.db.scalar(select(LegalObligation).where(LegalObligation.workspace_id == c.ws.id))
    legal_obligations.confirm_deadline(c.db, actor_id=c.users["counsel"].id, workspace_id=c.ws.id,
        obligation_id=obligation.id, timezone_name="UTC", due_local=(date.today() + timedelta(days=21)).isoformat(),
        owner_id=c.users["owner"].id, notice_days=7, current_terms_version=c.terms)
    c.db.commit()
    return {"contracts": len(analyses), "obligation_id": str(obligation.id)}


def _regulatory_and_compliance(c, now):
    from app.db.models.legal_extraction import LegalSourceSpan
    from app.schemas import legal_compliance as cs
    from app.schemas.legal_regulatory import (ApplicabilityRequest, ChangeRequest, DocumentRequest, SourceRequest,
                                              VersionRequest, WatchlistRequest)
    from app.services import legal_compliance, legal_events, legal_regulatory as reg
    analyst = c.users["analyst"].id

    def call(fn, request, **kw):
        row = fn(c.db, actor_id=analyst, workspace_id=c.ws.id, current_terms_version=c.terms, request=request, **kw)
        c.db.commit()
        return row

    def create(resource, request):
        row = legal_compliance.create(c.db, resource=resource, actor_id=analyst, workspace_id=c.ws.id,
                                      request=request, current_terms_version=c.terms)
        c.db.commit()
        return row

    source = call(reg.create_source, SourceRequest(name="SYNTHETIC Records Authority", jurisdiction="SYNTHETIC",
                                                   owner_id=analyst))
    c.review("regulatory_source", source.id, source.revision_sha256, "compliance")
    document = call(reg.create_document, DocumentRequest(source_id=source.id, title="Synthetic Records Regulation"))
    versions = []
    # Half-open effective intervals: v1 ends exactly when v2 starts, so the as-of version is unambiguous.
    for data, effective, until in ((REGULATION_V1, date(2025, 1, 1), date(2026, 1, 1)), (REGULATION_V2, date(2026, 1, 1), None)):
        received, artifact = c.receive(data, f"regulation-{effective.year}.txt", "regulation")
        versions.append(call(reg.import_version, VersionRequest(regulatory_document_id=document.id,
            document_id=received.document_id, version_id=received.version_id, extraction_id=artifact.extraction_id,
            effective_from=effective, effective_until=until), data_root=c.data_root))
    call(reg.create_watchlist, WatchlistRequest(source_id=source.id, max_age_days=30))
    version = versions[1]
    applicability = call(reg.create_applicability, ApplicabilityRequest(regulatory_version_id=version.id,
        state="applicable", jurisdiction="SYNTHETIC", entity="Synthetic entity", product="Synthetic product",
        business_unit="Synthetic unit", effective_on=now.date(), rationale="Synthetic applicability"))
    c.review("regulatory_applicability", applicability.id, applicability.revision_sha256, "compliance")
    spans = list(c.db.scalars(select(LegalSourceSpan.id).where(LegalSourceSpan.extraction_id == version.extraction_id)))
    control = create("controls", cs.ControlRequest(title="Synthetic retention control", description="Retain records",
                                                   owner_id=c.users["owner"].id))
    states, expiring = {}, False
    plans = (("Retention evidence accepted", 7, timedelta(days=365)), ("No evidence yet", None, None),
             ("Evidence fails and expires", 3, timedelta(seconds=3)))
    for title, years, ttl in plans:
        requirement = create("requirements", cs.RequirementRequest(regulatory_version_id=version.id, title=title))
        interpretation = create("interpretations", cs.InterpretationRequest(requirement_id=requirement.id,
            text=f"Synthetic interpretation: {title}", span_ids=spans))
        c.review("requirement_interpretation", interpretation.id, interpretation.revision_sha256, "compliance")
        rule = create("rules", cs.RuleRequest(control_id=control.id, interpretation_id=interpretation.id,
            checks=[cs.CheckRequest(fact="retention_years", op="ge", value=7)]))
        c.review("compliance_rule", rule.id, rule.revision_sha256, "compliance")
        mapping = {"requirement_id": requirement.id, "control_id": control.id}
        if years is not None:
            evidence = create("evidence", cs.EvidenceRequest(title=f"Synthetic proof ({title})"))
            ev = create("evidence-versions", cs.EvidenceVersionRequest(evidence_id=evidence.id,
                document_id=version.document_id, version_id=version.version_id, observed_at=now, valid_from=now,
                expires_at=datetime.now(timezone.utc) + ttl, facts={"retention_years": years}, span_ids=spans))
            c.review("evidence_acceptance", ev.id, ev.revision_sha256, "compliance")
            mapping["evidence_version_id"] = ev.id
            expiring = expiring or ttl < timedelta(minutes=1)
        create("mappings", cs.MappingRequest(**mapping))
        assessment = create("assessments", cs.AssessmentRequest(requirement_id=requirement.id,
                                                                applicability_id=applicability.id))
        states[title] = assessment.status
        if assessment.status == "unsatisfied":
            create("findings", cs.FindingRequest(assessment_id=assessment.id, text="Synthetic retention gap"))
    if expiring:  # real expiry; the scheduled scan marks the current projection stale and opens a task
        time.sleep(3.5)
        legal_compliance.scan_expiry(c.db, datetime.now(timezone.utc))
        c.db.commit()
    # The new regulatory version's diff arrives after the assessments: its review opens the impact work.
    change = call(reg.create_change, ChangeRequest(from_version_id=versions[0].id, to_version_id=versions[1].id))
    c.review("regulatory_change", change.id, change.revision_sha256, "compliance")
    legal_events.dispatch_due(c.db, worker_id="legal-demo-seed")
    return {"assessment_states": states, "regulatory_change_id": str(change.id)}


def main():
    try:
        passwords = passwords_from_env()
    except SeedRefused as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        return 2
    from app.core.config import settings
    from app.db.session import SessionLocal
    import scripts.legal_worker as worker
    worker.register_all()
    with SessionLocal() as db:
        result = seed(db, data_root=settings.data_root, passwords=passwords, terms=settings.current_terms_version)
    print(result)  # ids and counts only, never passwords
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
