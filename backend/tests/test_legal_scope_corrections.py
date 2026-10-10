"""Immutable transcription proposals/independent decisions; synthetic source only."""
import hashlib
import os
import unittest
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.db.models import AuditEvent, DocumentVersion
from app.db.models.legal_correction import LegalCorrection, LegalCorrectionDecision
from app.db.models.legal_extraction import LegalExtraction, LegalSourceSpan
from app.db.models.legal_scope import DocumentAccess
from app.schemas.legal_correction import CorrectionRequest, CorrectionDecisionRequest
from app.services import legal_correction as corrections
from app.services.audit import AuditChainError
from app.services.legal_policy import LegalAccessDenied
import test_legal_scope_extraction as extraction_fixture
import test_legal_scope_provisioning as provisioning_fixture


class LegalCorrectionTests(unittest.TestCase):
    make_engine = provisioning_fixture.LegalProvisioningTests.make_engine

    def setUp(self):
        self.fixture = extraction_fixture.LegalExtractionTests()
        self.fixture.make_engine = self.make_engine
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.db = self.fixture.db
        Base.metadata.create_all(self.fixture.engine, tables=[LegalCorrection.__table__, LegalCorrectionDecision.__table__])
        self.received = self.fixture.prepare()
        self.artifact = self.fixture.process(self.received)
        self.span = self.db.get(LegalSourceSpan, self.artifact.span_ids[0])
        self.original = self.db.get(LegalExtraction, self.artifact.extraction_id).text[self.span.start:self.span.end]
        self.fixture.grant(self.fixture.bob, role="legal_reviewer")
        for operation in ("read", "review_legal"):
            self.db.add(DocumentAccess(document_id=self.received.document_id, organization_id=self.fixture.ws.organization_id,
                workspace_id=self.fixture.ws.id, user_id=self.fixture.bob.id, operation=operation))
        self.db.commit()
        self.request = CorrectionRequest(idempotency_key=uuid4(),
            expected_quote_sha256=hashlib.sha256(self.original.encode()).hexdigest(),
            corrected_text="SYNTHETIC corrected transcription: payment within 30 days.", rationale="Synthetic OCR typo correction")

    def propose(self, request=None, actor=None, workspace=None):
        result = corrections.propose(self.db, actor_id=(actor or self.fixture.alice).id,
            workspace_id=(workspace or self.fixture.ws).id, document_id=self.received.document_id,
            version_id=self.received.version_id, span_id=self.span.id, request=request or self.request,
            current_terms_version="1.0")
        self.db.commit()
        return result

    def decide(self, correction, actor=None, outcome="approved"):
        result = corrections.decide(self.db, actor_id=(actor or self.fixture.bob).id, workspace_id=self.fixture.ws.id,
            document_id=self.received.document_id, version_id=self.received.version_id,
            correction_id=correction["correction_id"], request=CorrectionDecisionRequest(outcome=outcome,
                rationale="Synthetic transcription review"), current_terms_version="1.0")
        self.db.commit()
        return result

    def test_proposal_replay_preserves_original_and_exact_locator(self):
        proposal = self.propose()
        replay = self.propose()
        self.assertEqual(proposal["correction_id"], replay["correction_id"])
        self.assertEqual(proposal["outcome"], "proposed")
        self.assertEqual(proposal["original_quote"], self.original)
        self.assertEqual(proposal["locator"], self.span.locator)
        self.assertEqual(self.db.get(LegalExtraction, self.artifact.extraction_id).text, self.original)
        self.assertEqual(self.db.get(DocumentVersion, self.received.version_id).status, "ready")
        self.assertEqual(len(list(self.db.scalars(select(LegalCorrection)))), 1)

    def test_independent_review_replay_and_successor_retain_history(self):
        proposal = self.propose()
        decided = self.decide(proposal)
        self.assertEqual(decided["outcome"], "approved")
        self.assertEqual(decided["reviewer_id"], self.fixture.bob.id)
        self.assertEqual(self.decide(proposal)["correction_id"], proposal["correction_id"])
        successor = self.propose(self.request.model_copy(update={"idempotency_key": uuid4(),
            "parent_correction_id": proposal["correction_id"], "corrected_text": "SYNTHETIC successor transcription"}))
        self.assertEqual(successor["outcome"], "proposed")
        self.assertEqual(len(list(self.db.scalars(select(LegalCorrectionDecision)))), 1)
        with self.assertRaises(corrections.CorrectionConflict):
            self.decide(proposal, outcome="rejected")

    def test_self_approval_denied_even_with_reviewer_role_and_grant(self):
        proposal = self.propose()
        self.fixture.alice.role = "reviewer"
        self.db.commit()
        self.fixture.grant(self.fixture.alice, role="legal_reviewer")
        self.db.add(DocumentAccess(document_id=self.received.document_id, organization_id=self.fixture.ws.organization_id,
            workspace_id=self.fixture.ws.id, user_id=self.fixture.alice.id, operation="review_legal"))
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):
            self.decide(proposal, actor=self.fixture.alice)

    def test_hash_mismatch_and_same_key_different_content_are_conflicts(self):
        with self.assertRaises(corrections.CorrectionConflict):
            self.propose(self.request.model_copy(update={"expected_quote_sha256": "0" * 64}))
        self.propose()
        with self.assertRaises(corrections.CorrectionConflict):
            self.propose(self.request.model_copy(update={"corrected_text": "SYNTHETIC different"}))

    def test_rejection_remains_visible_and_request_does_not_control_authority(self):
        from pydantic import ValidationError
        proposal = self.propose()
        self.assertEqual(self.decide(proposal, outcome="rejected")["outcome"], "rejected")
        self.assertEqual(self.propose()["outcome"], "rejected")
        for field in ("actor_id", "outcome", "approved"):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                CorrectionRequest.model_validate({**self.request.model_dump(), field: "approved"})
        for value in (" ", "\0"):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                CorrectionRequest.model_validate({**self.request.model_dump(), "corrected_text": value})

    def test_cross_workspace_and_revoked_access_are_uniformly_denied(self):
        with self.assertRaises(LegalAccessDenied):
            self.propose(workspace=self.fixture.other)
        proposal = self.propose()
        self.db.execute(update(DocumentAccess).where(DocumentAccess.user_id == self.fixture.bob.id).values(is_active=False))
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):
            self.decide(proposal)
        with self.assertRaises(LegalAccessDenied):
            corrections.get(self.db, actor_id=self.fixture.bob.id, workspace_id=self.fixture.ws.id,
                document_id=self.received.document_id, version_id=self.received.version_id,
                correction_id=proposal["correction_id"], current_terms_version="1.0")

    def test_audit_failure_rolls_back_proposal_and_decision(self):
        with patch.object(corrections, "append_event", side_effect=AuditChainError("SYNTHETIC failure")):
            with self.assertRaises(AuditChainError):
                self.propose()
        self.db.rollback()
        self.assertEqual(list(self.db.scalars(select(LegalCorrection))), [])
        proposal = self.propose()
        with patch.object(corrections, "append_event", side_effect=AuditChainError("SYNTHETIC failure")):
            with self.assertRaises(AuditChainError):
                self.decide(proposal)
        self.db.rollback()
        self.assertEqual(list(self.db.scalars(select(LegalCorrectionDecision))), [])

    def test_records_immutable_and_database_rejects_foreign_span(self):
        proposal = self.propose()
        row = self.db.get(LegalCorrection, proposal["correction_id"])
        values = {c.name: getattr(row, c.name) for c in LegalCorrection.__table__.columns}
        values.update(id=uuid4(), workspace_id=self.fixture.other.id, idempotency_key=uuid4())
        with self.assertRaises(IntegrityError):
            self.db.execute(LegalCorrection.__table__.insert().values(**values))
        self.db.rollback()
        row.corrected_text = "SYNTHETIC overwrite"
        with self.assertRaisesRegex(ValueError, "immutable"):
            self.db.flush()
        self.db.rollback()

    def test_quarantine_blocks_new_corrections_and_decisions(self):
        from app.services.legal_extraction import ExtractionBlocked
        proposal = self.propose()
        version = self.db.get(DocumentVersion, self.received.version_id)
        version.status = "quarantined"
        self.db.commit()
        with self.assertRaises(ExtractionBlocked):
            self.propose(self.request.model_copy(update={"idempotency_key": uuid4()}))
        with self.assertRaises(ExtractionBlocked):
            self.decide(proposal)

    def test_review_revocation_before_response_rolls_back_pending_decision(self):
        from app.db.models.legal_scope import WorkspaceMembership
        proposal = self.propose()
        real_audit = corrections.append_event
        def revoke(*args, **kwargs):
            result = real_audit(*args, **kwargs)
            self.db.execute(update(WorkspaceMembership).where(WorkspaceMembership.workspace_id == self.fixture.ws.id,
                WorkspaceMembership.user_id == self.fixture.bob.id).values(role="analyst"))
            return result
        with patch.object(corrections, "append_event", side_effect=revoke), self.assertRaises(LegalAccessDenied):
            self.decide(proposal)
        self.db.rollback()
        self.assertEqual(list(self.db.scalars(select(LegalCorrectionDecision))), [])


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not selected")
class LegalCorrectionPostgresTests(LegalCorrectionTests):
    make_engine = provisioning_fixture.LegalProvisioningPostgresTests.make_engine


if __name__ == "__main__":
    unittest.main()
