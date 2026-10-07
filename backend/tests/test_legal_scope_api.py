"""Scoped legal router + actual session deps/middleware on disposable PostgreSQL.

This bounded app deliberately excludes industrial/AI routes; it is not a full
app.main or model-runtime acceptance claim.
"""
import ast
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from uuid import uuid4


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable API runtime not explicitly selected")
class LegalScopeApiTests(unittest.TestCase):
    def setUp(self):
        from alembic import command
        from alembic.config import Config
        from fastapi import FastAPI
        from fastapi.exceptions import RequestValidationError
        from fastapi.responses import JSONResponse
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine, text
        from urllib.parse import urlsplit
        from app.core.config import settings
        from app.core.security import hash_session_token
        from app.db.models import AuthSession
        from app.db.session import get_db
        from app.api.routes.legal_scope import router
        from scripts.validate_legal_migrations import disposable_url
        import test_legal_scope

        admin = create_engine(disposable_url(), connect_args={"connect_timeout": 5})
        schema = "legal_api_" + uuid4().hex
        with admin.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        def cleanup():
            with admin.begin() as conn:
                conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            admin.dispose()
        self.addCleanup(cleanup)
        url = disposable_url().update_query_dict({"options": "-csearch_path=" + schema})
        with patch.object(settings, "database_url", url.render_as_string(hide_password=False)):
            command.upgrade(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head")
        engine = create_engine(url, connect_args={"connect_timeout": 5})
        self.fixture = test_legal_scope.LegalScopeTests()
        self.fixture.make_engine = lambda: engine
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.grant()
        token = "synthetic-legal-core-session-only"
        self.session = AuthSession(user_id=self.fixture.actor.id, token_hash=hash_session_token(token),
                                   expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
        self.fixture.db.add(self.session)
        self.fixture.db.commit()
        app = FastAPI()
        # Execute the real main.py functions without importing AI/native modules.
        tree = ast.parse((Path(__file__).resolve().parents[1] / "app/main.py").read_text(encoding="utf-8"))
        functions = [node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)
                     and node.name in {"browser_origin_guard", "validation_error"}]
        for node in functions:
            node.decorator_list = []
        namespace = {"settings": settings, "JSONResponse": JSONResponse, "urlsplit": urlsplit}
        exec(compile(ast.Module(body=functions, type_ignores=[]), "app/main.py", "exec"), namespace)
        app.middleware("http")(namespace["browser_origin_guard"])
        app.add_exception_handler(RequestValidationError, namespace["validation_error"])
        app.include_router(router)
        from sqlalchemy.orm import Session
        def isolated_db():
            with Session(engine) as db:
                yield db
        app.dependency_overrides[get_db] = isolated_db
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.client.cookies.set(settings.session_cookie_name, token)
        self.path = f"/v1/workspaces/{self.fixture.workspace.id}/documents/{self.fixture.document.id}"

    def test_authorized_metadata_has_no_paths_or_content_and_is_not_cached(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["classification"], "confidential")
        self.assertNotIn("source_path", response.json())
        self.assertNotIn("checksum", response.json())
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["referrer-policy"], "no-referrer")
        workspace = self.client.get(f"/v1/workspaces/{self.fixture.workspace.id}")
        self.assertEqual(workspace.json()["role"], "analyst")

    def test_unknown_denied_and_cross_workspace_resources_match_and_are_audited(self):
        from sqlalchemy import select, update
        from app.db.models import AuditEvent
        from app.db.models.legal_scope import DocumentAccess
        from app.services.audit import verify_chain
        unknown = self.client.get(f"/v1/workspaces/{self.fixture.workspace.id}/documents/{uuid4()}")
        foreign = self.client.get(f"/v1/workspaces/{self.fixture.other_workspace.id}/documents/{self.fixture.document.id}")
        self.fixture.db.execute(update(DocumentAccess).values(is_active=False))
        self.fixture.db.commit()
        denied = self.client.get(self.path)
        for response in (unknown, foreign, denied):
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), {"detail": {"code": "legal_resource_unavailable"}})
        events = list(self.fixture.db.scalars(select(AuditEvent)))
        self.assertEqual(len(events), 3)
        self.assertTrue(all(e.event_type == "SECURITY_POLICY_DENIED" for e in events))
        self.assertNotIn("synthetic.txt", str([e.payload for e in events]))
        self.assertTrue(verify_chain(self.fixture.db)["valid"])

    def test_upload_route_quarantines_bounds_rejects_and_denies(self):
        import tempfile
        from sqlalchemy import select
        from app.core.config import settings
        from app.db.models import AuditEvent
        from app.services import legal_intake
        upload = f"/v1/workspaces/{self.fixture.workspace.id}/documents"
        params = {"filename": "synthetic.txt", "document_type": "contract", "classification": "internal"}
        body = b"SYNTHETIC contract clause: payment within 30 days.\n"
        with patch.object(settings, "data_root", Path(tempfile.mkdtemp(prefix="legal-api-intake-"))):
            created = self.client.post(upload, params=params, content=body)
            self.assertEqual(created.status_code, 201)
            self.assertEqual((created.json()["status"], created.json()["quarantine_reasons"]),
                             ("quarantined", ["malware_scanner_not_configured"]))  # no scanner configured
            with patch.object(legal_intake, "MAX_BYTES", 8):
                self.assertEqual(self.client.post(upload, params=params, content=body).status_code, 413)
            rejected = self.client.post(upload, params={**params, "filename": "synthetic.pdf"}, content=body)
            self.assertEqual((rejected.status_code, rejected.json()), (422, {"detail": {"code": "type_mismatch"}}))
            self.assertEqual(self.client.post(upload, params=params, content=body,
                                              headers={"Origin": "https://untrusted.invalid"}).status_code, 403)
            foreign = self.client.post(f"/v1/workspaces/{self.fixture.other_workspace.id}/documents",
                                       params=params, content=b"other bytes\n")
            self.assertEqual((foreign.status_code, foreign.json()), (404, {"detail": {"code": "legal_resource_unavailable"}}))
        types = [e.event_type for e in self.fixture.db.scalars(select(AuditEvent).order_by(AuditEvent.sequence_number))]
        self.assertEqual(types, ["LEGAL_DOCUMENT_RECEIVED", "LEGAL_INTAKE_REJECTED", "SECURITY_POLICY_DENIED"])

    def test_real_session_terms_revocation_and_header_spoofing(self):
        self.client.cookies.clear()
        self.assertEqual(self.client.get(self.path, headers={"X-User-ID": str(self.fixture.actor.id),
                                                          "X-Role": "admin"}).status_code, 401)
        self.client.cookies.set("workbench_session", "synthetic-legal-core-session-only")
        self.fixture.actor.terms_version = "old"
        self.fixture.db.commit()
        self.assertEqual(self.client.get(self.path).status_code, 403)
        self.fixture.actor.terms_version = "1.0"
        self.session.revoked_at = datetime.now(timezone.utc)
        self.fixture.db.commit()
        self.assertEqual(self.client.get(self.path).status_code, 401)

    def test_extraction_and_source_api_scope_origin_and_quarantine(self):
        import tempfile
        from sqlalchemy import update
        from app.core.config import settings
        from app.db.models.legal_scope import DocumentAccess
        from app.services import legal_intake
        ws = self.fixture.workspace
        with patch.object(settings, "data_root", Path(tempfile.mkdtemp(prefix="legal-api-extraction-"))):
            received = legal_intake.receive(self.fixture.db, actor_id=self.fixture.actor.id, workspace_id=ws.id,
                filename="synthetic.txt", document_type="contract", classification="internal",
                data=b"SYNTHETIC contract payment within 30 days.\n", current_terms_version="1.0",
                data_root=settings.data_root, scanner=lambda data: (True, "synthetic-only"))
            self.fixture.db.add(DocumentAccess(document_id=received.document_id, organization_id=ws.organization_id,
                workspace_id=ws.id, user_id=self.fixture.actor.id, operation="propose"))
            self.fixture.db.commit()
            base = f"/v1/workspaces/{ws.id}/documents/{received.document_id}/versions/{received.version_id}"
            self.assertEqual(self.client.post(base + "/extractions", headers={"Origin": "https://untrusted.invalid"}).status_code, 403)
            response = self.client.post(base + "/extractions")
            self.assertEqual(response.status_code, 201)
            span = response.json()["span_ids"][0]
            source = self.client.get(base + "/spans/" + span)
            self.assertEqual(source.status_code, 200)
            self.assertEqual(source.json()["quote"], "SYNTHETIC contract payment within 30 days.\n")
            self.assertEqual(source.headers["cache-control"], "no-store")
            self.assertNotIn("source_path", source.json())
            replay = self.client.post(f"/v1/workspaces/{ws.id}/documents", content=b"SYNTHETIC contract payment within 30 days.\n",
                params={"filename": "synthetic.txt", "document_type": "contract", "classification": "internal"})
            self.assertEqual((replay.status_code, replay.json()["status"], replay.json()["duplicate"]), (201, "ready", True))
            self.assertEqual(self.client.get(base + "/spans/" + str(uuid4())).status_code, 404)
            self.fixture.db.execute(update(DocumentAccess).where(DocumentAccess.document_id == received.document_id)
                                    .values(is_active=False))
            self.fixture.db.commit()
            denied = self.client.get(base + "/spans/" + span)
            self.assertEqual(denied.status_code, 404)
            self.assertNotIn("SYNTHETIC contract", denied.text)
            quarantined = legal_intake.receive(self.fixture.db, actor_id=self.fixture.actor.id, workspace_id=ws.id,
                filename="quarantined.txt", document_type="contract", classification="internal",
                data=b"SYNTHETIC unscanned source.\n", current_terms_version="1.0", data_root=settings.data_root)
            self.fixture.db.add(DocumentAccess(document_id=quarantined.document_id, organization_id=ws.organization_id,
                workspace_id=ws.id, user_id=self.fixture.actor.id, operation="propose"))
            self.fixture.db.commit()
            blocked = self.client.post(f"/v1/workspaces/{ws.id}/documents/{quarantined.document_id}/versions/{quarantined.version_id}/extractions")
            self.assertEqual((blocked.status_code, blocked.json()), (409, {"detail": {"code": "document_quarantined"}}))

    def test_versioned_validation_does_not_echo_input_and_origin_guard_applies(self):
        response = self.client.get(self.path.replace(str(self.fixture.document.id), "private-invalid-id"))
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("input", response.json()["detail"][0])
        response = self.client.post(self.path, headers={"Origin": "https://untrusted.invalid"},
                                    json={"role": "admin"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(self.client.post(self.path).status_code, 405)  # no write/provisioning endpoint


if __name__ == "__main__":
    unittest.main()
