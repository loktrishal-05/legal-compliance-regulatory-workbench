"""Real cookie/terms/origin help endpoint; no workspace/model/authority input accepted."""
import os
import unittest
import test_legal_scope_api as fixtures
import test_legal_scope_help as help_fixture


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable API runtime not selected")
class HelpApiTests(unittest.TestCase):
    def setUp(self):
        from app.api.routes.legal_help import router
        self.fixture = fixtures.LegalScopeApiTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.client = self.fixture.client
        self.client.app.include_router(router)
        self.client.app.state.legal_help_service = help_fixture.HelpTests().service()

    def test_session_terms_origin_extras_and_per_user_rate_boundary(self):
        response = self.client.post("/v1/help/chat", json={"question": "How do I upload a document?"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "degraded")
        self.assertTrue(response.json()["citations"])
        self.assertEqual(response.headers["cache-control"], "no-store")
        for field in ("workspace_id", "document_id", "runtime", "model", "accepted"):
            self.assertEqual(self.client.post("/v1/help/chat", json={"question": "How do I upload?", field: "forged"}).status_code, 422)
        self.assertEqual(self.client.post("/v1/help/chat", json={"question": "How do I upload?"},
            headers={"Origin": "https://untrusted.invalid"}).status_code, 403)
        for _ in range(9):
            self.assertEqual(self.client.post("/v1/help/chat", json={"question": "How do I upload?"}).status_code, 200)
        self.assertEqual(self.client.post("/v1/help/chat", json={"question": "How do I upload?"}).status_code, 429)
        self.fixture.fixture.actor.terms_version = "old"
        self.fixture.fixture.db.commit()
        self.assertEqual(self.client.post("/v1/help/chat", json={"question": "How do I upload?"}).status_code, 403)
        self.client.cookies.clear()
        self.assertEqual(self.client.post("/v1/help/chat", json={"question": "How do I upload?"}).status_code, 401)
