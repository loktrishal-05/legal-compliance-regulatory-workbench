"""Cited extractive summary profiles, independent approval and lossless export parity."""
import io
import json
import os
import unittest
import zipfile
from uuid import uuid4
from sqlalchemy import update
from app.db.models.legal_scope import DocumentAccess
from app.services.legal_policy import LegalAccessDenied
import test_legal_scope_contracts_persistence as fixtures
import test_legal_scope_provisioning as provisioning


class SummaryTests(unittest.TestCase):
    make_engine = provisioning.LegalProvisioningTests.make_engine

    def setUp(self):
        from app.services import legal_summaries
        from app.schemas.legal_contract import SummaryRequest
        self.service = legal_summaries
        self.fixture = fixtures.ContractPersistenceTests()
        self.fixture.make_engine = self.make_engine
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.db, self.args = self.fixture.db, self.fixture.args
        self.request = SummaryRequest(sources=[{"document_id": self.fixture.source.document_id,
            "version_id": self.fixture.source.version_id}])

    def create(self, **updates):
        result = self.service.create(self.db, request=self.request.model_copy(update=updates), **self.args)
        self.db.commit()
        return result

    def approve(self, result):
        from app.services import legal_review
        f = self.fixture.fixture
        f.grant(f.bob, role="legal_reviewer")
        for operation in ("read", "review_legal"):
            self.db.add(DocumentAccess(document_id=self.fixture.source.document_id, organization_id=f.ws.organization_id,
                workspace_id=f.ws.id, user_id=f.bob.id, operation=operation))
        self.db.commit()
        legal_review.decide(self.db, workspace_id=f.ws.id, review_id=result["review_id"], reviewer_id=f.bob.id,
            decision="approve", rationale="Synthetic summary review", current_terms_version="1.0")
        self.db.commit()

    def test_every_profile_and_audience_preserve_all_source_statements_and_conditions(self):
        for profile in ("executive", "detailed", "clause", "risk", "obligation", "action", "change"):
            for audience in ("legal", "business"):
                result = self.create(profile=profile, audience=audience)
                self.assertEqual(result["profile"], profile)
                self.assertEqual(result["audience"], audience)
                self.assertTrue(all(s["citations"] for s in result["statements"]))
                self.assertTrue(any("provided the invoice is valid" in s["text"] for s in result["statements"]))
                self.assertEqual(result["coverage"]["omitted_span_ids"], [])
                self.assertEqual(result["outcome"], "pending")
                self.assertEqual(self.create(profile=profile, audience=audience)["summary_id"], result["summary_id"])

    def test_unapproved_export_denied_and_approved_exports_embed_identical_manifest(self):
        result = self.create()
        with self.assertRaises(self.fixture.service.ContractConflict):
            self.service.export(self.db, summary_id=result["summary_id"], format="json", **self.args)
        self.approve(result)
        expected = json.loads(self.service.export(self.db, summary_id=result["summary_id"], format="json", **self.args)[0])
        self.assertEqual(expected["summary"]["statements"], result["statements"])
        self.assertEqual(expected["manifest"]["revision_sha256"], result["revision_sha256"])
        docx, _ = self.service.export(self.db, summary_id=result["summary_id"], format="docx", **self.args)
        with zipfile.ZipFile(io.BytesIO(docx)) as archive:
            self.assertEqual(json.loads(archive.read("legal/manifest.json")), expected)
            self.assertIn("provided the invoice is valid", archive.read("word/document.xml").decode())
        import pymupdf
        pdf, _ = self.service.export(self.db, summary_id=result["summary_id"], format="pdf", **self.args)
        with pymupdf.open(stream=pdf, filetype="pdf") as document:
            self.assertEqual(json.loads(document.embfile_get("legal-manifest.json")), expected)
            self.assertIn("provided the invoice is valid", " ".join(" ".join(page.get_text() for page in document).split()))

    def test_revoked_or_cross_tenant_summary_read_export_and_review_deny(self):
        result = self.create()
        with self.assertRaises(LegalAccessDenied):
            self.service.get(self.db, summary_id=result["summary_id"], **(self.args | {"workspace_id": self.fixture.fixture.other.id}))
        self.approve(result)
        self.db.execute(update(DocumentAccess).where(DocumentAccess.user_id == self.args["actor_id"]).values(is_active=False))
        self.db.commit()
        for format in ("json", "pdf", "docx"):
            with self.assertRaises(LegalAccessDenied):
                self.service.export(self.db, summary_id=result["summary_id"], format=format, **self.args)

    def test_cross_document_synthesis_keeps_per_version_citations_and_conflict_warning(self):
        from app.schemas.legal_contract import SourceRequest
        f = self.fixture.fixture
        second = f.prepare(b"1. Payment\nBuyer shall pay within 15 days of invoice.\n", filename="synthetic-other.txt")
        f.process(second)
        result = self.create(sources=self.request.sources + [SourceRequest(document_id=second.document_id, version_id=second.version_id)])
        self.assertEqual({c["version_id"] for s in result["statements"] for c in s["citations"]},
            {str(self.fixture.source.version_id), str(second.version_id)})
        self.assertTrue(result["contradictions"])
        self.assertIn("cross_document_conflict_requires_review", result["uncertainties"])
        self.assertEqual(len(self.service.list_summaries(self.db, **self.args)["items"]), 1)
        self.db.execute(update(DocumentAccess).where(DocumentAccess.document_id == second.document_id).values(is_active=False))
        self.db.commit()
        self.assertEqual(self.service.list_summaries(self.db, **self.args), {"items": []})

    def test_unicode_exports_preserve_source_and_single_version_change_has_missing_information(self):
        from app.schemas.legal_contract import SourceRequest
        f = self.fixture.fixture
        source = f.prepare("1. Payment\nBuyer shall pay ₹100, provided consent remains valid.\n".encode(), filename="synthetic-unicode.txt")
        f.process(source)
        result = self.create(sources=[SourceRequest(document_id=source.document_id, version_id=source.version_id)], profile="change")
        self.assertIn("A second version is required to establish change.", result["missing_information"])
        f.grant(f.bob, role="legal_reviewer")
        for op in ("read", "review_legal"):
            self.db.add(DocumentAccess(document_id=source.document_id, organization_id=f.ws.organization_id,
                workspace_id=f.ws.id, user_id=f.bob.id, operation=op))
        self.db.commit()
        from app.services import legal_review
        legal_review.decide(self.db, workspace_id=f.ws.id, review_id=result["review_id"], reviewer_id=f.bob.id,
            decision="approve", rationale="Synthetic Unicode review", current_terms_version="1.0")
        self.db.commit()
        import pymupdf
        data, _ = self.service.export(self.db, summary_id=result["summary_id"], format="pdf", **self.args)
        with pymupdf.open(stream=data, filetype="pdf") as pdf:
            self.assertIn("₹100", "".join(p.get_text() for p in pdf))


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not selected")
class SummaryPostgresTests(SummaryTests):
    make_engine = provisioning.LegalProvisioningPostgresTests.make_engine


if __name__ == "__main__":
    unittest.main()
