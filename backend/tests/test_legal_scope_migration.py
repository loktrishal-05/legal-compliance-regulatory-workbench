"""Execute the new migration in RAM; compile PostgreSQL SQL without connecting."""
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch
from uuid import uuid4

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, event, insert, MetaData, select

from app.db.base import Base
from app.db.models import Document, User
from app.db.models.legal_scope import Organization


BACKEND = Path(__file__).resolve().parents[1]


def migration():
    spec = importlib.util.spec_from_file_location("legal_scope_migration", BACKEND / "alembic/versions/0019_legal_scope.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LegalScopeMigrationTests(unittest.TestCase):
    def test_disposable_guard_rejects_private_or_ambiguous_targets(self):
        from scripts.validate_legal_migrations import disposable_url
        for value in ("", "postgresql+psycopg://postgres:secret@localhost:55432/legal_compliance_workbench",
                      "postgresql+psycopg://legal_core_test:x@postgres:5432/private",
                      "postgresql+psycopg://legal_core_test:x@postgres:5432/legal_core_test?options=bad"):
            with self.subTest(target=value), patch.dict("os.environ", {"LEGAL_TEST_DATABASE_URL": value}):
                with self.assertRaises(ValueError):
                    disposable_url()

    def test_migration_matches_registered_models_and_preserves_legacy_document(self):
        engine = create_engine("sqlite:///:memory:")
        self.addCleanup(engine.dispose)
        event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
        Base.metadata.create_all(engine, tables=[User.__table__, Document.__table__])
        with engine.begin() as conn:
            document_id = uuid4()
            conn.execute(insert(Document).values(id=document_id, filename="synthetic legacy.txt",
                document_type="manual", source_path="synthetic/never-read", classification="confidential",
                checksum="b" * 64))
            context = MigrationContext.configure(conn, opts={"target_metadata": Base.metadata})
            with patch.object(migration_module := migration(), "op", Operations(context)):
                migration_module.upgrade()
            target = MetaData(naming_convention=Base.metadata.naming_convention)
            for table in Base.metadata.tables.values():
                if (table.name.startswith("legal_") and table.name not in {"legal_extractions", "legal_source_spans", "legal_corrections", "legal_correction_decisions"}) or table.name in {"users", "documents"}:
                    table.to_metadata(target)
            self.assertEqual(compare_metadata(context, target), [])
            self.assertEqual(conn.scalar(select(Document.checksum).where(Document.id == document_id)), "b" * 64)
            self.assertEqual(conn.scalar(select(Organization.id)), None)
            self.assertEqual(conn.exec_driver_sql("SELECT COUNT(*) FROM legal_document_scopes").scalar(), 0)

    def test_actual_head_and_postgres_sql_are_additive(self):
        config = Config()
        config.set_main_option("script_location", str(BACKEND / "alembic"))
        script = ScriptDirectory.from_config(config)
        self.assertEqual(script.get_heads(), ["0025_legal_corrections"])
        module = migration()
        self.assertEqual(module.down_revision, "0018_terms_acceptance")
        output = io.StringIO()
        context = MigrationContext.configure(dialect_name="postgresql", opts={
            "as_sql": True, "output_buffer": output, "target_metadata": Base.metadata,
        })
        with patch.object(module, "op", Operations(context)):
            module.upgrade()
        sql = output.getvalue()
        self.assertEqual(sql.count("CREATE TABLE legal_"), 7)
        for statement in ("DROP", "ALTER TABLE", "UPDATE ", "DELETE ", "INSERT "):
            self.assertNotIn(statement, sql)
        self.assertIn("FOREIGN KEY(organization_id, workspace_id, document_id)", sql)
        self.assertIn("REFERENCES legal_document_scopes", sql)
        self.assertIn("ck_legal_workspace_memberships_role", sql)


if __name__ == "__main__":
    unittest.main()
