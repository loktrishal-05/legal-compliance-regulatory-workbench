"""Durable document jobs, worker crash/lease/retry semantics, blank-region transcription and projection."""
from datetime import datetime, timedelta, timezone
import hashlib
import os
import unittest
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import select, update

from app.db.base import Base
from app.db.models import DocumentVersion
from app.db.models.legal_correction import LegalCorrection, LegalCorrectionDecision
from app.db.models.legal_extraction import LegalExtraction, LegalSourceSpan
from app.db.models.legal_jobs import LegalJob, LegalRegionTranscription
from app.db.models.legal_review import LegalEvent
from app.db.models.legal_scope import DocumentAccess
from app.services import legal_jobs, legal_review
from app.services.legal_extraction import ExtractionBlocked, ParserFailed
from app.services.legal_policy import LegalAccessDenied
import test_legal_scope_extraction as extraction_fixture
import test_legal_scope_reviews as review_fixture

TERMS = "1.0"


class JobFixture(unittest.TestCase):
    make_engine = extraction_fixture.LegalExtractionTests.make_engine

    def setUp(self):
        self.fixture = extraction_fixture.LegalExtractionTests()
        self.fixture.make_engine = self.make_engine
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.db = self.fixture.db
        Base.metadata.create_all(self.fixture.engine, tables=review_fixture.WORKFLOW_TABLES + [
            LegalJob.__table__, LegalRegionTranscription.__table__, LegalCorrection.__table__,
            LegalCorrectionDecision.__table__])
        self.received = self.fixture.prepare()
        self.now = datetime.now(timezone.utc)

    def submit(self, key="job-1", operation="extract", actor=None):
        job = legal_jobs.submit(self.db, actor_id=(actor or self.fixture.alice).id, workspace_id=self.fixture.ws.id,
            document_id=self.received.document_id, version_id=self.received.version_id, operation=operation,
            idempotency_key=key, current_terms_version=TERMS)
        self.db.commit()
        return job

    def tick(self, minutes=0):
        return legal_jobs.run_once(self.db, worker_id="synthetic-worker", data_root=self.fixture.root,
                                   current_terms_version=TERMS, now=self.now + timedelta(minutes=minutes))

    def job(self, job_id):
        return self.db.scalar(select(LegalJob).where(LegalJob.id == job_id).execution_options(populate_existing=True))

    def events(self, event_type):
        return review_fixture.fixtures.LegalProvisioningTests.events(self.fixture, event_type)

    def extractions(self):
        return self.db.scalars(select(LegalExtraction)).all()


class LegalJobTests(JobFixture):
    def test_submit_run_persists_artifact_and_outbox_event_once(self):
        job = self.submit()
        self.assertEqual(job.state, "queued")
        self.assertEqual(self.tick()["jobs"], 1)
        done = self.job(job.id)
        self.assertEqual((done.state, done.attempts, done.failure_code), ("succeeded", 1, None))
        self.assertEqual([row.id for row in self.extractions()], [done.extraction_id])
        event = self.db.scalar(select(LegalEvent).where(LegalEvent.event_type == "legal.document.extracted"))
        self.assertEqual(event.payload["extraction_id"], str(done.extraction_id))
        self.assertEqual(self.tick(1)["jobs"], 0)
        self.assertEqual(len(self.events("LEGAL_DOCUMENT_EXTRACTED")), 1)

    def test_duplicate_submits_join_and_changed_retry_conflicts(self):
        first = self.submit()
        self.assertEqual(self.submit().id, first.id)
        self.assertEqual(self.submit(key="job-2").id, first.id)  # one active job per version/operation
        with self.assertRaises(legal_jobs.JobConflict):
            self.submit(operation="ocr")
        self.db.rollback()
        self.assertEqual(len(self.db.scalars(select(LegalJob)).all()), 1)

    def test_crash_before_persistence_is_reclaimed_after_lease_expiry(self):
        job = self.submit()
        claimed = legal_jobs.claim(self.db, worker_id="dies", now=self.now)  # worker dies holding the lease
        self.assertEqual(claimed.state, "running")
        self.assertEqual(self.tick(1)["jobs"], 0)  # lease still valid
        self.assertEqual(self.tick(11)["jobs"], 1)
        done = self.job(job.id)
        self.assertEqual((done.state, done.attempts), ("succeeded", 2))
        self.assertEqual(len(self.extractions()), 1)

    def test_crash_after_persistence_before_commit_rolls_back_then_retries_without_duplicate(self):
        job = self.submit()
        with patch("app.services.legal_events.emit", side_effect=RuntimeError("synthetic crash")):
            self.tick()
        self.assertEqual(self.extractions(), [])
        self.assertEqual((self.job(job.id).state, self.job(job.id).failure_code), ("queued", "RuntimeError"))
        self.tick(5)
        self.assertEqual(self.job(job.id).state, "succeeded")
        self.assertEqual(len(self.extractions()), 1)

    def test_artifact_committed_elsewhere_is_reused(self):
        job = self.submit()
        self.fixture.process(self.received)  # synchronous route path won the race
        self.tick()
        self.assertEqual(self.job(job.id).state, "succeeded")
        self.assertEqual(len(self.extractions()), 1)

    def test_permission_revoked_while_queued_blocks_release(self):
        job = self.submit()
        self.db.execute(update(DocumentAccess).where(DocumentAccess.operation == "propose").values(is_active=False))
        self.db.commit()
        self.tick()
        done = self.job(job.id)
        self.assertEqual((done.state, done.failure_code), ("failed", "actor_not_authorized"))
        self.assertEqual(self.extractions(), [])
        with self.assertRaises(LegalAccessDenied):  # other tenant cannot even read status
            legal_jobs.get(self.db, actor_id=self.fixture.bob.id, workspace_id=self.fixture.other.id, job_id=job.id,
                           current_terms_version=TERMS)

    def test_parser_failure_retries_then_dead_letters(self):
        job = self.submit()
        with patch("app.services.legal_extraction.run_parser", side_effect=ParserFailed("parser_failed")):
            for minute in (0, 10, 30, 60):
                self.tick(minute)
        done = self.job(job.id)
        self.assertEqual((done.state, done.attempts, done.failure_code), ("dead_letter", 3, "parser_failed"))
        self.assertEqual(len(self.events("LEGAL_EXTRACTION_FAILED")), 3)
        self.assertEqual(self.extractions(), [])

    def test_workspace_quota_applies_backpressure(self):
        with patch.object(legal_jobs, "MAX_ACTIVE_JOBS_PER_WORKSPACE", 0):
            with self.assertRaises(legal_jobs.JobQuotaExceeded):
                self.submit()
        self.db.rollback()

    def test_quarantined_version_cannot_queue(self):
        self.db.execute(update(DocumentVersion).values(status="quarantined"))
        self.db.commit()
        with self.assertRaises(ExtractionBlocked):
            self.submit()
        self.db.rollback()


class LegalTranscriptionProjectionTests(JobFixture):
    def setUp(self):
        super().setUp()
        self.artifact = self.fixture.process(self.received)
        self.fixture.grant(self.fixture.bob, role="legal_reviewer")
        self.db.add(DocumentAccess(document_id=self.received.document_id, organization_id=self.fixture.ws.organization_id,
            workspace_id=self.fixture.ws.id, user_id=self.fixture.bob.id, operation="read"))
        self.db.commit()

    def transcribe(self, key="region-1", text="SYNTHETIC handwritten margin note"):
        row = legal_jobs.transcribe_region(self.db, actor_id=self.fixture.alice.id, workspace_id=self.fixture.ws.id,
            document_id=self.received.document_id, version_id=self.received.version_id,
            extraction_id=self.artifact.extraction_id, page=1, bbox=[10.0, 20.0, 200.0, 60.0], text=text,
            rationale="Synthetic blank region", idempotency_key=key, current_terms_version=TERMS)
        self.db.commit()
        return row

    def projection(self):
        return legal_jobs.projection(self.db, actor_id=self.fixture.alice.id, workspace_id=self.fixture.ws.id,
            document_id=self.received.document_id, version_id=self.received.version_id, current_terms_version=TERMS)

    def test_blank_region_needs_independent_review_before_projection(self):
        row = self.transcribe()
        self.assertEqual(self.transcribe().id, row.id)
        with self.assertRaises(legal_jobs.JobConflict):
            self.transcribe(text="SYNTHETIC changed")
        self.db.rollback()
        self.assertEqual(self.projection()["manual_regions"], [])
        review = legal_review.submit(self.db, workspace_id=self.fixture.ws.id, target_type="region_transcription",
            target_id=row.id, target_revision_sha256=row.transcription_sha256, requester_id=self.fixture.alice.id,
            idempotency_key="review-region-1", current_terms_version=TERMS)
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):  # author cannot approve own transcription
            legal_review.decide(self.db, workspace_id=self.fixture.ws.id, review_id=review.id,
                reviewer_id=self.fixture.alice.id, decision="approve", rationale="self", current_terms_version=TERMS)
        self.db.rollback()
        legal_review.decide(self.db, workspace_id=self.fixture.ws.id, review_id=review.id,
            reviewer_id=self.fixture.bob.id, decision="approve", rationale="Synthetic check", current_terms_version=TERMS)
        self.db.commit()
        regions = self.projection()["manual_regions"]
        self.assertEqual([(r["page"], r["text"]) for r in regions], [(1, "SYNTHETIC handwritten margin note")])

    def test_projection_overlays_only_approved_corrections_and_keeps_original(self):
        span = self.db.get(LegalSourceSpan, self.artifact.span_ids[0])
        artifact = self.db.get(LegalExtraction, self.artifact.extraction_id)
        original_text = artifact.text
        quote = original_text[span.start:span.end]
        correction = LegalCorrection(id=uuid4(), organization_id=self.fixture.ws.organization_id,
            workspace_id=self.fixture.ws.id, span_id=span.id, extraction_id=artifact.id,
            actor_id=self.fixture.alice.id, idempotency_key=uuid4(),
            original_quote_sha256=hashlib.sha256(quote.encode()).hexdigest(), correction_sha256="c" * 64,
            corrected_text="SYNTHETIC corrected line", rationale="Synthetic")
        self.db.add(correction)
        self.db.commit()
        before = self.projection()
        self.assertNotIn("approved_correction", [s["kind"] for s in before["segments"]])
        self.db.add(LegalCorrectionDecision(id=uuid4(), organization_id=self.fixture.ws.organization_id,
            workspace_id=self.fixture.ws.id, correction_id=correction.id, correction_sha256="c" * 64,
            reviewer_id=self.fixture.bob.id, requester_id=self.fixture.alice.id, outcome="approved", rationale="ok"))
        self.db.commit()
        after = self.projection()
        overlay = [s for s in after["segments"] if s["kind"] == "approved_correction"]
        self.assertEqual([(s["text"], s["original_text"]) for s in overlay], [("SYNTHETIC corrected line", quote)])
        self.assertEqual(after["label"], "corrected_projection_not_original")
        self.assertEqual(self.db.get(LegalExtraction, artifact.id).text, original_text)
        self.assertEqual(after["original_text_sha256"], hashlib.sha256(original_text.encode()).hexdigest())


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not selected")
class LegalJobPostgresTests(LegalJobTests):
    make_engine = extraction_fixture.LegalExtractionPostgresTests.make_engine


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not selected")
class LegalTranscriptionProjectionPostgresTests(LegalTranscriptionProjectionTests):
    make_engine = extraction_fixture.LegalExtractionPostgresTests.make_engine


if __name__ == "__main__":
    unittest.main()
