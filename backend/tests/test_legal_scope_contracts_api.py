"""Real cookie/terms/middleware HTTP contract-summary-assistant journeys on migrated PostgreSQL."""
from datetime import datetime, timedelta, timezone
import os
import unittest
from uuid import uuid4
from sqlalchemy import update
from app.db.models.legal_scope import DocumentAccess
import test_legal_scope_api as api_fixture
import test_legal_scope_contracts_persistence as fixtures


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable API runtime not selected")
class ContractApiTests(unittest.TestCase):
    def setUp(self):
        from app.api.routes.legal_contracts import router
        from app.api.routes.legal_review import router as reviews
        from app.core.config import settings
        from app.core.security import hash_session_token
        from app.db.models import AuthSession
        self.api = api_fixture.LegalScopeApiTests()
        self.api.setUp()
        self.addCleanup(self.api.doCleanups)
        self.client = self.api.client
        self.client.app.include_router(router)
        self.client.app.include_router(reviews)
        self.fixture = fixtures.ContractPersistenceTests()
        self.fixture.make_engine = lambda: self.api.fixture.engine
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.db = self.fixture.db
        f = self.fixture.fixture
        for label, user in (("alice", f.alice), ("bob", f.bob)):
            self.db.add(AuthSession(user_id=user.id, token_hash=hash_session_token("synthetic-b-" + label),
                expires_at=datetime.now(timezone.utc)+timedelta(hours=1)))
        self.db.commit()
        self.client.cookies.set(settings.session_cookie_name, "synthetic-b-alice")
        self.prefix = f"/v1/workspaces/{f.ws.id}"
        self.body = {"document_id": str(self.fixture.source.document_id), "version_id": str(self.fixture.source.version_id), "title": "Synthetic MSA"}

    def test_contract_analysis_lists_summary_review_and_exports(self):
        response = self.client.post(self.prefix + "/contracts", json=self.body)
        self.assertEqual(response.status_code, 201, response.text)
        result = response.json()
        path = self.prefix + f"/contracts/{result['contract_id']}/versions/{result['contract_version_id']}/analysis"
        analysis = self.client.post(path, json={})
        self.assertEqual(analysis.status_code, 201, analysis.text)
        self.assertEqual(len(analysis.json()["clauses"]), 6)
        self.assertEqual(len(self.client.get(self.prefix + "/clauses").json()["items"]), 6)
        self.assertEqual(len(self.client.get(self.prefix + "/obligation-proposals").json()["items"]), 3)
        summary = self.client.post(self.prefix + "/summaries", json={"sources": [dict(self.body, title="unused") | {}]})
        self.assertEqual(summary.status_code, 422)
        summary = self.client.post(self.prefix + "/summaries", json={"sources": [{k:v for k,v in self.body.items() if k != "title"}], "profile": "executive", "audience": "business"})
        self.assertEqual(summary.status_code, 201, summary.text)
        value = summary.json()
        export_path = self.prefix + f"/summaries/{value['summary_id']}/export"
        self.assertEqual(self.client.get(export_path, params={"format": "json"}).status_code, 409)
        f = self.fixture.fixture
        f.grant(f.bob, role="legal_reviewer")
        for op in ("read", "review_legal"):
            self.db.add(DocumentAccess(document_id=self.fixture.source.document_id, organization_id=f.ws.organization_id,
                workspace_id=f.ws.id, user_id=f.bob.id, operation=op))
        self.db.commit()
        self.client.cookies.set("workbench_session", "synthetic-b-bob")
        approved = self.client.post(self.prefix + f"/reviews/{value['review_id']}/decisions", json={"decision": "approve", "rationale": "Synthetic independent review"})
        self.assertEqual(approved.status_code, 201, approved.text)
        self.client.cookies.set("workbench_session", "synthetic-b-alice")
        for format in ("json", "pdf", "docx"):
            exported = self.client.get(export_path, params={"format": format})
            self.assertEqual(exported.status_code, 200, exported.text[:100] if format == "json" else "binary")
            self.assertEqual(exported.headers["cache-control"], "no-store")
        self.assertEqual(self.client.get(path).status_code, 200)

    def test_session_origin_authority_extras_unknown_and_revoked_denial(self):
        self.assertEqual(self.client.post(self.prefix + "/contracts", json=self.body,
            headers={"Origin": "https://untrusted.invalid"}).status_code, 403)
        self.assertEqual(self.client.post(self.prefix + "/contracts", json=self.body | {"accepted": True}).status_code, 422)
        unknown = self.client.get(self.prefix + f"/summaries/{uuid4()}")
        self.assertEqual(unknown.status_code, 404)
        self.assertEqual(unknown.json(), {"detail": {"code": "legal_resource_unavailable"}})
        self.client.cookies.clear()
        self.assertEqual(self.client.get(self.prefix + "/contracts").status_code, 401)

    def test_http_assistant_conversation_and_revocation(self):
        conversation = self.client.post(self.prefix + "/conversations", json={})
        self.assertEqual(conversation.status_code, 201, conversation.text)
        cid = conversation.json()["conversation_id"]
        answer = self.client.post(self.prefix + "/assistant/questions", json={"question": "invoice", "conversation_id": cid})
        self.assertEqual(answer.status_code, 201, answer.text)
        self.assertEqual(answer.json()["status"], "qualified")
        self.assertEqual(len(self.client.get(self.prefix + f"/conversations/{cid}").json()["messages"]), 1)
        self.db.execute(update(DocumentAccess).where(DocumentAccess.user_id == self.fixture.args["actor_id"]).values(is_active=False))
        self.db.commit()
        denied = self.client.get(self.prefix + f"/conversations/{cid}")
        self.assertEqual(denied.status_code, 404)
        self.assertEqual(self.client.delete(self.prefix + f"/conversations/{cid}").status_code, 200)

    def test_version_redline_collision_and_source_revocation_http(self):
        initial = self.client.post(self.prefix + "/contracts", json=self.body).json()
        f = self.fixture.fixture
        second = f.prepare(b"1. Payment\nBuyer shall pay within 15 days of invoice, provided the invoice is valid.\n", filename="second.txt")
        f.process(second)
        linked = self.client.post(self.prefix + f"/contracts/{initial['contract_id']}/versions",
            json={"document_id": str(second.document_id), "version_id": str(second.version_id)})
        self.assertEqual(linked.status_code, 201, linked.text)
        diff = self.client.get(self.prefix + f"/contracts/{initial['contract_id']}/redline",
            params={"from": initial["contract_version_id"], "to": linked.json()["contract_version_id"]})
        self.assertEqual(diff.status_code, 200, diff.text)
        self.assertTrue(diff.json()["changes"])
        other = self.client.post(self.prefix + "/contracts", json={"document_id": str(second.document_id),
            "version_id": str(second.version_id), "title": "Synthetic second"}).json()
        request = {"left_contract_id": initial["contract_id"], "left_version_id": initial["contract_version_id"],
            "right_contract_id": other["contract_id"], "right_version_id": other["contract_version_id"]}
        collision = self.client.post(self.prefix + "/contract-findings/collisions", json=request)
        self.assertEqual(collision.status_code, 201, collision.text)
        self.assertEqual(len(collision.json()["finding_ids"]), 1)
        self.db.execute(update(DocumentAccess).where(DocumentAccess.document_id == second.document_id).values(is_active=False))
        self.db.commit()
        findings = self.client.get(self.prefix + "/contract-findings")
        self.assertEqual(findings.json()["items"], [])
        analysis = self.client.get(self.prefix + f"/contracts/{initial['contract_id']}/versions/{initial['contract_version_id']}/analysis")
        self.assertEqual(analysis.json()["findings"], [])


if __name__ == "__main__":
    unittest.main()
