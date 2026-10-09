"""Regulatory HTTP registry, real cookie/terms middleware and disposable migrations."""
import os
import unittest
from uuid import uuid4

import test_legal_scope_api as api_fixture


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable API runtime not selected")
class RegulatoryApiTests(unittest.TestCase):
    def setUp(self):
        from app.api.routes.legal_regulatory import router
        self.base = api_fixture.LegalScopeApiTests()
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        self.base.client.app.include_router(router)
        self.client = self.base.client
        self.workspace = self.base.fixture.workspace.id
        self.path = f"/v1/workspaces/{self.workspace}/regulatory"

    def test_registry_and_empty_lists_have_real_scoped_shapes(self):
        body = {"name": "SYNTHETIC authority", "jurisdiction": "SYNTHETIC", "authority_tier": "unverified",
                "owner_id": str(self.base.fixture.actor.id)}
        response = self.client.post(self.path + "/sources", json=body)
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["trust_state"], "proposed")
        self.assertEqual(response.headers["cache-control"], "no-store")
        listed = self.client.get(self.path + "/sources")
        self.assertEqual(listed.json()["items"][0]["review_state"], "not_approved")
        for resource in ("versions", "changes", "applicability", "watchlists", "campaigns"):
            response = self.client.get(self.path + "/" + resource)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json(), {"items": [], "has_more": False, "next_offset": None})

    def test_unknown_workspace_and_forged_state_are_denied(self):
        response = self.client.get(f"/v1/workspaces/{uuid4()}/regulatory/sources")
        self.assertEqual((response.status_code, response.json()),
                         (404, {"detail": {"code": "legal_resource_unavailable"}}))
        response = self.client.post(self.path + "/sources", json={"name": "SYNTHETIC", "jurisdiction": "SYNTHETIC",
            "owner_id": str(self.base.fixture.actor.id), "trust_state": "approved"})
        self.assertEqual(response.status_code, 422)
