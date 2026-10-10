"""Step 9 HTTP authorization matrix over EVERY legal route (agents A/B/C) on migrated disposable PostgreSQL.

Real session cookies, real origin guard/validation handler from app/main.py, all `app.api.routes.legal_*`
routers. Roles: analyst with grants, workspace admin without grant, legal reviewer, business owner,
auditor, other-tenant member, terms-not-accepted member. Asserts uniform 404 / 403, no 2xx for
outsiders, no granted-document leakage to members without grants, and no totals on list responses.
"""
import ast
from datetime import datetime, timedelta, timezone
import importlib
import os
from pathlib import Path
import pkgutil
import re
import unittest
from unittest.mock import patch
from uuid import uuid4

UNAVAILABLE = {"detail": {"code": "legal_resource_unavailable"}}
BACKEND = Path(__file__).resolve().parents[1]


def build_app(engine):
    from fastapi import FastAPI
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse
    from sqlalchemy.orm import Session
    from urllib.parse import urlsplit
    import app.api.routes as routes
    from app.core.config import settings
    from app.db.session import get_db
    app = FastAPI()
    tree = ast.parse((BACKEND / "app/main.py").read_text(encoding="utf-8"))
    functions = [node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)
                 and node.name in {"browser_origin_guard", "validation_error"}]
    for node in functions:
        node.decorator_list = []
    namespace = {"settings": settings, "JSONResponse": JSONResponse, "urlsplit": urlsplit}
    exec(compile(ast.Module(body=functions, type_ignores=[]), "app/main.py", "exec"), namespace)
    app.middleware("http")(namespace["browser_origin_guard"])
    app.add_exception_handler(RequestValidationError, namespace["validation_error"])
    modules = sorted(m.name for m in pkgutil.iter_modules(routes.__path__) if m.name.startswith("legal_"))
    routers = [importlib.import_module(f"app.api.routes.{name}").router for name in modules]
    for router in routers:
        app.include_router(router)

    def isolated_db():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = isolated_db
    return app, routers


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable API runtime not explicitly selected")
class LegalAuthorizationMatrixTests(unittest.TestCase):
    def setUp(self):
        from alembic import command
        from alembic.config import Config
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine, text
        from app.core.config import settings
        from app.core.security import hash_session_token
        from app.db.models import AuthSession, User
        from scripts.validate_legal_migrations import disposable_url
        import test_legal_scope_extraction as extraction_fixture

        admin = create_engine(disposable_url(), connect_args={"connect_timeout": 5})
        schema = "legal_matrix_" + uuid4().hex
        with admin.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))

        def cleanup():
            with admin.begin() as conn:
                conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            admin.dispose()
        self.addCleanup(cleanup)
        url = disposable_url().update_query_dict({"options": "-csearch_path=" + schema})
        with patch.object(settings, "database_url", url.render_as_string(hide_password=False)):
            command.upgrade(Config(str(BACKEND / "alembic.ini")), "head")
        self.engine = create_engine(url, connect_args={"connect_timeout": 5})
        self.addCleanup(self.engine.dispose)
        f = self.f = extraction_fixture.LegalExtractionTests()
        f.make_engine = lambda: self.engine
        f.setUp()
        self.addCleanup(f.doCleanups)
        self.db = f.db
        self.received = f.prepare()
        f.process(self.received)
        now = datetime.now(timezone.utc)

        def user(name, platform="requester", terms="1.0"):
            row = User(id=uuid4(), username=f"synthetic-{name}", role=platform, terms_version=terms,
                       terms_accepted_at=now)
            self.db.add(row)
            self.db.commit()
            return row
        self.erin, self.frank, self.dave = user("erin"), user("frank"), user("dave")
        self.gina = user("gina")
        f.grant(f.bob, role="legal_reviewer")
        f.grant(self.erin, role="business_owner")
        f.grant(self.frank, role="auditor")
        f.grant(self.gina, role="analyst")
        f.grant(self.dave, role="analyst", admin=f.bob, ws=f.other)
        self.gina.terms_version = "0.9-old"  # membership exists, current terms not accepted
        self.db.commit()
        self.tokens = {}
        for name, row in {"analyst": f.alice, "admin_no_grant": f.admin, "reviewer": f.bob, "business_owner": self.erin,
                          "auditor": self.frank, "other_tenant": self.dave, "terms_missing": self.gina}.items():
            token = f"synthetic-matrix-{name}-{uuid4().hex}"
            self.db.add(AuthSession(user_id=row.id, token_hash=hash_session_token(token),
                                    expires_at=now + timedelta(hours=1)))
            self.tokens[name] = token
        self.db.commit()
        self.app, self.routers = build_app(self.engine)
        data_root = patch.object(settings, "data_root", f.root)
        data_root.start()
        self.addCleanup(data_root.stop)
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)
        self.cookie = settings.session_cookie_name
        self.ws = f.ws.id
        self.secret_markers = [str(self.received.document_id), "Party A shall pay"]

    def call(self, role, method, path, **kw):
        self.client.cookies.set(self.cookie, self.tokens[role])
        return self.client.request(method, path, **kw)

    def routes(self):
        for route in (route for router in self.routers for route in router.routes):
            if getattr(route, "path", "").startswith("/v1/workspaces/{workspace_id}"):
                for method in sorted(route.methods - {"HEAD", "OPTIONS"}):
                    yield method, route.path

    def concrete(self, path, workspace_id):
        return re.sub(r"\{[a-z_]+\}", lambda m: str(workspace_id) if m.group(0) == "{workspace_id}" else str(uuid4()),
                      path)

    def test_every_legal_route_is_uniformly_unavailable_to_outsiders(self):
        routes = list(self.routes())
        self.assertGreater(len(routes), 15)
        for method, template in routes:
            path = self.concrete(template, self.ws)
            for role in ("other_tenant", "terms_missing"):
                with self.subTest(role=role, method=method, path=template):
                    response = self.call(role, method, path, params={"q": "Party", "as_of": "2026-01-01"},
                                         json={} if method in {"POST", "PATCH", "PUT"} else None)
                    self.assertLess(response.status_code, 500, response.text[:300])
                    self.assertNotIn(response.status_code, range(200, 300), response.text[:300])
                    if role == "terms_missing":
                        self.assertEqual(response.status_code, 403)
                    elif response.status_code == 404:
                        self.assertEqual(response.json(), UNAVAILABLE)
                    for marker in self.secret_markers:
                        self.assertNotIn(marker, response.text)

    def test_unknown_ids_are_uniform_404_for_authorized_members(self):
        for method, template in self.routes():
            if method != "GET" or template.count("{") < 2:
                continue
            with self.subTest(path=template):
                response = self.call("analyst", "GET", self.concrete(template, self.ws),
                                     params={"q": "Party", "as_of": "2026-01-01"})
                self.assertIn(response.status_code, (404, 422), response.text[:300])
                if response.status_code == 404:
                    self.assertEqual(response.json(), UNAVAILABLE)

    def test_members_without_grants_see_no_document_content_or_counts(self):
        lists = [t for m, t in self.routes() if m == "GET" and t.count("{") == 1]
        self.assertIn("/v1/workspaces/{workspace_id}/documents", lists)
        for template in lists:
            for role in ("admin_no_grant", "reviewer", "business_owner", "auditor"):
                with self.subTest(role=role, path=template):
                    response = self.call(role, "GET", self.concrete(template, self.ws),
                                         params={"q": "Party", "as_of": "2026-01-01"})
                    self.assertLess(response.status_code, 500, response.text[:300])
                    for marker in self.secret_markers:
                        self.assertNotIn(marker, response.text)
                    if response.status_code == 200 and isinstance(response.json(), dict):
                        self.assertFalse({"total", "count", "total_count"} & response.json().keys())

    def test_granted_analyst_positive_paths_for_agent_a_routes(self):
        base = f"/v1/workspaces/{self.ws}"
        doc, version = self.received.document_id, self.received.version_id
        listing = self.call("analyst", "GET", f"{base}/documents").json()
        self.assertEqual([d["document_id"] for d in listing["items"]], [str(doc)])
        self.assertNotIn("total", listing)
        self.assertEqual(len(self.call("analyst", "GET", f"{base}/documents/{doc}/versions").json()["items"]), 1)
        spans = self.call("analyst", "GET", f"{base}/documents/{doc}/versions/{version}/spans").json()
        self.assertIn("Party A shall pay", spans["items"][0]["quote"])
        found = self.call("analyst", "GET", f"{base}/search", params={"q": "Party pay"}).json()
        self.assertEqual((found["mode"], found["items"][0]["document_id"]), ("postgres_fulltext", str(doc)))
        original = self.call("analyst", "GET", f"{base}/documents/{doc}/versions/{version}/original")
        self.assertEqual(original.status_code, 200)
        self.assertEqual(original.headers["x-content-type-options"], "nosniff")
        self.assertTrue(original.headers["content-disposition"].startswith("attachment;"))
        job = self.call("analyst", "POST", f"{base}/documents/{doc}/versions/{version}/jobs",
                        json={"operation": "extract", "idempotency_key": "matrix-job"})
        self.assertEqual(job.status_code, 202, job.text)
        self.assertEqual(self.call("analyst", "GET", f"{base}/jobs/{job.json()['job_id']}").json()["state"], "queued")
        self.assertEqual(self.call("other_tenant", "GET", f"{base}/jobs/{job.json()['job_id']}").json(), UNAVAILABLE)
        projection = self.call("analyst", "GET", f"{base}/documents/{doc}/versions/{version}/projection").json()
        self.assertEqual(projection["label"], "corrected_projection_not_original")
        reviews = self.call("analyst", "GET", f"{base}/reviews")
        self.assertEqual((reviews.status_code, reviews.json()), (200, []))
        mine = self.call("analyst", "GET", "/v1/workspaces").json()["items"]
        self.assertEqual([w["workspace_id"] for w in mine], [str(self.ws)])
        theirs = self.call("other_tenant", "GET", "/v1/workspaces").json()["items"]
        self.assertEqual([w["workspace_id"] for w in theirs], [str(self.f.other.id)])
        self.assertEqual(self.call("terms_missing", "GET", "/v1/workspaces").status_code, 403)


if __name__ == "__main__":
    unittest.main()
