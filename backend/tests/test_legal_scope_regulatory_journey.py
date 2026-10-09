"""Real intake/extraction -> registry review -> version/diff/applicability, synthetic only."""
from datetime import date
import os
import unittest
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import select

from app.db.base import Base
from app.db.models.legal_regulatory import (RegulatorySource, RegulatoryDocument, RegulatoryVersion,
    RegulatoryChange, ApplicabilityDecision, RegulatoryWatchlist, RegulatoryCampaign)
from app.db.models.legal_review import LegalReview, LegalReviewDecision, LegalEvent
from app.db.models.legal_scope import DocumentAccess
from app.schemas.legal_regulatory import SourceRequest, DocumentRequest, VersionRequest, ChangeRequest, ApplicabilityRequest
from app.services import legal_regulatory as service, legal_review
from app.services.audit import AuditChainError
from app.services.legal_policy import LegalAccessDenied
import test_legal_scope_extraction as extraction
import test_legal_scope_provisioning as provisioning


class RegulatoryJourneyTests(unittest.TestCase):
    make_engine = provisioning.LegalProvisioningTests.make_engine

    def setUp(self):
        self.fixture = extraction.LegalExtractionTests()
        self.fixture.make_engine = self.make_engine
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.db = self.fixture.db
        Base.metadata.create_all(self.fixture.engine, tables=[m.__table__ for m in (RegulatorySource,
            RegulatoryDocument, RegulatoryVersion, RegulatoryChange, ApplicabilityDecision, RegulatoryWatchlist,
            RegulatoryCampaign, LegalReview, LegalReviewDecision, LegalEvent)])
        self.fixture.grant(self.fixture.bob, role="compliance_reviewer")
        self.source = self.call(service.create_source, SourceRequest(name="SYNTHETIC regulator", jurisdiction="SYNTHETIC",
            owner_id=self.fixture.alice.id))
        self.document = self.call(service.create_document, DocumentRequest(source_id=self.source.id, title="Synthetic regulation"))

    def call(self, fn, request, **kw):
        result = fn(self.db, actor_id=self.fixture.alice.id, workspace_id=self.fixture.ws.id,
                    current_terms_version="1.0", request=request, **kw)
        self.db.commit()
        return result

    def review(self, row, target, reviewer=None, digest=None):
        review = legal_review.submit(self.db, workspace_id=self.fixture.ws.id, target_type=target,
            target_id=row.id, target_revision_sha256=digest or row.revision_sha256,
            requester_id=self.fixture.alice.id, idempotency_key=str(row.id), current_terms_version="1.0")
        self.db.commit()
        legal_review.decide(self.db, workspace_id=self.fixture.ws.id, review_id=review.id,
            reviewer_id=(reviewer or self.fixture.bob).id, decision="approve", rationale="Synthetic review",
            current_terms_version="1.0")
        self.db.commit()
        return review

    def version_request(self, text=b"1. SYNTHETIC retain five years.\n2. Report annually.", effective=date(2025, 1, 1)):
        received = self.fixture.prepare(text)
        artifact = self.fixture.process(received)
        for operation in ("read", "review_compliance"):
            self.db.add(DocumentAccess(document_id=received.document_id, organization_id=self.fixture.ws.organization_id,
                workspace_id=self.fixture.ws.id, user_id=self.fixture.bob.id, operation=operation))
        self.db.commit()
        return VersionRequest(regulatory_document_id=self.document.id, document_id=received.document_id,
            version_id=received.version_id, extraction_id=artifact.extraction_id, effective_from=effective)

    def import_version(self, request):
        return self.call(service.import_version, request, data_root=self.fixture.root)

    def test_unapproved_registry_blocks_import(self):
        with self.assertRaises(LegalAccessDenied):
            self.import_version(self.version_request())

    def test_independent_registry_review_and_source_integrity(self):
        self.review(self.source, "regulatory_source")
        request = self.version_request()
        row = self.import_version(request)
        self.assertEqual(self.import_version(request).id, row.id)
        self.assertEqual(row.effective_from, date(2025, 1, 1))
        row.effective_from = date(2020, 1, 1)
        with self.assertRaisesRegex(ValueError, "immutable"):
            self.db.flush()
        self.db.rollback()

    def test_self_review_and_forged_hash_never_promote(self):
        with self.assertRaises(LegalAccessDenied):
            self.review(self.source, "regulatory_source", reviewer=self.fixture.alice)
        self.db.rollback()
        other = self.call(service.create_source, SourceRequest(name="SYNTHETIC other", jurisdiction="SYNTHETIC",
            owner_id=self.fixture.alice.id))
        with self.assertRaises(LegalAccessDenied):
            self.review(other, "regulatory_source", digest="0" * 64)
        self.db.rollback()
        self.assertEqual(other.trust_state, "proposed")

    def test_change_review_creates_one_campaign_and_event(self):
        self.review(self.source, "regulatory_source")
        old = self.import_version(self.version_request())
        new = self.import_version(self.version_request(b"1. SYNTHETIC retain seven years.\n2. Report annually."))
        change = self.call(service.create_change, ChangeRequest(from_version_id=old.id, to_version_id=new.id))
        self.assertTrue(change.exact_diff)
        self.assertTrue(change.semantic_proposal["review_required"])
        review = self.review(change, "regulatory_change")
        legal_review.decide(self.db, workspace_id=self.fixture.ws.id, review_id=review.id,
            reviewer_id=self.fixture.bob.id, decision="approve", rationale="Synthetic review", current_terms_version="1.0")
        self.db.commit()
        self.assertEqual(len(self.db.scalars(select(RegulatoryCampaign)).all()), 1)
        self.assertEqual(len(self.db.scalars(select(LegalEvent)).all()), 1)

    def test_unknown_effectivity_cannot_be_accepted_as_not_applicable(self):
        self.review(self.source, "regulatory_source")
        version = self.import_version(self.version_request(effective=None))
        proposal = self.call(service.create_applicability, ApplicabilityRequest(regulatory_version_id=version.id,
            state="not_applicable", jurisdiction="SYNTHETIC", entity="Synthetic entity", product="Synthetic product",
            business_unit="Synthetic unit", rationale="Synthetic applicability", effective_on=date(2026, 10, 9)))
        with self.assertRaises(service.RegulatoryConflict):
            self.review(proposal, "regulatory_applicability")
        self.db.rollback()
        self.assertFalse(service.approved(self.db, proposal, "regulatory_applicability"))

    def test_audit_failure_rolls_back_registry(self):
        with patch.object(service, "append_event", side_effect=AuditChainError("synthetic")):
            with self.assertRaises(AuditChainError):
                self.call(service.create_source, SourceRequest(name="must roll back", jurisdiction="SYNTHETIC",
                    owner_id=self.fixture.alice.id))
        self.db.rollback()
        self.assertEqual(len(self.db.scalars(select(RegulatorySource)).all()), 1)


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not selected")
class RegulatoryJourneyPostgresTests(RegulatoryJourneyTests):
    make_engine = provisioning.LegalProvisioningPostgresTests.make_engine
