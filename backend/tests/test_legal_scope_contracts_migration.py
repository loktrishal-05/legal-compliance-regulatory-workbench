"""0028 owns B tables only; actual PostgreSQL immutability and schema parity."""
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from uuid import uuid4


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not selected")
class ContractMigrationTests(unittest.TestCase):
    def test_0028_tables_match_models_and_reject_update_delete_truncate(self):
        from alembic import command
        from alembic.config import Config
        from sqlalchemy import create_engine, inspect, text
        from sqlalchemy.exc import DBAPIError
        from app.core.config import settings
        from app.db.models.legal_contract import TABLES, MODELS
        from scripts.validate_legal_migrations import disposable_url
        admin = create_engine(disposable_url(), connect_args={"connect_timeout": 5})
        schema = "legal_b_migration_" + uuid4().hex
        with admin.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        def cleanup():
            with admin.begin() as conn:
                conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            admin.dispose()
        self.addCleanup(cleanup)
        url = disposable_url().update_query_dict({"options": "-csearch_path=" + schema})
        with patch.object(settings, "database_url", url.render_as_string(hide_password=False)):
            config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
            command.upgrade(config, "0028_legal_contracts")
            command.upgrade(config, "0028_legal_contracts")
        engine = create_engine(url)
        self.addCleanup(engine.dispose)
        inspector = inspect(engine)
        self.assertTrue(set(TABLES).issubset(inspector.get_table_names()))
        for model in MODELS:
            self.assertEqual({c.name for c in model.__table__.columns},
                {c["name"] for c in inspector.get_columns(model.__tablename__)})
            self.assertEqual({engine.dialect.identifier_preparer.format_constraint(c).strip('"') for c in model.__table__.constraints},
                {inspector.get_pk_constraint(model.__tablename__)["name"]} |
                {c["name"] for c in inspector.get_foreign_keys(model.__tablename__)} |
                {c["name"] for c in inspector.get_unique_constraints(model.__tablename__)} |
                {c["name"] for c in inspector.get_check_constraints(model.__tablename__)})
        for table in TABLES[:-1]:
            with engine.connect() as conn:
                with self.assertRaisesRegex(DBAPIError, "immutable"):
                    conn.execute(text(f'TRUNCATE "{table}" CASCADE'))
                conn.rollback()
        with engine.connect() as conn:
            triggers = conn.execute(text("SELECT tgname FROM pg_trigger WHERE NOT tgisinternal AND (tgname LIKE 'immutable_legal_contract%' OR tgname LIKE 'immutable_truncate_legal_contract%')")).scalars().all()
        self.assertEqual(len(triggers), 26)


if __name__ == "__main__":
    unittest.main()
