"""Adversarial exact review, version membership, cross-source reads and transaction release."""
import os
import unittest
from uuid import uuid4
from sqlalchemy import select, update
from app.db.models.legal_review import LegalReviewDecision, LegalEvent
from app.db.models.legal_scope import DocumentAccess, WorkspaceMembership, LegalDocumentScope, Matter
from app.services import legal_review
from app.services.legal_policy import LegalAccessDenied
import test_legal_scope_contracts_persistence as fixtures
import test_legal_scope_provisioning as provisioning


class ContractHardeningTests(unittest.TestCase):
    make_engine = provisioning.LegalProvisioningTests.make_engine

    def setUp(self):
        self.fixture = fixtures.ContractPersistenceTests()
        self.fixture.make_engine = self.make_engine
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.db, self.service, self.args = self.fixture.db, self.fixture.service, self.fixture.args

    def reviewer(self, role="legal_reviewer"):
        f = self.fixture.fixture
        f.grant(f.bob, role=role)
        for op in ("read", "review_legal"):
            self.db.add(DocumentAccess(document_id=self.fixture.source.document_id, organization_id=f.ws.organization_id,
                workspace_id=f.ws.id, user_id=f.bob.id, operation=op))
        self.db.commit()
        return f.bob.id

    def decide(self, review, reviewer):
        return legal_review.decide(self.db, workspace_id=self.args["workspace_id"], review_id=review.id,
            reviewer_id=reviewer, decision="approve", rationale="Synthetic independent review", current_terms_version="1.0")

    def test_forged_hash_fails_without_decision_or_event_and_document_review_grant_required(self):
        proposal = self.fixture.analyze()["obligations"][0]
        reviewer = self.reviewer()
        review = legal_review.submit(self.db, workspace_id=self.args["workspace_id"], target_type="contract_obligation",
            target_id=proposal["proposal_id"], target_revision_sha256="0" * 64, requester_id=self.args["actor_id"],
            idempotency_key="forged-hash", current_terms_version="1.0")
        self.db.commit()
        with self.assertRaises(self.service.ContractConflict):
            self.decide(review, reviewer)
        self.db.rollback()
        self.assertEqual(list(self.db.scalars(select(LegalReviewDecision))), [])
        self.assertEqual(list(self.db.scalars(select(LegalEvent))), [])
        good = self.service.submit_proposal(self.db, target_type="contract_obligation", target_id=proposal["proposal_id"], **self.args)
        self.db.commit()
        self.db.execute(update(DocumentAccess).where(DocumentAccess.user_id == reviewer,
            DocumentAccess.operation == "review_legal").values(is_active=False))
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):
            self.decide(good, reviewer)

    def test_business_owner_auditor_and_real_self_reviewer_cannot_approve(self):
        proposal = self.fixture.analyze()["obligations"][0]
        review = self.service.submit_proposal(self.db, target_type="contract_obligation", target_id=proposal["proposal_id"], **self.args)
        self.db.commit()
        reviewer = self.reviewer(role="business_owner")
        for role in ("business_owner", "auditor"):
            self.db.execute(update(WorkspaceMembership).where(WorkspaceMembership.user_id == reviewer).values(role=role))
            self.db.commit()
            with self.assertRaises(LegalAccessDenied):
                self.decide(review, reviewer)
        f = self.fixture.fixture
        f.alice.role = "reviewer"
        self.db.commit()
        f.grant(f.alice, role="legal_reviewer")
        self.db.add(DocumentAccess(document_id=self.fixture.source.document_id, organization_id=f.ws.organization_id,
            workspace_id=f.ws.id, user_id=f.alice.id, operation="review_legal"))
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):
            self.decide(review, f.alice.id)

    def test_restricted_matter_blocks_existing_analysis_lists_and_review(self):
        contract = self.fixture.create()
        result = self.fixture.analyze(contract)
        f = self.fixture.fixture
        matter = Matter(id=uuid4(), organization_id=f.ws.organization_id, workspace_id=f.ws.id, name="Synthetic restricted")
        self.db.add(matter)
        self.db.flush()
        self.db.execute(update(LegalDocumentScope).where(LegalDocumentScope.document_id == self.fixture.source.document_id).values(matter_id=matter.id))
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):
            self.service.get_analysis(self.db, contract_id=contract["contract_id"], version_id=contract["contract_version_id"], **self.args)
        self.assertEqual(self.service.list_related(self.db, kind="obligation-proposals", **self.args), {"items": []})

    def test_new_source_can_be_versioned_under_contract_without_leaking_denied_version(self):
        contract = self.fixture.create()
        f = self.fixture.fixture
        second = f.prepare(b"1. Payment\nBuyer shall pay within 15 days of invoice, provided the invoice is valid.\n", filename="synthetic-v2.txt")
        f.process(second)
        v2 = self.service.add_version(self.db, contract_id=contract["contract_id"], document_id=second.document_id,
            version_id=second.version_id, **self.args)
        self.db.commit()
        diff = self.service.redline(self.db, contract_id=contract["contract_id"], from_version_id=contract["contract_version_id"],
            to_version_id=v2["contract_version_id"], **self.args)
        self.assertIn("15 days", str(diff))
        self.assertIn("30 days", str(diff))
        self.db.execute(update(DocumentAccess).where(DocumentAccess.document_id == second.document_id).values(is_active=False))
        self.db.commit()
        items = self.service.list_contracts(self.db, **self.args)["items"]
        self.assertEqual(len(items[0]["versions"]), 1)
        with self.assertRaises(LegalAccessDenied):
            self.service.redline(self.db, contract_id=contract["contract_id"], from_version_id=contract["contract_version_id"],
                to_version_id=v2["contract_version_id"], **self.args)

    def test_existing_contract_event_replay_does_not_conflict_with_user_title(self):
        from app.services import legal_events
        self.fixture.create()
        event = legal_events.emit(self.db, workspace_id=self.args["workspace_id"], event_type="legal.document.extracted",
            idempotency_key="user-title-event", payload={"actor_id": str(self.args["actor_id"]),
                "document_id": str(self.fixture.source.document_id), "version_id": str(self.fixture.source.version_id),
                "extraction_id": str(self.fixture.extraction.extraction_id)})
        self.service.handle_document_extracted(self.db, event)
        self.db.commit()
        self.assertEqual(len(list(self.db.scalars(select(LegalEvent).where(LegalEvent.event_type == "legal.contract.analysis_requested")))), 1)

    def test_requester_revoked_before_review_blocks_accepted_obligation_release(self):
        proposal = self.fixture.analyze()["obligations"][0]
        reviewer = self.reviewer()
        review = self.service.submit_proposal(self.db, target_type="contract_obligation", target_id=proposal["proposal_id"], **self.args)
        self.db.commit()
        self.db.execute(update(DocumentAccess).where(DocumentAccess.user_id == self.args["actor_id"],
            DocumentAccess.operation == "propose").values(is_active=False))
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):
            self.decide(review, reviewer)
        self.db.rollback()
        self.assertEqual(list(self.db.scalars(select(LegalReviewDecision))), [])
        self.assertEqual(list(self.db.scalars(select(LegalEvent))), [])


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not selected")
class ContractHardeningPostgresTests(ContractHardeningTests):
    make_engine = provisioning.LegalProvisioningPostgresTests.make_engine


if __name__ == "__main__":
    unittest.main()
