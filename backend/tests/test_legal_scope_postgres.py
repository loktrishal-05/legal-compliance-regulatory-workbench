"""Run the same role/FK/revocation matrix on approved disposable PostgreSQL."""
import os
import unittest
from uuid import uuid4

from sqlalchemy import create_engine, text

from scripts.validate_legal_migrations import disposable_url
import test_legal_scope


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not explicitly selected")
class LegalScopePostgresTests(test_legal_scope.LegalScopeTests):
    def make_engine(self):
        url = disposable_url()
        admin = create_engine(url, connect_args={"connect_timeout": 5})
        schema = "legal_policy_" + uuid4().hex
        with admin.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        def cleanup():
            with admin.begin() as conn:
                conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            admin.dispose()
        self.addCleanup(cleanup)
        return create_engine(url.update_query_dict({"options": "-csearch_path=" + schema}),
                             connect_args={"connect_timeout": 5})


if __name__ == "__main__":
    unittest.main()
