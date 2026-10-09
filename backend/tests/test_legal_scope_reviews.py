"""Exact-revision independent reviews, transactional outbox and durable scans: SYNTHETIC tenants only."""
from datetime import datetime, timedelta, timezone
import hashlib
import os
import unittest
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.db.models import User
from app.db.models.legal_review import LegalEvent, LegalReview, LegalReviewDecision, LegalSchedulerScan
from app.services import legal_events, legal_review, legal_scheduler
from app.services import legal_provisioning as prov
from app.services.audit import AuditChainError
from app.services.legal_policy import LegalAccessDenied
import test_legal_scope_provisioning as fixtures

TERMS = fixtures.TERMS
WORKFLOW_TABLES = [LegalReview.__table__, LegalReviewDecision.__table__, LegalEvent.__table__,
                   LegalSchedulerScan.__table__]


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


class WorkflowFixture(unittest.TestCase):
    """Provisioned tenants plus a second independent reviewer (carol) and the workflow tables."""
    extra_tables = ()
    target_id = uuid4()
    make_engine = fixtures.LegalProvisioningTests.make_engine
    grant = fixtures.LegalProvisioningTests.grant
    events = fixtures.LegalProvisioningTests.events

    def setUp(self):
        fixtures.LegalProvisioningTests.setUp(self)
        Base.metadata.create_all(self.engine, tables=WORKFLOW_TABLES + list(self.extra_tables))
        self.carol = User(id=uuid4(), username="synthetic-carol", role="reviewer", terms_version=TERMS,
                          terms_accepted_at=datetime.now(timezone.utc))
        self.db.add(self.carol)
        self.db.commit()
        self.grant(self.alice, role="analyst")
        self.grant(self.bob, role="legal_reviewer")
        self.grant(self.carol, role="legal_reviewer")
        self.handled = []
        legal_review.register_target("synthetic_target", on_approve=lambda db, review: self.handled.append(review.id))
        legal_review.register_target("synthetic_compliance", operation="review_compliance")

    def submit(self, revision="rev-1", key=None, actor=None, target_id=None, target_type="synthetic_target", ws=None):
        review = legal_review.submit(self.db, workspace_id=(ws or self.ws).id, target_type=target_type,
            target_id=target_id or self.target_id, target_revision_sha256=sha(revision),
            requester_id=(actor or self.alice).id, idempotency_key=key or "key-" + revision, current_terms_version=TERMS)
        self.db.commit()
        return review

    def decide(self, review, decision="approve", actor=None, rationale="Synthetic independent review"):
        row = legal_review.decide(self.db, workspace_id=review.workspace_id, review_id=review.id,
            reviewer_id=(actor or self.bob).id, decision=decision, rationale=rationale, current_terms_version=TERMS)
        self.db.commit()
        return row

    def approved(self, revision="rev-1", target_id=None):
        return legal_review.is_approved(self.db, workspace_id=self.ws.id, target_type="synthetic_target",
            target_id=target_id or self.target_id, target_revision_sha256=sha(revision))


class LegalReviewTests(WorkflowFixture):
    def test_independent_approval_binds_exact_revision_and_runs_handler(self):
        review = self.submit()
        self.assertEqual(legal_review.status(self.db, review), "pending")
        self.decide(review)
        self.assertTrue(self.approved())
        self.assertFalse(self.approved("rev-2"))  # changed revision hash makes the approval inapplicable
        self.assertEqual(self.handled, [review.id])
        self.assertEqual(legal_review.status(self.db, review), "approved")
        self.assertEqual(len(self.events("LEGAL_REVIEW_DECIDED")), 1)
        self.assertEqual(self.events("LEGAL_REVIEW_REQUESTED")[0].payload["target_revision_sha256"], sha("rev-1"))

    def test_self_approval_denied_even_with_reviewer_role(self):
        review = self.submit()
        self.alice.role = "reviewer"
        self.db.commit()
        self.grant(self.alice, role="legal_reviewer")
        with self.assertRaises(LegalAccessDenied):
            self.decide(review, actor=self.alice)
        self.db.rollback()
        self.assertFalse(self.approved())

    def test_analyst_or_wrong_domain_reviewer_cannot_decide(self):
        review = self.submit()
        self.grant(self.carol, role="analyst")
        with self.assertRaises(LegalAccessDenied):
            self.decide(review, actor=self.carol)
        self.db.rollback()
        compliance = self.submit(target_type="synthetic_compliance", key="c1")
        with self.assertRaises(LegalAccessDenied):
            self.decide(compliance)  # bob is a legal reviewer, not a compliance reviewer
        self.db.rollback()

    def test_retry_is_idempotent_and_changed_content_conflicts(self):
        first = self.submit()
        self.assertEqual(self.submit().id, first.id)
        with self.assertRaises(legal_review.LegalReviewConflict):
            self.submit(revision="rev-2", key="key-rev-1")
        self.db.rollback()
        with self.assertRaises(legal_review.LegalReviewConflict):
            self.submit(key="another-key")  # same exact revision already under review
        self.db.rollback()
        decision = self.decide(first)
        self.assertEqual(self.decide(first).id, decision.id)
        with self.assertRaises(legal_review.LegalReviewConflict):
            self.decide(first, decision="reject")
        self.db.rollback()
        self.assertEqual(self.handled, [first.id])

    def test_concurrent_terminal_decisions_cannot_both_persist(self):
        review = self.submit()
        self.decide(review)
        with self.assertRaises(legal_review.LegalReviewConflict):
            self.decide(review, decision="reject", actor=self.carol)
        self.db.rollback()
        with self.assertRaises(IntegrityError):  # database boundary, bypassing the service lock
            self.db.execute(LegalReviewDecision.__table__.insert().values(id=uuid4(),
                organization_id=self.ws.organization_id, workspace_id=self.ws.id, review_id=review.id,
                requester_id=self.alice.id, reviewer_id=self.carol.id, decision="reject", rationale="x"))
        self.db.rollback()

    def test_escalation_never_approves_and_hands_off(self):
        review = self.submit()
        self.decide(review, decision="escalate", rationale="Synthetic material escalation")
        self.assertFalse(self.approved())
        self.assertEqual(legal_review.status(self.db, review), "escalated")
        self.assertEqual(self.handled, [])
        self.decide(review, actor=self.carol)
        self.assertTrue(self.approved())

    def test_request_changes_needs_successor_revision(self):
        review = self.submit()
        self.decide(review, decision="request_changes")
        self.assertEqual(legal_review.status(self.db, review), "changes_requested")
        successor = self.submit(revision="rev-2")
        self.decide(successor)
        self.assertFalse(self.approved("rev-1"))
        self.assertTrue(self.approved("rev-2"))

    def test_revoked_reviewer_and_other_tenant_are_denied(self):
        review = self.submit()
        prov.revoke_membership(self.db, admin_id=self.admin.id, workspace_id=self.ws.id, user_id=self.bob.id,
                               current_terms_version=TERMS)
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):
            self.decide(review)
        self.db.rollback()
        with self.assertRaises(LegalAccessDenied):  # bob administers the other tenant only
            legal_review.get(self.db, workspace_id=self.other.id, review_id=review.id, actor_id=self.bob.id,
                             current_terms_version=TERMS)
        self.db.rollback()

    def test_audit_or_handler_failure_rolls_back_decision(self):
        review = self.submit()
        with patch("app.services.legal_review.append_event", side_effect=AuditChainError("synthetic")):
            with self.assertRaises(AuditChainError):
                self.decide(review)
        self.db.rollback()
        legal_review.register_target("synthetic_target", on_approve=lambda db, r: 1 / 0)
        with self.assertRaises(ZeroDivisionError):
            self.decide(review)
        self.db.rollback()
        self.assertEqual(self.db.scalars(select(LegalReviewDecision)).all(), [])
        self.assertFalse(self.approved())

    def test_unregistered_target_and_immutability(self):
        with self.assertRaises(legal_review.LegalReviewConflict):
            self.submit(target_type="unknown_target")
        review = self.submit()
        review_row = self.db.get(LegalReview, review.id)
        review_row.target_revision_sha256 = sha("tampered")
        with self.assertRaises(ValueError):
            self.db.flush()
        self.db.rollback()


class LegalEventTests(WorkflowFixture):
    def emit(self, payload=None, key="evt-1", event_type="synthetic.event"):
        row = legal_events.emit(self.db, workspace_id=self.ws.id, event_type=event_type,
                                payload=payload or {"value": 1}, idempotency_key=key)
        self.db.commit()
        return row

    def test_emit_idempotent_and_changed_payload_conflicts(self):
        first = self.emit()
        self.assertEqual(self.emit().id, first.id)
        with self.assertRaises(legal_events.LegalEventConflict):
            self.emit({"value": 2})
        self.db.rollback()
        self.assertEqual(len(self.db.scalars(select(LegalEvent)).all()), 1)

    def test_dispatch_runs_handlers_once_and_retries_to_dead_letter(self):
        seen, failures = [], []
        legal_events.register_handler("synthetic.ok", lambda db, event: seen.append(event.payload["value"]))
        legal_events.register_handler("synthetic.fail", lambda db, event: failures.append(1) or 1 / 0)
        self.emit(event_type="synthetic.ok")
        failing = self.emit(event_type="synthetic.fail", key="evt-2")
        now = datetime.now(timezone.utc)
        self.assertEqual(legal_events.dispatch_due(self.db, worker_id="w1", now=now), 2)
        self.assertEqual(legal_events.dispatch_due(self.db, worker_id="w1", now=now), 0)  # backoff and done
        self.assertEqual(seen, [1])
        for step in range(1, 10):
            legal_events.dispatch_due(self.db, worker_id="w1", now=now + timedelta(hours=step))
        row = self.db.get(LegalEvent, failing.id)
        self.db.refresh(row)
        self.assertEqual((row.status, row.attempts, row.last_error_code), ("dead_letter", 5, "ZeroDivisionError"))
        self.assertEqual(len(failures), 5)
        legal_events._HANDLERS.pop("synthetic.ok")
        legal_events._HANDLERS.pop("synthetic.fail")


class LegalSchedulerTests(WorkflowFixture):
    def test_scan_runs_once_per_interval_and_records_receipts(self):
        calls = []
        legal_scheduler.register_scan("synthetic-scan", lambda db, now: calls.append(now) or 3)
        legal_scheduler.register_scan("synthetic-broken", lambda db, now: 1 / 0)
        self.addCleanup(legal_scheduler._SCANS.pop, "synthetic-scan")
        self.addCleanup(legal_scheduler._SCANS.pop, "synthetic-broken")
        now = datetime.now(timezone.utc)
        result = legal_scheduler.run_due(self.db, now)
        self.assertEqual(result["synthetic-scan"], 3)
        self.assertEqual(result["synthetic-broken"], "error:ZeroDivisionError")
        self.assertNotIn("synthetic-scan", legal_scheduler.run_due(self.db, now + timedelta(seconds=5)))
        legal_scheduler.run_due(self.db, now + timedelta(minutes=2))
        self.assertEqual(len(calls), 2)
        receipt = self.db.get(LegalSchedulerScan, "synthetic-scan")
        self.db.refresh(receipt)
        self.assertEqual((receipt.runs, receipt.last_count, receipt.last_error_code), (2, 3, None))


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not selected")
class LegalReviewPostgresTests(LegalReviewTests):
    make_engine = fixtures.LegalProvisioningPostgresTests.make_engine


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not selected")
class LegalEventPostgresTests(LegalEventTests):
    make_engine = fixtures.LegalProvisioningPostgresTests.make_engine


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not selected")
class LegalSchedulerPostgresTests(LegalSchedulerTests):
    make_engine = fixtures.LegalProvisioningPostgresTests.make_engine


if __name__ == "__main__":
    unittest.main()
