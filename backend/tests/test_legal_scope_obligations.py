"""Step 6/7: accepted obligations, deterministic deadlines, exactly-once timers, tasks, remediation, exceptions,
comments, audit snapshots and evidence packs. SYNTHETIC tenants and documents only."""
from datetime import datetime, timedelta, timezone
import hashlib
import os
import unittest
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import select, update

from app.db.base import Base
from app.db.models import User
from app.db.models import legal_obligations as models
from app.db.models.legal_jobs import LegalJob, LegalRegionTranscription
from app.db.models.legal_review import LegalReview
from app.db.models.legal_scope import DocumentAccess
from app.services import legal_audit_export as audit_export
from app.services import legal_events, legal_obligations as ob, legal_review, legal_scheduler
from app.services.legal_policy import LegalAccessDenied
import test_legal_scope_extraction as extraction_fixture
import test_legal_scope_reviews as review_fixture

TERMS = "1.0"
OBLIGATION_TABLES = [m.__table__ for m in (models.LegalObligation, models.LegalDeadlineOccurrence, models.LegalTask,
    models.LegalTaskDependency, models.LegalRemediation, models.LegalException, models.LegalNotification,
    models.LegalDispatchReceipt, models.LegalComment, models.LegalEvidencePack)]
UTC = timezone.utc


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


class ObligationFixture(unittest.TestCase):
    make_engine = extraction_fixture.LegalExtractionTests.make_engine

    def setUp(self):
        f = self.f = extraction_fixture.LegalExtractionTests()
        f.make_engine = self.make_engine
        f.setUp()
        self.addCleanup(f.doCleanups)
        self.db = f.db
        Base.metadata.create_all(f.engine, tables=review_fixture.WORKFLOW_TABLES + OBLIGATION_TABLES + [
            LegalJob.__table__, LegalRegionTranscription.__table__])
        self.received = f.prepare()
        f.process(self.received)
        now = datetime.now(UTC)
        users = {}
        for name, platform in (("carol", "reviewer"), ("erin", "requester"), ("frank", "requester")):
            users[name] = User(id=uuid4(), username=f"synthetic-{name}", role=platform, terms_version=TERMS,
                               terms_accepted_at=now)
            self.db.add(users[name])
        self.db.commit()
        self.carol, self.erin, self.frank = users["carol"], users["erin"], users["frank"]
        f.grant(f.bob, role="legal_reviewer")
        f.grant(self.carol, role="compliance_reviewer")
        f.grant(self.erin, role="business_owner")
        f.grant(self.frank, role="auditor")
        for user in (f.bob, self.carol, self.erin, self.frank):
            self.db.add(DocumentAccess(document_id=self.received.document_id, organization_id=f.ws.organization_id,
                                       workspace_id=f.ws.id, user_id=user.id, operation="read"))
        self.db.commit()
        self.ws = f.ws.id
        self.now = datetime.now(UTC)
        for name in ("contract_obligation", "compliance_finding"):
            self.addCleanup(self.restore_target, name, legal_review._TARGETS.get(name))
        legal_review.register_target("contract_obligation", on_approve=self.emit_obligation)
        legal_review.register_target("compliance_finding", operation="review_compliance", on_approve=lambda db, r:
            legal_events.emit(db, workspace_id=r.workspace_id, event_type="legal.compliance.finding_accepted",
                              payload={"finding_id": str(r.target_id), "assessment_id": None},
                              idempotency_key=str(r.target_id)))

    @staticmethod
    def restore_target(name, original):
        if original is None:
            legal_review._TARGETS.pop(name, None)
        else:
            legal_review._TARGETS[name] = original

    def emit_obligation(self, db, review):  # stands in for agent B's approved proposal hand-off
        legal_events.emit(db, workspace_id=review.workspace_id, event_type="legal.contract.obligation_accepted",
            idempotency_key=f"contract-obligation:{review.target_id}", payload={
                "proposal_id": str(review.target_id), "proposal_sha256": review.target_revision_sha256,
                "review_id": str(review.id), "requester_id": str(review.requester_id),
                "document_id": str(self.received.document_id), "version_id": str(self.received.version_id),
                "source_sha256": "a" * 64, "actor": "Party A", "action": "pay Party B",
                "obligation_type": "duty", "trigger": "invoice", "conditions": [],
                "original_deadline_phrase": "within 30 days of invoice", "uncertainties": ["invoice date unknown"],
                "citations": [{"span_id": str(uuid4())}]})

    def approve(self, target_type, target_id=None, revision="r1", reviewer=None):
        target_id = target_id or uuid4()
        review = legal_review.submit(self.db, workspace_id=self.ws, target_type=target_type, target_id=target_id,
            target_revision_sha256=sha(revision), requester_id=self.f.alice.id,
            idempotency_key=f"{target_type}:{target_id}", current_terms_version=TERMS)
        self.db.commit()
        legal_review.decide(self.db, workspace_id=self.ws, review_id=review.id, reviewer_id=(reviewer or self.f.bob).id,
                            decision="approve", rationale="Synthetic independent review", current_terms_version=TERMS)
        self.db.commit()
        return target_id

    def dispatch(self):
        return legal_events.dispatch_due(self.db, worker_id="synthetic", now=self.now)

    def obligation(self):
        target = self.approve("contract_obligation")
        self.dispatch()
        return self.db.scalar(select(models.LegalObligation).where(models.LegalObligation.proposal_id == target))

    def confirm(self, row, tz="Europe/London", due="2026-12-01", **kw):
        result = ob.confirm_deadline(self.db, actor_id=kw.pop("actor", self.f.bob).id, workspace_id=self.ws,
            obligation_id=row.id, timezone_name=tz, due_local=due, owner_id=kw.pop("owner", self.erin).id,
            current_terms_version=TERMS, **kw)
        self.db.commit()
        return result

    def notifications(self, user):
        return ob.list_notifications(self.db, actor_id=user.id, workspace_id=self.ws, current_terms_version=TERMS)


class ObligationTests(ObligationFixture):
    def test_only_independently_accepted_obligations_are_created_and_dates_stay_unconfirmed(self):
        row = self.obligation()
        self.assertEqual((row.status, row.due_at, row.original_deadline_phrase),
                         ("needs_confirmation", None, "within 30 days of invoice"))
        task = self.db.scalars(select(models.LegalTask)).one()
        self.assertEqual((task.kind, task.source_id), ("obligation", row.id))
        self.dispatch()
        self.assertEqual(len(self.db.scalars(select(models.LegalObligation)).all()), 1)  # idempotent
        forged = legal_events.emit(self.db, workspace_id=self.ws, event_type="legal.contract.obligation_accepted",
            idempotency_key="forged", payload={"proposal_id": str(uuid4()), "proposal_sha256": "b" * 64})
        self.db.commit()
        for step in range(6):
            legal_events.dispatch_due(self.db, worker_id="w", now=self.now + timedelta(hours=step))
        self.db.refresh(forged)
        self.assertEqual((forged.status, forged.last_error_code), ("dead_letter", "ObligationConflict"))

    def test_confirmation_requires_reviewer_timezone_and_unambiguous_local_time(self):
        row = self.obligation()
        for kwargs, code in (({"tz": None}, "timezone_required"), ({"tz": "Mars/Base"}, "timezone_unknown"),
                             ({"tz": "America/New_York", "due": "2026-03-08T02:30:00"}, "local_time_nonexistent"),
                             ({"tz": "America/New_York", "due": "2026-11-01T01:30:00"}, "local_time_ambiguous"),
                             ({"recurrence_rule": "FREQ=HOURLY;COUNT=2"}, "recurrence_rule_unsupported")):
            with self.subTest(code=code), self.assertRaises(ob.ObligationConflict) as caught:
                self.confirm(row, **kwargs)
            self.assertEqual(str(caught.exception), code)
            self.db.rollback()
        with self.assertRaises(LegalAccessDenied):  # analyst cannot confirm legal date semantics
            self.confirm(row, actor=self.f.alice)
        self.db.rollback()
        self.assertEqual(self.db.get(models.LegalObligation, row.id).status, "needs_confirmation")

    def test_date_only_dst_and_leap_year_rules(self):
        row = self.confirm(self.obligation(), tz="America/New_York", due="2026-03-08")
        self.assertTrue(row.date_only)
        self.assertEqual(ob._aware(row.due_at), datetime(2026, 3, 9, 3, 59, 59, tzinfo=UTC))  # EDT, after the jump
        monthly = ob.occurrences(datetime(2026, 10, 15, 9, 0), ZoneInfo("Europe/Berlin"), "FREQ=MONTHLY;COUNT=2")
        self.assertEqual([d.hour for d in monthly], [7, 8])  # same 09:00 wall clock across the CET switch
        leap = ob.occurrences(datetime(2028, 2, 29, 12, 0), ZoneInfo("UTC"), "FREQ=YEARLY;COUNT=2")
        self.assertEqual([d.date().isoformat() for d in leap], ["2028-02-29", "2032-02-29"])  # skipped, not clamped
        ends = ob.occurrences(datetime(2026, 1, 31, 12, 0), ZoneInfo("UTC"), "FREQ=MONTHLY;COUNT=3")
        self.assertEqual([d.month for d in ends], [1, 3, 5])

    def test_timers_fire_exactly_once_and_catch_up_after_downtime(self):
        self.confirm(self.obligation(), tz="UTC", due="2026-12-01T12:00:00", notice_days=7)
        due = datetime(2026, 12, 1, 12, 0, tzinfo=UTC)
        self.assertEqual(ob.scan_deadlines(self.db, due - timedelta(days=8)), 0)
        self.assertEqual(ob.scan_deadlines(self.db, due - timedelta(days=6)), 1)
        self.db.commit()
        self.assertEqual(ob.scan_deadlines(self.db, due - timedelta(days=5)), 0)  # duplicate claim / restart
        self.assertEqual(ob.scan_deadlines(self.db, due + timedelta(hours=1)), 1)
        self.db.commit()
        self.assertEqual(ob.scan_deadlines(self.db, due + timedelta(days=30)), 0)
        kinds = sorted(n.kind for n in self.notifications(self.erin))
        self.assertEqual(kinds, ["obligation_assigned", "overdue_escalation", "reminder"])
        late = self.obligation()
        self.confirm(late, tz="UTC", due="2026-01-01T00:00:00", notice_days=3)
        result = legal_scheduler.run_due(self.db, datetime(2026, 6, 1, tzinfo=UTC), force=True)
        self.assertEqual(result["legal-deadlines"], 2)  # reminder + escalation caught up in one scan

    def test_tasks_cycles_reassignment_owner_progress_and_bulk_triage(self):
        row = self.confirm(self.obligation())
        task = self.db.scalar(select(models.LegalTask).where(models.LegalTask.source_id == row.id))
        other = ob._task(self.db, workspace_id=self.ws, organization_id=self.f.ws.organization_id,
                         kind="evidence_request", title="Synthetic evidence", source_type="synthetic", source_id=uuid4())
        self.db.commit()
        ob.update_task(self.db, actor_id=self.f.alice.id, workspace_id=self.ws, task_id=task.id,
                       add_dependency=other.id, current_terms_version=TERMS)
        self.db.commit()
        with self.assertRaises(ob.ObligationConflict):
            ob.update_task(self.db, actor_id=self.f.alice.id, workspace_id=self.ws, task_id=other.id,
                           add_dependency=task.id, current_terms_version=TERMS)
        self.db.rollback()
        ob.update_task(self.db, actor_id=self.erin.id, workspace_id=self.ws, task_id=task.id, status="in_progress",
                       current_terms_version=TERMS)
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):  # business owner cannot close or reassign
            ob.update_task(self.db, actor_id=self.erin.id, workspace_id=self.ws, task_id=task.id, status="done",
                           current_terms_version=TERMS)
        self.db.rollback()
        with self.assertRaises(ob.ObligationConflict):  # dependency still open
            ob.update_task(self.db, actor_id=self.f.alice.id, workspace_id=self.ws, task_id=task.id, status="done",
                           current_terms_version=TERMS)
        self.db.rollback()
        self.db.execute(update(DocumentAccess).where(DocumentAccess.user_id == self.carol.id).values(is_active=False))
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):  # reassignment to a user whose grant was revoked
            ob.update_task(self.db, actor_id=self.f.alice.id, workspace_id=self.ws, task_id=task.id,
                           owner_id=self.carol.id, current_terms_version=TERMS)
        self.db.rollback()
        results = ob.bulk_triage(self.db, actor_id=self.erin.id, workspace_id=self.ws,
                                 task_ids=[task.id, other.id, uuid4()], status="submitted", current_terms_version=TERMS)
        self.db.commit()
        self.assertEqual(list(results.values()), ["ok", "unavailable", "unavailable"])

    def test_remediation_needs_evidence_independent_review_and_failed_retest_reopens(self):
        finding = self.approve("compliance_finding", reviewer=self.carol)
        self.dispatch()
        remediation = self.db.scalars(select(models.LegalRemediation)).one()
        self.assertEqual(remediation.finding_id, finding)
        with self.assertRaises(ob.ObligationConflict):
            ob.update_task(self.db, actor_id=self.f.alice.id, workspace_id=self.ws, task_id=remediation.task_id,
                           status="done", current_terms_version=TERMS)
        self.db.rollback()
        with self.assertRaises(ob.ObligationConflict):
            ob.submit_closure(self.db, actor_id=self.f.alice.id, workspace_id=self.ws, remediation_id=remediation.id,
                              evidence=[], current_terms_version=TERMS)
        self.db.rollback()
        review = ob.submit_closure(self.db, actor_id=self.f.alice.id, workspace_id=self.ws,
            remediation_id=remediation.id, evidence=[{"evidence_id": str(uuid4())}], current_terms_version=TERMS)
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):  # a legal reviewer is not a compliance reviewer
            legal_review.decide(self.db, workspace_id=self.ws, review_id=review.id, reviewer_id=self.f.bob.id,
                                decision="approve", rationale="x", current_terms_version=TERMS)
        self.db.rollback()
        legal_review.decide(self.db, workspace_id=self.ws, review_id=review.id, reviewer_id=self.carol.id,
                            decision="approve", rationale="Synthetic closure check", current_terms_version=TERMS)
        self.db.commit()
        self.db.refresh(remediation)
        self.assertEqual(remediation.status, "closed")
        ob.record_retest(self.db, actor_id=self.carol.id, workspace_id=self.ws, remediation_id=remediation.id,
                         passed=False, current_terms_version=TERMS)
        self.db.commit()
        self.assertEqual((remediation.status, remediation.reopen_count), ("reopened", 1))
        again = ob.submit_closure(self.db, actor_id=self.f.alice.id, workspace_id=self.ws,
            remediation_id=remediation.id, evidence=[{"evidence_id": str(uuid4())}], current_terms_version=TERMS)
        self.db.commit()
        self.assertNotEqual(again.id, review.id)

    def test_exception_requires_expiry_review_and_expires(self):
        with self.assertRaises(ob.ObligationConflict):
            ob.propose_exception(self.db, actor_id=self.f.alice.id, workspace_id=self.ws, subject_type="finding",
                subject_id=uuid4(), rationale="Synthetic", expires_at=self.now - timedelta(days=1),
                current_terms_version=TERMS)
        self.db.rollback()
        row, review = ob.propose_exception(self.db, actor_id=self.f.alice.id, workspace_id=self.ws,
            subject_type="finding", subject_id=uuid4(), rationale="Synthetic accepted risk",
            expires_at=self.now + timedelta(days=30), current_terms_version=TERMS)
        self.db.commit()
        self.assertEqual(row.status, "proposed")
        legal_review.decide(self.db, workspace_id=self.ws, review_id=review.id, reviewer_id=self.carol.id,
                            decision="approve", rationale="Synthetic risk acceptance", current_terms_version=TERMS)
        self.db.commit()
        self.assertEqual(row.status, "active")
        self.assertEqual(ob.scan_exception_expiry(self.db, self.now + timedelta(days=31)), 1)
        self.db.commit()
        self.assertEqual(ob.scan_exception_expiry(self.db, self.now + timedelta(days=32)), 0)
        self.assertEqual(row.status, "expired")
        self.assertEqual(self.db.scalar(select(models.LegalTask.kind).where(models.LegalTask.source_id == row.id)),
                         "exception_expired")

    def test_comments_check_every_mention_recipient(self):
        row = self.confirm(self.obligation())
        outsider = User(id=uuid4(), username="synthetic-outsider", role="requester", terms_version=TERMS,
                        terms_accepted_at=self.now)
        self.db.add(outsider)
        self.db.commit()
        self.f.grant(outsider, role="viewer")
        with self.assertRaises(ob.ObligationConflict):
            ob.add_comment(self.db, actor_id=self.f.bob.id, workspace_id=self.ws, subject_type="obligation",
                           subject_id=row.id, body="Synthetic note", mentions=[outsider.id], current_terms_version=TERMS)
        self.db.rollback()
        comment = ob.add_comment(self.db, actor_id=self.f.bob.id, workspace_id=self.ws, subject_type="obligation",
            subject_id=row.id, body="Synthetic note", mentions=[self.erin.id], current_terms_version=TERMS)
        self.db.commit()
        self.assertIn("mention", [n.kind for n in self.notifications(self.erin)])
        with self.assertRaises(ValueError):
            comment.body = "edited"
            self.db.flush()
        self.db.rollback()
        with self.assertRaises(LegalAccessDenied):
            ob.list_comments(self.db, actor_id=outsider.id, workspace_id=self.ws, subject_type="obligation",
                             subject_id=row.id, current_terms_version=TERMS)


class AuditExportTests(ObligationFixture):
    def test_audit_scope_snapshot_and_evidence_pack_exclusions(self):
        before = datetime.now(UTC) - timedelta(seconds=1)
        target = self.approve("contract_obligation")
        self.dispatch()
        with self.assertRaises(LegalAccessDenied):  # analysts are not auditors
            audit_export.audit_events(self.db, actor_id=self.f.alice.id, workspace_id=self.ws,
                                      current_terms_version=TERMS)
        events = audit_export.audit_events(self.db, actor_id=self.frank.id, workspace_id=self.ws,
                                           current_terms_version=TERMS)
        self.assertTrue({"LEGAL_REVIEW_DECIDED", "LEGAL_ACTIVITY_RECORDED"} <= {e["event_type"] for e in events})
        self.assertTrue(all(e["payload"]["workspace_id"] == str(self.ws) for e in events))
        early = audit_export.snapshot(self.db, actor_id=self.frank.id, workspace_id=self.ws, as_of=before,
                                      current_terms_version=TERMS)
        self.assertEqual(early["reviews"], [])
        later = audit_export.snapshot(self.db, actor_id=self.frank.id, workspace_id=self.ws,
                                      as_of=datetime.now(UTC) + timedelta(seconds=1), current_terms_version=TERMS)
        self.assertEqual([r["state_as_of"] for r in later["reviews"]], ["approved"])
        self.assertIsNone(later["obligations"][0]["effective_due_at"])  # recorded, not yet effective
        review_id = self.db.scalar(select(LegalReview.id).where(LegalReview.target_id == target))
        foreign_doc = uuid4()
        pack = audit_export.create_evidence_pack(self.db, actor_id=self.frank.id, workspace_id=self.ws,
            document_ids=[self.received.document_id, foreign_doc], review_ids=[review_id, uuid4()],
            current_terms_version=TERMS)
        self.db.commit()
        out = audit_export.get_export(self.db, actor_id=self.frank.id, workspace_id=self.ws, export_id=pack.id,
                                      current_terms_version=TERMS)
        self.assertTrue(out["integrity_verified"])
        self.assertEqual([d["document_id"] for d in out["manifest"]["documents"]], [str(self.received.document_id)])
        self.assertEqual(len(out["manifest"]["reviews"]), 1)
        self.assertNotIn(str(foreign_doc), str(out))
        with self.assertRaises(LegalAccessDenied):  # neither creator nor auditor
            audit_export.get_export(self.db, actor_id=self.erin.id, workspace_id=self.ws, export_id=pack.id,
                                    current_terms_version=TERMS)
        self.db.rollback()
        with self.assertRaises(ValueError):
            pack.manifest_sha256 = "0" * 64
            self.db.flush()
        self.db.rollback()


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not selected")
class ObligationPostgresTests(ObligationTests):
    make_engine = extraction_fixture.LegalExtractionPostgresTests.make_engine


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not selected")
class AuditExportPostgresTests(AuditExportTests):
    make_engine = extraction_fixture.LegalExtractionPostgresTests.make_engine


if __name__ == "__main__":
    unittest.main()
