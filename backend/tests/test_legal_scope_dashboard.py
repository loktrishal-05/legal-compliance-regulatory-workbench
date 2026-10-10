"""Dashboard aggregates are permission-filtered: two tenants, an auditor with and without a source grant."""
from datetime import datetime, timedelta, timezone
import os
import unittest
from uuid import uuid4

from sqlalchemy import update

from app.db.base import Base
from app.db.models import User
from app.db.models.legal_scope import DocumentAccess
from app.services import legal_review
from app.services.legal_dashboard import dashboard
from app.services.legal_policy import LegalAccessDenied
import test_legal_scope_obligations as obligation_fixture

TERMS = "1.0"


class DashboardTests(obligation_fixture.ObligationFixture):
    def setUp(self):
        super().setUp()
        Base.metadata.create_all(self.f.engine, tables=[t for t in Base.metadata.sorted_tables
            if t.name.startswith(("legal_compliance_", "legal_regulatory_"))])

    def view(self, user, ws=None):
        return dashboard(self.db, actor_id=user.id, workspace_id=(ws or self.ws), current_terms_version=TERMS)

    def test_counts_only_what_the_caller_can_read(self):
        row = self.obligation()
        due = (datetime.now(timezone.utc) + timedelta(days=10)).strftime("%Y-%m-%dT09:00:00")
        self.confirm(row, tz="UTC", due=due)
        legal_review.submit(self.db, workspace_id=self.ws, target_type="contract_obligation", target_id=uuid4(),
            target_revision_sha256="b" * 64, requester_id=self.f.alice.id, idempotency_key="pending-1",
            current_terms_version=TERMS)
        self.db.commit()
        mine = self.view(self.f.alice)
        self.assertEqual(sum(mine["documents_by_status"].values()), 1)
        self.assertEqual(mine["reviews_pending_by_target"], {"contract_obligation": 1})
        self.assertEqual(sum(w["count"] for w in mine["obligations_due"]["weeks"]), 1)
        self.assertEqual(mine["tasks_by_status"], {"open": 1})
        self.assertEqual(set(mine["assessments_by_state"]), set(("satisfied", "partially_satisfied", "unsatisfied",
            "insufficient_evidence", "not_applicable", "needs_review")))
        auditor = self.view(self.frank)
        self.assertEqual(sum(auditor["documents_by_status"].values()), 1)
        self.db.execute(update(DocumentAccess).where(DocumentAccess.user_id == self.frank.id).values(is_active=False))
        self.db.commit()
        revoked = self.view(self.frank)  # no source grant -> no document, obligation or document-bound task counts
        self.assertEqual((revoked["documents_by_status"], revoked["tasks_by_status"]), ({}, {}))
        self.assertEqual(sum(w["count"] for w in revoked["obligations_due"]["weeks"]), 0)
        self.assertFalse({"total", "count"} & revoked.keys())

    def test_other_tenant_sees_nothing_and_cannot_query_this_workspace(self):
        self.obligation()
        dave = User(id=uuid4(), username="synthetic-dave", role="requester", terms_version=TERMS,
                    terms_accepted_at=datetime.now(timezone.utc))
        self.db.add(dave)
        self.db.commit()
        self.f.grant(dave, role="analyst", admin=self.f.bob, ws=self.f.other)
        theirs = self.view(dave, ws=self.f.other.id)
        self.assertEqual((theirs["documents_by_status"], theirs["reviews_pending_by_target"], theirs["tasks_by_status"]),
                         ({}, {}, {}))
        with self.assertRaises(LegalAccessDenied):
            self.view(dave)


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not selected")
class DashboardPostgresTests(DashboardTests):
    make_engine = obligation_fixture.ObligationPostgresTests.make_engine


if __name__ == "__main__":
    unittest.main()
