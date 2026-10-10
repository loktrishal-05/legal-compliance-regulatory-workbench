"""Persisted compliance graph and server-owned approval state, synthetic documents."""
from datetime import datetime, timedelta, timezone
import os
import unittest

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.db.models import legal_compliance as models
from app.schemas import legal_compliance as schemas
from app.schemas.legal_regulatory import ApplicabilityRequest
from app.services import legal_compliance as service
from app.services import legal_regulatory, legal_review
from app.services.legal_policy import LegalAccessDenied
import test_legal_scope_regulatory_journey as regulatory_fixture
import test_legal_scope_provisioning as provisioning


class CompliancePersistenceTests(unittest.TestCase):
    make_engine = provisioning.LegalProvisioningTests.make_engine

    def setUp(self):
        self.base = regulatory_fixture.RegulatoryJourneyTests()
        self.base.make_engine = self.make_engine
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        self.db = self.base.db
        self.fixture = self.base.fixture
        Base.metadata.create_all(self.fixture.engine, tables=[table for table in Base.metadata.sorted_tables
            if table.name.startswith("legal_compliance_")])
        self.base.review(self.base.source, "regulatory_source")
        self.version = self.base.import_version(self.base.version_request())
        self.requirement = self.create("requirements", schemas.RequirementRequest(
            regulatory_version_id=self.version.id, title="Synthetic retention duty"))

    def create(self, resource, request):
        row = service.create(self.db, resource=resource, actor_id=self.fixture.alice.id,
            workspace_id=self.fixture.ws.id, request=request, current_terms_version="1.0")
        self.db.commit()
        return row

    def prepare_graph(self):
        from app.db.models.legal_extraction import LegalSourceSpan
        self.applicability = self.base.call(legal_regulatory.create_applicability, ApplicabilityRequest(
            regulatory_version_id=self.version.id, state="applicable", jurisdiction="SYNTHETIC", entity="Synthetic entity",
            product="Synthetic product", business_unit="Synthetic unit", effective_on=datetime.now(timezone.utc).date(),
            rationale="Synthetic applicability"))
        self.base.review(self.applicability, "regulatory_applicability")
        spans = list(self.db.scalars(select(LegalSourceSpan.id).where(LegalSourceSpan.extraction_id == self.version.extraction_id)))
        interpretation = self.create("interpretations", schemas.InterpretationRequest(
            requirement_id=self.requirement.id, text="Synthetic approved interpretation", span_ids=spans))
        self.base.review(interpretation, "requirement_interpretation")
        control = self.create("controls", schemas.ControlRequest(title="Synthetic control", description="Retain records",
            owner_id=self.fixture.alice.id))
        rule = self.create("rules", schemas.RuleRequest(control_id=control.id, interpretation_id=interpretation.id,
            checks=[schemas.CheckRequest(fact="retention_years", op="ge", value=7)]))
        self.base.review(rule, "compliance_rule")
        self.control = control
        self.create("mappings", schemas.MappingRequest(requirement_id=self.requirement.id, control_id=control.id))
        return spans

    def assess(self):
        return self.create("assessments", schemas.AssessmentRequest(requirement_id=self.requirement.id,
            applicability_id=self.applicability.id))

    def test_missing_evidence_is_insufficient_and_snapshot_immutable(self):
        self.prepare_graph()
        row = self.assess()
        self.assertEqual(row.status, "insufficient_evidence")
        self.assertTrue(row.result["reasons"])
        row.status = "satisfied"
        with self.assertRaisesRegex(ValueError, "immutable"):
            self.db.flush()
        self.db.rollback()

    def test_evidence_acceptance_and_expiry_do_not_rewrite_snapshot(self):
        spans = self.prepare_graph()
        evidence = self.create("evidence", schemas.EvidenceRequest(title="Synthetic proof"))
        now = datetime.now(timezone.utc)
        version = self.create("evidence-versions", schemas.EvidenceVersionRequest(evidence_id=evidence.id,
            document_id=self.version.document_id, version_id=self.version.version_id, observed_at=now,
            valid_from=now, expires_at=now + timedelta(days=1), facts={"retention_years": 7}, span_ids=spans))
        self.create("mappings", schemas.MappingRequest(requirement_id=self.requirement.id,
            control_id=self.control.id, evidence_version_id=version.id))
        self.assertEqual(self.assess().status, "insufficient_evidence")
        self.base.review(version, "evidence_acceptance")
        snapshot = self.assess()
        self.assertEqual(snapshot.status, "satisfied")
        service.scan_expiry(self.db, now + timedelta(days=2))
        self.db.commit()
        self.assertTrue(list(self.db.scalars(select(models.Reevaluation))))
        self.assertEqual(self.db.get(models.Assessment, snapshot.id).status, "satisfied")

    def test_cross_workspace_mapping_denied_at_service_and_database(self):
        self.prepare_graph()
        self.fixture.ws.id  # preserved source workspace
        request = schemas.MappingRequest(requirement_id=self.requirement.id, control_id=self.control.id)
        with self.assertRaises(LegalAccessDenied):
            service.create(self.db, resource="mappings", actor_id=self.fixture.alice.id,
                workspace_id=self.fixture.other.id, request=request, current_terms_version="1.0")
        with self.assertRaises(IntegrityError):
            self.db.execute(models.Mapping.__table__.insert().values(organization_id=self.fixture.other.organization_id,
                workspace_id=self.fixture.other.id, requirement_id=self.requirement.id, control_id=self.control.id))
        self.db.rollback()


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not selected")
class CompliancePersistencePostgresTests(CompliancePersistenceTests):
    make_engine = provisioning.LegalProvisioningPostgresTests.make_engine
