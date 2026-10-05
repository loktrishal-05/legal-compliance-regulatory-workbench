"""Terms enforcement through real session cookies, without identity overrides."""
from copy import deepcopy
from unittest.mock import patch
import unittest

from sqlalchemy import select
from app.core.config import settings
from app.db.models import AuditEvent, User, VerifiedKnowledge
from app.services import accounts, terms
from app.services.audit import verify_chain
import test_phase_f_auth


class TermsTests(unittest.TestCase):
    def setUp(self):
        self.f = test_phase_f_auth.AccountsTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.client, self.db, self.user = self.f.client, self.f.db, self.f.user
        VerifiedKnowledge.__table__.create(self.f.engine)
        self.payload = {"version": "1.0", "acknowledgements": {key: True for key in terms.ACKNOWLEDGEMENTS}}

    def accept(self, payload=None, **kwargs):
        return self.client.post("/auth/terms/accept", json=self.payload if payload is None else payload, **kwargs)

    def events(self):
        return self.db.scalars(select(AuditEvent).where(AuditEvent.event_type == "TERMS_ACCEPTED")).all()

    def test_first_login_requires_acceptance_and_session_functions_remain_available(self):
        self.f.login()
        current = self.client.get("/auth/terms/current")
        self.assertEqual(current.status_code, 200)
        self.assertEqual(current.headers["cache-control"], "no-store")
        self.assertTrue(current.json()["requires_acceptance"])
        self.assertIsNone(current.json()["accepted_at"])
        self.assertEqual([a["text"] for a in current.json()["acknowledgements"]], list(terms.ACKNOWLEDGEMENTS.values()))
        self.assertEqual(self.client.get("/auth/me").status_code, 200)
        self.assertEqual(self.client.get("/auth/sessions").status_code, 200)
        self.assertEqual(self.client.post("/auth/logout").status_code, 200)
        self.assertEqual(self.client.get("/auth/me").status_code, 401)
        self.assertEqual(self.events(), [])

    def test_every_checkbox_is_required_and_strictly_boolean_true(self):
        self.f.login()
        for key in terms.ACKNOWLEDGEMENTS:
            for value in (False, None, 1, "true", [], {}):
                body = deepcopy(self.payload)
                body["acknowledgements"][key] = value
                with self.subTest(key=key, value=value):
                    self.assertEqual(self.accept(body).status_code, 422)
            body = deepcopy(self.payload)
            del body["acknowledgements"][key]
            self.assertEqual(self.accept(body).status_code, 422)
        self.assertEqual(self.events(), [])
        self.assertIsNone(self.user.terms_version)

    def test_acceptance_is_audited_persistent_idempotent_and_account_bound(self):
        self.f.login()
        response = self.accept(headers={"X-Forwarded-For": "203.0.113.9", "Host": "forged-host"})
        self.assertEqual(response.status_code, 200, response.text)
        accepted = response.json()
        self.assertEqual(accepted["version"], "1.0")
        self.assertTrue(accepted["accepted_at"])
        event = self.events()[0]
        self.assertEqual(event.actor_id, self.user.id)
        self.assertEqual(event.payload["version"], "1.0")
        self.assertEqual(event.payload["request_host"], "testclient")
        self.assertEqual(event.payload["acknowledgements"], self.payload["acknowledgements"])
        self.assertTrue(verify_chain(self.db)["valid"])
        self.assertEqual(self.accept().json(), accepted)
        self.assertEqual(len(self.events()), 1)
        self.db.expire_all()
        current = self.client.get("/auth/terms/current").json()
        self.assertFalse(current["requires_acceptance"])
        self.assertEqual(current["accepted_at"], accepted["accepted_at"])
        self.client.post("/auth/logout")
        self.f.login()
        self.assertFalse(self.client.get("/auth/terms/current").json()["requires_acceptance"])
        self.assertEqual(self.client.get("/verified-knowledge").status_code, 200)
        other = User(username="another-person", password_hash=self.user.password_hash)
        self.db.add(other); self.db.commit()
        self.f.login(username=other.username)
        self.assertTrue(self.client.get("/auth/terms/current").json()["requires_acceptance"])
        self.assertEqual(self.client.get("/verified-knowledge").status_code, 403)

    def test_version_change_requires_explicit_reacceptance(self):
        self.f.login(); self.assertEqual(self.accept().status_code, 200)
        with patch.object(settings, "current_terms_version", "1.1"):
            self.assertTrue(self.client.get("/auth/terms/current").json()["requires_acceptance"])
            self.assertEqual(self.client.get("/verified-knowledge").status_code, 403)
            self.assertEqual(self.accept().status_code, 409)
            body = {**self.payload, "version": "1.1"}
            self.assertEqual(self.accept(body).json()["version"], "1.1")
            self.assertFalse(self.client.get("/auth/terms/current").json()["requires_acceptance"])
        self.assertEqual([e.payload["version"] for e in self.events()], ["1.0", "1.1"])

    def test_unauthenticated_or_forged_identity_cannot_accept(self):
        self.assertEqual(self.accept().status_code, 401)
        self.assertEqual(self.client.get("/auth/terms/current").status_code, 401)
        self.f.login()
        for field in ("user_id", "accepted_at", "role", "request_host"):
            self.assertEqual(self.accept({**self.payload, field: str(self.f.admin.id)}).status_code, 422)
        body = deepcopy(self.payload); body["acknowledgements"]["extra"] = True
        self.assertEqual(self.accept(body).status_code, 422)
        self.assertEqual(self.client.get("/auth/terms/accept").status_code, 405)
        self.assertEqual(self.events(), [])

    def test_protected_routes_cannot_be_bypassed_by_url_or_role(self):
        self.user.role = "admin"; self.db.commit(); self.f.login()
        for path in ("/executions", "/approvals", "/bi/operational", "/documents/pid", "/equipment",
                     "/sensors/channels?equipment_tag=P-101", "/maintenance/history", "/audit/log",
                     "/verified-knowledge", "/knowledge-gaps", "/admin/users"):
            with self.subTest(path=path):
                response = self.client.get(path, headers={"Referer": "http://testserver/app"})
                self.assertEqual(response.status_code, 403, response.text)
                self.assertEqual(response.json()["detail"]["code"], "terms_acceptance_required")
        self.assertEqual(self.client.post("/query", json={"query": "Review a pump"}).status_code, 403)

    def test_origin_csrf_and_revoked_sessions(self):
        self.f.login()
        self.assertEqual(self.accept(headers={"Origin": "https://outside.invalid"}).status_code, 403)
        self.client.headers.pop("Origin")
        self.assertEqual(self.accept(headers={"Sec-Fetch-Site": "cross-site"}).status_code, 403)
        self.assertEqual(self.events(), [])
        self.assertEqual(self.client.post("/auth/sessions/revoke-all").status_code, 200)
        self.assertEqual(self.accept().status_code, 401)

    def test_audit_failure_rolls_back_acceptance_and_keeps_gate_closed(self):
        self.f.login()
        with patch.object(accounts, "event", side_effect=RuntimeError("audit unavailable")):
            with self.assertRaises(RuntimeError):
                self.accept()
        self.db.expire_all()
        self.assertIsNone(self.user.terms_version)
        self.assertIsNone(self.user.terms_accepted_at)
        self.assertEqual(self.events(), [])
        self.assertEqual(self.client.get("/verified-knowledge").status_code, 403)


@unittest.skipUnless(__import__("os").environ.get("WORKBENCH_TEST_POSTGRES") == "1", "Real PostgreSQL required")
class TermsPostgreSQLTests(unittest.TestCase):
    def test_upgrade_preserves_users_and_concurrent_acceptance_is_atomic(self):
        from concurrent.futures import ThreadPoolExecutor
        from pathlib import Path
        from threading import Barrier
        from uuid import uuid4
        from alembic import command
        from alembic.config import Config
        from sqlalchemy import create_engine, text
        from sqlalchemy.engine import make_url
        from sqlalchemy.exc import DBAPIError
        from sqlalchemy.orm import Session
        from app.schemas.auth import TermsAcceptance

        schema = "test_terms_" + uuid4().hex
        admin = create_engine(settings.database_url)
        with admin.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        def cleanup():
            with admin.begin() as connection:
                connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            admin.dispose()
        self.addCleanup(cleanup)
        url = make_url(settings.database_url).update_query_dict({"options": f"-csearch_path={schema}"})
        engine = create_engine(url); self.addCleanup(engine.dispose)
        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        user_id = uuid4()
        with patch.object(settings, "database_url", url.render_as_string(hide_password=False)):
            command.upgrade(config, "0017_accounts_recovery")
            with engine.begin() as connection:
                connection.execute(text("INSERT INTO users (id, username, role) VALUES (:id, 'legacy', 'requester')"), {"id": user_id})
            command.upgrade(config, "head")
            command.check(config)
            # A history-free downgrade is reversible; migration 0017 itself stays untouched.
            command.downgrade(config, "0017_accounts_recovery")
            command.upgrade(config, "head")
            command.check(config)
        with Session(engine) as db:
            user = db.get(User, user_id)
            self.assertIsNone(user.terms_version)
            self.assertIsNone(user.terms_accepted_at)
            self.assertEqual(user.username, "legacy")
        payload = TermsAcceptance(version=settings.current_terms_version,
                                  acknowledgements={key: True for key in terms.ACKNOWLEDGEMENTS})
        barrier = Barrier(2)
        def worker(_):
            with Session(engine) as db:
                user = db.get(User, user_id)
                barrier.wait(timeout=10)
                return terms.accept(db, user, payload, "127.0.0.1")
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, range(2)))
        self.assertEqual(results[0], results[1])
        with Session(engine) as db:
            self.assertEqual(len(db.scalars(select(AuditEvent).where(AuditEvent.event_type == "TERMS_ACCEPTED")).all()), 1)
            self.assertTrue(verify_chain(db)["valid"])
        with patch.object(settings, "database_url", url.render_as_string(hide_password=False)), self.assertRaises(DBAPIError):
            command.downgrade(config, "0017_accounts_recovery")
