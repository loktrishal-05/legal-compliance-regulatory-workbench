"""E2a synthetic native documents, scoped immutable provenance, failure and denial checks."""
import io
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from uuid import uuid4
import zipfile

from sqlalchemy import select, update, text
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.db.models import AuditEvent, Document, DocumentVersion
from app.db.models.legal_scope import DocumentAccess, WorkspaceMembership
from app.db.models.legal_extraction import LegalExtraction, LegalSourceSpan
from app.services import legal_extraction as extraction
from app.services.legal_policy import LegalAccessDenied
import test_legal_scope_intake as intake_fixture
import test_legal_scope_provisioning as fixtures


def synthetic_docx():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>1. Payment</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>SYNTHETIC Buyer shall pay</w:t></w:r><w:r><w:tab/><w:t>within 30 days.</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:body></w:document>')
    return buffer.getvalue()


class LegalExtractionTests(unittest.TestCase):
    make_engine = fixtures.LegalProvisioningTests.make_engine
    grant = fixtures.LegalProvisioningTests.grant
    receive = intake_fixture.LegalIntakeTests.receive

    def setUp(self):
        intake_fixture.LegalIntakeTests.setUp(self)
        Base.metadata.create_all(self.engine, tables=[LegalExtraction.__table__, LegalSourceSpan.__table__])

    def prepare(self, data=intake_fixture.TXT, filename="synthetic.txt", scanner=intake_fixture.CLEAN):
        result = self.receive(data, filename, scanner=scanner)
        self.db.add(DocumentAccess(document_id=result.document_id, organization_id=self.ws.organization_id,
                                   workspace_id=self.ws.id, user_id=self.alice.id, operation="propose"))
        self.db.commit()
        return result

    def process(self, received, **kw):
        result = extraction.process(self.db, actor_id=self.alice.id, workspace_id=self.ws.id,
            document_id=received.document_id, version_id=received.version_id,
            current_terms_version=fixtures.TERMS, data_root=self.root, **kw)
        self.db.commit()
        return result

    def resolve(self, received, span_id, **kw):
        return extraction.resolve_span(self.db, actor_id=kw.pop("actor_id", self.alice.id),
            workspace_id=kw.pop("workspace_id", self.ws.id), document_id=received.document_id,
            version_id=received.version_id, span_id=span_id, current_terms_version=fixtures.TERMS, **kw)

    def test_text_spans_exact_unicode_hash_bound_and_idempotent(self):
        data = "SYNTHETIC clause: Buyer shall pay ₹100.\r\nNotice within 30 days.\n".encode()
        received = self.prepare(data)
        result = self.process(received)
        self.assertEqual(result.status, "ready")
        quotes = [self.resolve(received, sid) for sid in result.span_ids]
        self.assertEqual(quotes[0]["quote"], "SYNTHETIC clause: Buyer shall pay ₹100.\r\n")
        self.assertEqual(quotes[0]["locator"], {"kind": "line", "line": 1, "offset_unit": "unicode_codepoint"})
        self.assertEqual(quotes[0]["source_sha256"], self.db.get(DocumentVersion, received.version_id).source_sha256)
        with patch.object(extraction, "run_parser", side_effect=AssertionError("retry parsed twice")):
            self.assertEqual(self.process(received).extraction_id, result.extraction_id)

    def test_docx_table_text_has_part_and_paragraph_locator_not_fake_page(self):
        received = self.prepare(synthetic_docx(), "synthetic.docx")
        result = self.process(received)
        quotes = [self.resolve(received, sid) for sid in result.span_ids]
        self.assertEqual([q["quote"] for q in quotes], ["1. Payment", "SYNTHETIC Buyer shall pay\twithin 30 days."])
        self.assertEqual(quotes[1]["locator"]["part"], "word/document.xml")
        self.assertEqual(quotes[1]["locator"]["paragraph"], 2)
        self.assertNotIn("page", quotes[1]["locator"])

    def test_real_native_pdf_retains_heading_and_page_boxes(self):
        import pymupdf
        with pymupdf.open() as pdf:
            page = pdf.new_page()
            page.insert_text((50, 50), "1. PAYMENT", fontsize=16)
            page.insert_text((50, 90), "SYNTHETIC Buyer shall pay Seller within 30 days of invoice.")
            data = pdf.tobytes()
        received = self.prepare(data, "synthetic.pdf")
        result = self.process(received)
        quotes = [self.resolve(received, sid) for sid in result.span_ids]
        self.assertTrue(any("1. PAYMENT" in q["quote"] for q in quotes))
        self.assertTrue(all(q["locator"]["page"] == 1 and len(q["locator"]["bbox"]) == 4 for q in quotes))

    def test_blank_pdf_requires_verification_and_has_no_invented_text(self):
        import pymupdf
        with pymupdf.open() as pdf:
            pdf.new_page()
            data = pdf.tobytes()
        result = self.process(self.prepare(data, "blank.pdf"))
        self.assertEqual((result.status, result.span_ids), ("needs_verification", ()))
        self.assertIn("pdf_low_text_or_scanned_pages", result.warnings)

    def test_quarantine_and_revocation_block_parser_before_source_read(self):
        received = self.prepare(scanner=None)
        with patch.object(extraction, "run_parser", side_effect=AssertionError("quarantine parsed")):
            with self.assertRaises(extraction.ExtractionBlocked):
                self.process(received)
        self.db.execute(update(WorkspaceMembership).where(WorkspaceMembership.user_id == self.alice.id)
                        .values(is_active=False))
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):
            self.process(received)

    def test_read_grant_alone_does_not_authorize_processing(self):
        received = self.receive(intake_fixture.TXT)
        with patch.object(extraction, "run_parser", side_effect=AssertionError("unauthorized parser")):
            with self.assertRaises(LegalAccessDenied):
                self.process(received)

    def test_cross_workspace_span_and_unknown_span_denied(self):
        received = self.prepare()
        result = self.process(received)
        for options in ({"workspace_id": self.other.id}, {"actor_id": self.bob.id}):
            with self.subTest(options=options), self.assertRaises(LegalAccessDenied):
                self.resolve(received, result.span_ids[0], **options)
        with self.assertRaises(LegalAccessDenied):
            self.resolve(received, uuid4())

    def test_parser_failure_audited_without_source_text_and_retry_allowed(self):
        received = self.prepare()
        with patch.object(extraction, "run_parser", side_effect=extraction.ParserFailed("parser_timeout")):
            with self.assertRaises(extraction.ParserFailed):
                self.process(received)
        self.db.commit()  # caller owns transaction, including failure audit/state
        event = self.db.scalars(select(AuditEvent).where(AuditEvent.event_type == "LEGAL_EXTRACTION_FAILED")).one()
        self.assertEqual(event.payload["code"], "parser_timeout")
        self.assertNotIn("Party A", str(event.payload))
        self.assertEqual(self.db.get(DocumentVersion, received.version_id).status, "failed")
        self.assertEqual(self.process(received).status, "ready")

    def test_source_tampering_is_denied_before_parser(self):
        received = self.prepare()
        path = self.root / self.db.get(Document, received.document_id).source_path
        path.chmod(0o600)
        path.write_bytes(b"SYNTHETIC tampered")
        from app.services.legal_intake import IntakeIntegrityError
        with patch.object(extraction, "run_parser", side_effect=AssertionError("tampered parser")):
            with self.assertRaises(IntakeIntegrityError):
                self.process(received)

    def test_revocation_during_parse_blocks_persistence(self):
        received = self.prepare()
        original = extraction.run_parser
        def revoke(*args, **kwargs):
            result = original(*args, **kwargs)
            self.db.execute(update(DocumentAccess).where(DocumentAccess.document_id == received.document_id)
                            .values(is_active=False))
            self.db.flush()
            return result
        with patch.object(extraction, "run_parser", side_effect=revoke), self.assertRaises(LegalAccessDenied):
            self.process(received)
        self.db.rollback()
        self.assertEqual(list(self.db.scalars(select(LegalExtraction))), [])

    def test_audit_failure_rolls_back_artifact_and_spans(self):
        from app.services.audit import AuditChainError
        received = self.prepare()
        with patch.object(extraction, "append_event", side_effect=AuditChainError("SYNTHETIC failure")):
            with self.assertRaises(AuditChainError):
                self.process(received)
        self.db.rollback()
        self.assertEqual(list(self.db.scalars(select(LegalSourceSpan))), [])

    def test_artifact_and_span_immutable(self):
        result = self.process(self.prepare())
        row = self.db.get(LegalExtraction, result.extraction_id)
        row.text = "SYNTHETIC rewritten"
        with self.assertRaisesRegex(ValueError, "immutable"):
            self.db.flush()
        self.db.rollback()

    def test_database_rejects_foreign_version_binding(self):
        received = self.prepare()
        result = self.process(received)
        row = self.db.get(LegalExtraction, result.extraction_id)
        values = {c.name: getattr(row, c.name) for c in LegalExtraction.__table__.columns}
        values.update(id=uuid4(), workspace_id=self.other.id, organization_id=self.other.organization_id)
        with self.assertRaises(IntegrityError):
            self.db.execute(LegalExtraction.__table__.insert().values(**values))
        self.db.rollback()


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not selected")
class LegalExtractionPostgresTests(LegalExtractionTests):
    make_engine = fixtures.LegalProvisioningPostgresTests.make_engine


class ParserBoundaryTests(unittest.TestCase):
    def test_timeout_is_sanitized(self):
        import subprocess
        with patch.object(extraction.subprocess, "run", side_effect=subprocess.TimeoutExpired("synthetic", 10)):
            with self.assertRaises(extraction.ParserFailed) as error:
                extraction.run_parser(b"SYNTHETIC", "txt")
        self.assertEqual(error.exception.code, "parser_timeout")

    def test_output_limits_reject_without_truncating_legal_text(self):
        from app.services.legal_parser_worker import parse
        with self.assertRaises(ValueError):
            parse(b"SYNTHETIC", "exe")


if __name__ == "__main__":
    unittest.main()
