"""Tenant/source-bound immutable contract persistence and current authorization."""
import os
import unittest
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from app.db.base import Base
from app.db.models.legal_scope import DocumentAccess
from app.services.legal_policy import LegalAccessDenied
import test_legal_scope_extraction as extraction_fixture
import test_legal_scope_provisioning as provisioning_fixture
from test_legal_scope_contracts import CORPUS


class ContractPersistenceTests(unittest.TestCase):
    make_engine = provisioning_fixture.LegalProvisioningTests.make_engine

    def setUp(self):
        from app.db.models import legal_contract as models
        from app.services import legal_contracts as service
        self.models, self.service = models, service
        self.fixture = extraction_fixture.LegalExtractionTests()
        self.fixture.make_engine = self.make_engine
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.db = self.fixture.db
        tables = {t for t in Base.metadata.tables.values() if t.name in models.TABLES}
        pending = list(tables)
        while pending:
            for fk in pending.pop().foreign_keys:
                if fk.column.table not in tables:
                    tables.add(fk.column.table)
                    pending.append(fk.column.table)
        Base.metadata.create_all(self.fixture.engine, tables=list(tables))
        self.source = self.fixture.prepare((CORPUS / "msa.txt").read_bytes())
        self.extraction = self.fixture.process(self.source)
        self.args = {"actor_id": self.fixture.alice.id, "workspace_id": self.fixture.ws.id,
                     "current_terms_version": "1.0"}

    def create(self, **kwargs):
        result = self.service.create_contract(self.db, document_id=self.source.document_id,
            version_id=self.source.version_id, title="Synthetic MSA", **(self.args | kwargs))
        self.db.commit()
        return result

    def analyze(self, contract=None, **kwargs):
        contract = contract or self.create()
        result = self.service.analyze(self.db, contract_id=contract["contract_id"],
            version_id=contract["contract_version_id"], **(self.args | kwargs))
        self.db.commit()
        return result

    def test_create_analysis_and_replay_preserve_immutable_source_proposals(self):
        contract = self.create()
        self.assertEqual(self.create()["contract_id"], contract["contract_id"])
        result = self.analyze(contract)
        self.assertEqual(self.analyze(contract)["analysis_id"], result["analysis_id"])
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(len(result["clauses"]), 6)
        self.assertEqual(len(result["obligations"]), 3)
        self.assertTrue(all(o["outcome"] == "proposed" for o in result["obligations"]))
        self.assertEqual(len(list(self.db.scalars(select(self.models.ContractAnalysis)))), 1)

    def test_cross_tenant_read_only_and_revocation_are_denied_before_sources(self):
        contract = self.create()
        with self.assertRaises(LegalAccessDenied):
            self.analyze(contract, workspace_id=self.fixture.other.id)
        self.db.execute(update(DocumentAccess).where(DocumentAccess.user_id == self.fixture.alice.id,
            DocumentAccess.operation == "propose").values(is_active=False))
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):
            self.analyze(contract)
        self.assertEqual(self.service.list_contracts(self.db, **self.args)["items"][0]["contract_id"], contract["contract_id"])
        self.db.execute(update(DocumentAccess).values(is_active=False))
        self.db.commit()
        self.assertEqual(self.service.list_contracts(self.db, **self.args), {"items": []})

    def test_cross_workspace_fk_and_orm_mutation_are_rejected(self):
        result = self.analyze()
        row = self.db.get(self.models.ContractAnalysis, result["analysis_id"])
        values = {c.name: getattr(row, c.name) for c in row.__table__.columns}
        values.update(id=uuid4(), workspace_id=self.fixture.other.id, revision_sha256="e" * 64)
        with self.assertRaises(IntegrityError):
            self.db.execute(row.__table__.insert().values(**values))
        self.db.rollback()
        row.profile_version = "forged"
        with self.assertRaisesRegex(ValueError, "immutable"):
            self.db.flush()
        self.db.rollback()

    def test_audit_failure_rolls_back_new_analysis_and_all_children(self):
        from app.services.audit import AuditChainError
        contract = self.create()
        with patch.object(self.service, "append_event", side_effect=AuditChainError("synthetic")):
            with self.assertRaises(AuditChainError):
                self.analyze(contract)
        self.db.rollback()
        self.assertEqual(list(self.db.scalars(select(self.models.ContractAnalysis))), [])
        self.assertEqual(list(self.db.scalars(select(self.models.ContractClause))), [])

    def test_clause_span_fk_cannot_be_rebound_to_another_extraction(self):
        result = self.analyze()
        row = self.db.scalars(select(self.models.ContractClauseSpan)).first()
        values = {c.name: getattr(row, c.name) for c in row.__table__.columns}
        values.update(id=uuid4(), extraction_id=uuid4())
        with self.assertRaises(IntegrityError):
            self.db.execute(row.__table__.insert().values(**values))
        self.db.rollback()


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not selected")
class ContractPersistencePostgresTests(ContractPersistenceTests):
    make_engine = provisioning_fixture.LegalProvisioningPostgresTests.make_engine


if __name__ == "__main__":
    unittest.main()
