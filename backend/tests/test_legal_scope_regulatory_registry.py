"""Registry persistence and trust-boundary checks over synthetic workspaces."""
import unittest
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.db.models.legal_regulatory import RegulatorySource
from app.schemas.legal_regulatory import SourceRequest, VersionRequest
from app.services import legal_regulatory as regulatory
from app.services.legal_policy import LegalAccessDenied
import test_legal_scope_provisioning as provisioning


class RegulatoryRegistryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = provisioning.LegalProvisioningTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.db = self.fixture.db
        Base.metadata.create_all(self.fixture.engine, tables=[RegulatorySource.__table__])
        self.fixture.grant(self.fixture.alice)
        self.request = SourceRequest(name="SYNTHETIC Registry", jurisdiction="SYNTHETIC",
            authority_tier="unverified", owner_id=self.fixture.alice.id)

    def create(self, actor=None, workspace=None):
        return regulatory.create_source(self.db, actor_id=(actor or self.fixture.alice).id,
            workspace_id=(workspace or self.fixture.ws).id, request=self.request, current_terms_version="1.0")

    def test_source_is_provisional_and_manual(self):
        row = self.create()
        self.db.commit()
        self.assertEqual((row.trust_state, row.import_policy), ("proposed", "manual"))
        self.assertEqual(row.owner_id, self.fixture.alice.id)
        self.assertIsNone(row.last_success_at)

    def test_authority_and_accepted_state_are_not_client_controlled(self):
        for key in ("trust_state", "approved", "actor_id", "import_policy"):
            with self.subTest(key=key), self.assertRaises(ValidationError):
                SourceRequest.model_validate({**self.request.model_dump(), key: "approved"})
        with self.assertRaises(ValidationError):
            VersionRequest(regulatory_document_id=uuid4(), document_id=uuid4(), version_id=uuid4(),
                extraction_id=uuid4(), effective_from="2026-10-09", effective_until="2026-10-09")

    def test_viewer_and_other_workspace_denied(self):
        self.fixture.grant(self.fixture.bob, role="viewer")
        for kwargs in ({"actor": self.fixture.bob}, {"workspace": self.fixture.other}):
            with self.subTest(kwargs=kwargs), self.assertRaises(LegalAccessDenied):
                self.create(**kwargs)

    def test_owner_must_belong_to_workspace(self):
        self.request = self.request.model_copy(update={"owner_id": self.fixture.bob.id})
        with self.assertRaises(LegalAccessDenied):
            self.create()

    def test_database_denies_cross_workspace_owner(self):
        row = self.create()
        self.db.commit()
        values = {c.name: getattr(row, c.name) for c in row.__table__.columns}
        values.update(id=uuid4(), workspace_id=self.fixture.other.id)
        with self.assertRaises(IntegrityError):
            self.db.execute(RegulatorySource.__table__.insert().values(**values))
        self.db.rollback()
