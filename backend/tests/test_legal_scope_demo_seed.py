"""Demo seed: refuses without LEGAL_DEMO_MODE/passwords; seeding twice is idempotent (migrated PostgreSQL)."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from scripts.legal_demo_seed import ROLES, SeedRefused, passwords_from_env

GOOD = {"LEGAL_DEMO_MODE": "true", **{f"DEMO_{role.upper()}_PASSWORD": f"synthetic-{role}-pass-123" for role in ROLES}}


class DemoSeedGuardTests(unittest.TestCase):
    def test_refuses_without_flag_or_passwords(self):
        with self.assertRaises(SeedRefused):
            passwords_from_env({k: v for k, v in GOOD.items() if k != "LEGAL_DEMO_MODE"})
        with self.assertRaises(SeedRefused):
            passwords_from_env({**GOOD, "LEGAL_DEMO_MODE": "false"})
        with self.assertRaises(SeedRefused):
            passwords_from_env({**GOOD, "DEMO_AUDITOR_PASSWORD": "short"})
        self.assertEqual(set(passwords_from_env(GOOD)), set(ROLES))


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not selected")
class DemoSeedPostgresTests(unittest.TestCase):
    def setUp(self):
        from alembic import command
        from alembic.config import Config
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import Session
        from app.core.config import settings
        from scripts.validate_legal_migrations import disposable_url
        admin = create_engine(disposable_url(), connect_args={"connect_timeout": 5})
        schema = "legal_seed_" + uuid4().hex
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
        self.engine = create_engine(url, connect_args={"connect_timeout": 5})
        self.addCleanup(self.engine.dispose)
        self.db = Session(self.engine, expire_on_commit=False)
        self.addCleanup(self.db.close)
        self.root = Path(tempfile.mkdtemp(prefix="legal-seed-"))

    def counts(self):
        from sqlalchemy import func, select
        from app.db.models import AuditEvent, Document
        from app.db.models.legal_review import LegalReview
        return tuple(self.db.scalar(select(func.count()).select_from(m)) for m in (Document, LegalReview, AuditEvent))

    def test_seed_through_real_services_then_idempotent(self):
        from sqlalchemy import select
        from app.db.models import User
        from app.db.models.legal_obligations import LegalNotification, LegalObligation, LegalTask
        from app.services.legal_dashboard import dashboard
        from scripts.legal_demo_seed import seed
        first = seed(self.db, data_root=self.root, passwords=passwords_from_env(GOOD), terms="1.0")
        self.assertEqual((first["status"], first["contracts"]), ("seeded", 2))
        self.assertTrue({"satisfied", "insufficient_evidence"} <= set(first["assessment_states"].values()), first["assessment_states"])
        self.assertEqual(self.db.get(LegalObligation, first["obligation_id"]).status, "active")
        self.assertTrue(self.db.scalars(select(LegalTask)).all())
        self.assertTrue(self.db.scalars(select(LegalNotification)).all())
        before = self.counts()
        self.assertEqual(seed(self.db, data_root=self.root, passwords=passwords_from_env(GOOD), terms="1.0"),
                         {"status": "already_seeded"})
        self.assertEqual(self.counts(), before)
        owner = self.db.scalar(select(User).where(User.username == "demo-owner"))
        view = dashboard(self.db, actor_id=owner.id, workspace_id=first["workspace_id"], current_terms_version="1.0")
        self.assertGreaterEqual(view["assessments_stale"], 1)
        self.assertEqual(sum(w["count"] for w in view["obligations_due"]["weeks"]), 1)


if __name__ == "__main__":
    unittest.main()
