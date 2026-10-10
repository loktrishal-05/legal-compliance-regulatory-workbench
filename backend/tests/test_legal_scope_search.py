"""Authorized document lists, span lists, hash-verified originals and span search: SYNTHETIC tenants only."""
from datetime import datetime, timezone
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import update

from app.db.base import Base
from app.db.models import Document, User
from app.db.models.legal_jobs import LegalJob, LegalRegionTranscription
from app.db.models.legal_scope import DocumentAccess, Matter, MatterAccess
from app.services import legal_extraction, legal_jobs, legal_search
from app.services.legal_intake import IntakeIntegrityError
from app.services.legal_policy import LegalAccessDenied, authorize_workspace
import test_legal_scope_extraction as extraction_fixture
import test_legal_scope_reviews as review_fixture

TERMS = "1.0"
OTHER_TXT = b"SYNTHETIC lease: Tenant shall maintain insurance coverage annually.\n"


class SearchFixture(unittest.TestCase):
    make_engine = extraction_fixture.LegalExtractionTests.make_engine

    def setUp(self):
        self.f = extraction_fixture.LegalExtractionTests()
        self.f.make_engine = self.make_engine
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.db = self.f.db
        Base.metadata.create_all(self.f.engine, tables=review_fixture.WORKFLOW_TABLES + [
            LegalJob.__table__, LegalRegionTranscription.__table__])
        self.mine = self.f.prepare()
        self.f.process(self.mine)
        # Tenant B holds byte-identical content.
        self.dave = User(id=uuid4(), username="synthetic-dave", role="requester", terms_version=TERMS,
                         terms_accepted_at=datetime.now(timezone.utc))
        self.db.add(self.dave)
        self.db.commit()
        self.f.grant(self.dave, role="analyst", admin=self.f.bob, ws=self.f.other)
        self.theirs = self.f.receive(extraction_fixture.intake_fixture.TXT, user=self.dave, ws=self.f.other)
        self.db.add(DocumentAccess(document_id=self.theirs.document_id, organization_id=self.f.other.organization_id,
                                   workspace_id=self.f.other.id, user_id=self.dave.id, operation="propose"))
        self.db.commit()
        legal_extraction.process(self.db, actor_id=self.dave.id, workspace_id=self.f.other.id,
            document_id=self.theirs.document_id, version_id=self.theirs.version_id, current_terms_version=TERMS,
            data_root=self.f.root)
        self.db.commit()

    def ctx(self, user=None, ws=None):
        return authorize_workspace(self.db, (user or self.f.alice).id, (ws or self.f.ws).id, current_terms_version=TERMS)

    def search(self, q="Party A", user=None, ws=None):
        return legal_search.search_spans(self.db, self.ctx(user, ws), q, 20, current_terms_version=TERMS)


class LegalSearchTests(SearchFixture):
    def test_identical_content_in_two_tenants_never_crosses(self):
        mine = self.search()
        theirs = self.search(user=self.dave, ws=self.f.other)
        self.assertEqual({r["document_id"] for r in mine}, {self.mine.document_id})
        self.assertEqual({r["document_id"] for r in theirs}, {self.theirs.document_id})
        self.assertIn("Party A shall pay", mine[0]["quote"])
        with self.assertRaises(LegalAccessDenied):  # alice has no membership in tenant B at all
            self.ctx(ws=self.f.other)

    def test_restricted_matter_and_clearance_filter_before_ranking(self):
        matter = Matter(id=uuid4(), organization_id=self.f.ws.organization_id, workspace_id=self.f.ws.id,
                        name="Synthetic restricted matter")
        self.db.add(matter)
        self.db.flush()
        self.db.add(MatterAccess(organization_id=self.f.ws.organization_id, workspace_id=self.f.ws.id,
                                 matter_id=matter.id, user_id=self.f.alice.id))
        self.db.commit()
        restricted = self.f.receive(OTHER_TXT, filename="matter.txt", matter_id=matter.id)
        self.db.add(DocumentAccess(document_id=restricted.document_id, organization_id=self.f.ws.organization_id,
                                   workspace_id=self.f.ws.id, user_id=self.f.alice.id, operation="propose"))
        self.db.commit()
        self.f.process(restricted)
        self.assertEqual(len(self.search("insurance")), 1)
        self.assertEqual(len(legal_search.list_documents(self.db, self.ctx(), current_terms_version=TERMS)), 2)
        self.db.execute(update(MatterAccess).values(is_active=False))
        self.db.commit()
        self.assertEqual(self.search("insurance"), [])
        self.assertEqual([d["document_id"] for d in legal_search.list_documents(self.db, self.ctx(),
                          current_terms_version=TERMS)], [self.mine.document_id])

    def test_revocation_mid_search_drops_result(self):
        real = legal_search.authorize_document

        def revoke_then_check(db, actor_id, workspace_id, document_id, **kw):
            db.execute(update(DocumentAccess).where(DocumentAccess.user_id == actor_id).values(is_active=False))
            return real(db, actor_id, workspace_id, document_id, **kw)
        with patch.object(legal_search, "authorize_document", side_effect=revoke_then_check):
            self.assertEqual(self.search(), [])
        self.db.rollback()
        self.assertEqual(len(self.search()), 1)

    def test_tampered_ids_and_foreign_versions_are_unavailable(self):
        ctx = self.ctx()
        with self.assertRaises(LegalAccessDenied):  # tenant B document through tenant A workspace
            legal_jobs._extraction(self.db, ctx, self.theirs.document_id, self.theirs.version_id)
        with self.assertRaises(LegalAccessDenied):  # own document, foreign version id
            legal_jobs._extraction(self.db, ctx, self.mine.document_id, self.theirs.version_id)
        with self.assertRaises(LegalAccessDenied):
            legal_jobs.original(self.db, actor_id=self.f.alice.id, workspace_id=self.f.ws.id,
                document_id=self.theirs.document_id, version_id=self.theirs.version_id, current_terms_version=TERMS,
                data_root=self.f.root)

    def test_original_download_is_hash_verified_and_audited(self):
        data, fmt, name, sha = legal_jobs.original(self.db, actor_id=self.f.alice.id, workspace_id=self.f.ws.id,
            document_id=self.mine.document_id, version_id=self.mine.version_id, current_terms_version=TERMS,
            data_root=self.f.root)
        self.db.commit()
        self.assertEqual((data, fmt), (extraction_fixture.intake_fixture.TXT, "txt"))
        stored = Path(self.f.root, *self.db.get(Document, self.mine.document_id).source_path.split("/"))
        stored.chmod(0o600)
        stored.write_bytes(b"tampered")
        with self.assertRaises(IntakeIntegrityError):
            legal_jobs.original(self.db, actor_id=self.f.alice.id, workspace_id=self.f.ws.id,
                document_id=self.mine.document_id, version_id=self.mine.version_id, current_terms_version=TERMS,
                data_root=self.f.root)

    def test_empty_overlong_and_nul_queries_return_nothing(self):
        for q in ("", " ", "x" * 201, "a\0b"):
            self.assertEqual(self.search(q), [])


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not selected")
class LegalSearchPostgresTests(LegalSearchTests):
    make_engine = extraction_fixture.LegalExtractionPostgresTests.make_engine


if __name__ == "__main__":
    unittest.main()
