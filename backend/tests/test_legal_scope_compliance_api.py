"""Compliance HTTP API on disposable PostgreSQL: real cookies/origin guard, six-state results over HTTP
(insufficient_evidence, satisfied, unsatisfied here; all six evaluator states in test_legal_scope_compliance_snapshot),
evidence expiry -> stale current projection, and uniform cross-tenant denial."""
from datetime import datetime, timedelta, timezone
import os
import time
import unittest
from unittest.mock import patch
from uuid import uuid4

SIX = {"satisfied", "partially_satisfied", "unsatisfied", "insufficient_evidence", "not_applicable", "needs_review"}
UNAVAILABLE = {"detail": {"code": "legal_resource_unavailable"}}


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not selected")
class ComplianceApiTests(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient
        from app.core.config import settings
        from app.core.security import hash_session_token
        from app.db.base import Base
        from app.db.models import AuthSession, User
        import test_legal_scope_authz_matrix as matrix
        import test_legal_scope_compliance_persistence as compliance
        import test_legal_scope_provisioning as provisioning
        c = self.c = compliance.CompliancePersistenceTests()
        c.make_engine = provisioning.LegalProvisioningPostgresTests.make_engine.__get__(c)
        c.setUp()
        self.addCleanup(c.doCleanups)
        self.db, self.f = c.db, c.fixture
        Base.metadata.create_all(self.f.engine, tables=[AuthSession.__table__])
        now = datetime.now(timezone.utc)
        self.dave = User(id=uuid4(), username="synthetic-dave", role="requester", terms_version="1.0",
                         terms_accepted_at=now)
        self.db.add(self.dave)
        self.db.commit()
        self.f.grant(self.dave, role="analyst", admin=self.f.bob, ws=self.f.other)
        self.tokens = {}
        for name, user in (("alice", self.f.alice), ("dave", self.dave)):
            token = f"synthetic-compliance-{name}-{uuid4().hex}"
            self.db.add(AuthSession(user_id=user.id, token_hash=hash_session_token(token),
                                    expires_at=now + timedelta(hours=1)))
            self.tokens[name] = token
        self.db.commit()
        app, _ = matrix.build_app(self.f.engine)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.cookie = settings.session_cookie_name
        self.base = f"/v1/workspaces/{self.f.ws.id}/compliance"
        root = patch.object(settings, "data_root", self.f.root)
        root.start()
        self.addCleanup(root.stop)

    def call(self, who, method, path, **kw):
        self.client.cookies.set(self.cookie, self.tokens[who])
        return self.client.request(method, self.base + path, **kw)

    def assess(self):
        response = self.call("alice", "POST", "/assessments", json={
            "requirement_id": str(self.c.requirement.id), "applicability_id": str(self.c.applicability.id)})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertIn(response.json()["status"], SIX)
        return response.json()

    def evidence(self, years, expires_in):
        from app.db.models import legal_compliance as m
        now = datetime.now(timezone.utc)
        evidence = self.call("alice", "POST", "/evidence", json={"title": f"Synthetic proof {years}"}).json()
        version = self.call("alice", "POST", "/evidence-versions", json={
            "evidence_id": evidence["id"], "document_id": str(self.c.version.document_id),
            "version_id": str(self.c.version.version_id), "observed_at": now.isoformat(),
            "valid_from": now.isoformat(), "expires_at": (now + expires_in).isoformat(),
            "facts": {"retention_years": years}, "span_ids": [str(s) for s in self.spans]})
        self.assertEqual(version.status_code, 201, version.text)
        self.assertEqual(version.json()["review_state"], "not_approved")
        mapping = self.call("alice", "POST", "/mappings", json={"requirement_id": str(self.c.requirement.id),
            "control_id": str(self.c.control.id), "evidence_version_id": version.json()["id"]})
        self.assertEqual(mapping.status_code, 201, mapping.text)
        self.c.base.review(self.db.get(m.EvidenceVersion, version.json()["id"]), "evidence_acceptance")
        return version.json()

    def test_states_expiry_to_stale_and_lists(self):
        from app.services import legal_compliance
        self.spans = self.c.prepare_graph()
        self.assertEqual(self.assess()["status"], "insufficient_evidence")
        self.evidence(7, timedelta(seconds=3))
        satisfied = self.assess()
        self.assertEqual(satisfied["status"], "satisfied")
        fresh = self.call("alice", "GET", f"/assessments/{satisfied['id']}/current").json()
        self.assertNotEqual(fresh["current"].get("freshness"), "stale")
        time.sleep(3.2)
        legal_compliance.scan_expiry(self.db, datetime.now(timezone.utc))
        self.db.commit()
        stale = self.call("alice", "GET", f"/assessments/{satisfied['id']}/current").json()
        self.assertEqual(stale["current"]["freshness"], "stale")
        self.assertEqual(stale["assessment"]["status"], "satisfied")  # stored snapshot never rewritten
        listed = self.call("alice", "GET", "/assessments").json()
        self.assertEqual(len(listed["items"]), 2)
        self.assertFalse({"total", "count"} & listed.keys())

    def test_failing_evidence_is_unsatisfied_and_impact_is_scoped(self):
        self.spans = self.c.prepare_graph()
        self.evidence(3, timedelta(days=30))
        self.assertEqual(self.assess()["status"], "unsatisfied")
        impact = self.call("alice", "GET", "/impact", params={"changed_id": str(self.c.control.id)})
        self.assertEqual(impact.status_code, 200, impact.text)
        self.assertTrue(impact.json()["paths"])

    def test_cross_tenant_and_unknown_ids_are_uniform_404(self):
        self.spans = self.c.prepare_graph()
        assessment = self.assess()
        for method, path, kw in (("GET", "/requirements", {}), ("GET", f"/assessments/{assessment['id']}/current", {}),
                                 ("GET", "/impact", {"params": {"changed_id": str(self.c.control.id)}}),
                                 ("POST", "/evidence", {"json": {"title": "Synthetic intrusion"}})):
            with self.subTest(path=path):
                response = self.call("dave", method, path, **kw)
                self.assertEqual((response.status_code, response.json()), (404, UNAVAILABLE))
        unknown = self.call("alice", "GET", f"/assessments/{uuid4()}/current")
        self.assertEqual((unknown.status_code, unknown.json()), (404, UNAVAILABLE))
        forged = self.call("alice", "POST", "/assessments", json={"requirement_id": str(self.c.requirement.id),
            "applicability_id": str(self.c.applicability.id), "status": "satisfied"})
        self.assertEqual(forged.status_code, 422)  # client cannot choose the state


if __name__ == "__main__":
    unittest.main()
