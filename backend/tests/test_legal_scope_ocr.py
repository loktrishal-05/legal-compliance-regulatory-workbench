"""Synthetic rasterized/mixed PDFs, real local OCR; no customer documents/models."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.services import legal_extraction as extraction


def scanned_pdf(mixed=False):
    import pymupdf
    with pymupdf.open() as source:
        page = source.new_page(width=612, height=792)
        page.insert_text((72, 120), "SYNTHETIC Buyer shall pay Seller within 30 days.", fontsize=18)
        image = page.get_pixmap(matrix=pymupdf.Matrix(2, 2)).tobytes("png")
    with pymupdf.open() as pdf:
        page = pdf.new_page(width=612, height=792)
        if mixed:
            page.insert_text((72, 50), "SYNTHETIC native heading retained", fontsize=14)
            page.insert_image(pymupdf.Rect(0, 80, 612, 872), stream=image)
        else:
            page.insert_image(page.rect, stream=image)
        return pdf.tobytes()


class LegalOcrTests(unittest.TestCase):
    def test_real_scanned_pdf_has_ocr_text_exact_page_regions_and_uncertainty(self):
        from app.services.legal_parser_worker import parse
        from app.schemas.legal_extraction import NativeArtifact
        data = scanned_pdf()
        parsed = NativeArtifact.model_validate(parse(data, "pdf", ocr=True)).model_dump()
        self.assertEqual(parsed["source_sha256"], hashlib.sha256(data).hexdigest())
        self.assertIn("Buyer shall pay Seller within 30 days", parsed["text"])
        self.assertEqual(parsed["status"], "needs_verification")
        self.assertIn("ocr_text_requires_human_verification", parsed["warnings"])
        self.assertTrue(parsed["spans"])
        for span in parsed["spans"]:
            self.assertEqual(span["locator"]["page"], 1)
            self.assertEqual(span["locator"]["extraction_method"], "ocr")
            self.assertTrue(parsed["text"][span["start"]:span["end"]].strip())
            x0, y0, x1, y1 = span["locator"]["bbox"]
            self.assertTrue(0 <= x0 < x1 <= 612 and 0 <= y0 < y1 <= 792)

    def test_mixed_pdf_preserves_native_text_and_adds_image_text(self):
        parsed = extraction.run_parser(scanned_pdf(mixed=True), "pdf", ocr=True)
        self.assertIn("SYNTHETIC native heading retained", parsed["text"])
        self.assertIn("Buyer shall pay Seller", parsed["text"])
        self.assertEqual({s["locator"]["extraction_method"] for s in parsed["spans"]}, {"native", "ocr"})

    def test_blank_pdf_never_gets_invented_text(self):
        import pymupdf
        from app.services.legal_parser_worker import parse
        with pymupdf.open() as pdf:
            pdf.new_page()
            parsed = parse(pdf.tobytes(), "pdf", ocr=True)
        self.assertEqual(parsed["text"], "")
        self.assertEqual(parsed["spans"], [])
        self.assertEqual(parsed["status"], "needs_verification")

    def test_ocr_bounds_and_missing_language_data_fail_without_partial_output(self):
        from app.services import legal_parser_worker as worker
        with patch.object(worker, "OCR_MAX_PIXELS", 1), self.assertRaises(ValueError):
            worker.parse(scanned_pdf(), "pdf", ocr=True)
        with patch.object(worker, "OCR_TESSDATA", "/tmp/legal-missing-tessdata"), self.assertRaises(Exception):
            worker.parse(scanned_pdf(), "pdf", ocr=True)
        with self.assertRaises(extraction.ParserFailed):
            extraction.run_parser(b"SYNTHETIC", "txt", ocr=True)

    def test_scan_page_limit_refuses_whole_artifact_instead_of_partial_text(self):
        import pymupdf
        from app.services.legal_parser_worker import parse
        with pymupdf.open(stream=scanned_pdf(), filetype="pdf") as source, pymupdf.open() as pdf:
            for _ in range(6):
                pdf.insert_pdf(source)
            with self.assertRaisesRegex(ValueError, "ocr_page_limit"):
                parse(pdf.tobytes(deflate=True), "pdf", ocr=True)


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable API runtime not selected")
class LegalOcrApiTests(unittest.TestCase):
    def test_native_then_ocr_then_correction_and_independent_http_review(self):
        from datetime import datetime, timedelta, timezone
        from uuid import UUID, uuid4
        from sqlalchemy import select
        from app.core.config import settings
        from app.core.security import hash_session_token
        from app.db.models import AuthSession, User
        from app.db.models.legal_scope import DocumentAccess, WorkspaceMembership
        from app.db.models.legal_extraction import LegalExtraction
        from app.services import legal_intake
        from test_legal_scope_api import LegalScopeApiTests
        fixture = LegalScopeApiTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        db, workspace, actor = fixture.fixture.db, fixture.fixture.workspace, fixture.fixture.actor
        with tempfile.TemporaryDirectory(prefix="legal-ocr-api-") as directory:
            with patch.object(settings, "data_root", Path(directory)):
                received = legal_intake.receive(db, actor_id=actor.id, workspace_id=workspace.id,
                    filename="synthetic.pdf", document_type="contract", classification="internal",
                    data=scanned_pdf(), current_terms_version="1.0", data_root=settings.data_root,
                    scanner=lambda data: (True, "synthetic-fixture"))
                db.add(DocumentAccess(document_id=received.document_id, organization_id=workspace.organization_id,
                    workspace_id=workspace.id, user_id=actor.id, operation="propose"))
                db.commit()
                base = f"/v1/workspaces/{workspace.id}/documents/{received.document_id}/versions/{received.version_id}"
                native = fixture.client.post(base + "/extractions")
                self.assertEqual(native.status_code, 201)
                self.assertEqual(native.json()["span_ids"], [])
                with patch.object(settings, "legal_ocr_enabled", False):
                    self.assertEqual(fixture.client.post(base + "/extractions?ocr=true").status_code, 409)
                with patch.object(settings, "legal_ocr_enabled", True):
                    processed = fixture.client.post(base + "/extractions?ocr=true")
                    self.assertEqual(processed.status_code, 201)
                    self.assertEqual(processed.json()["status"], "needs_verification")
                    self.assertEqual(fixture.client.post(base + "/extractions?ocr=true").json()["extraction_id"],
                                     processed.json()["extraction_id"])
                self.assertEqual(len(list(db.scalars(select(LegalExtraction).where(LegalExtraction.version_id == received.version_id)))), 2)
                span = processed.json()["span_ids"][0]
                source = fixture.client.get(base + "/spans/" + span).json()
                self.assertEqual(source["locator"]["extraction_method"], "ocr")
                payload = {"idempotency_key": str(uuid4()), "expected_quote_sha256": hashlib.sha256(source["quote"].encode()).hexdigest(),
                    "corrected_text": "SYNTHETIC Buyer shall pay Seller within 30 days.", "rationale": "Synthetic visual transcription check"}
                proposed = fixture.client.post(base + "/spans/" + span + "/corrections", json=payload)
                self.assertEqual(proposed.status_code, 201)
                self.assertEqual(proposed.json()["outcome"], "proposed")
                correction = base + "/corrections/" + proposed.json()["correction_id"]
                self.assertEqual(fixture.client.post(correction + "/decisions", json={"outcome": "approved", "rationale": "Self"}).status_code, 404)
                now = datetime.now(timezone.utc)
                reviewer = User(id=uuid4(), username="synthetic-ocr-reviewer", role="reviewer", terms_version="1.0", terms_accepted_at=now)
                db.add(reviewer)
                db.flush()
                db.add(WorkspaceMembership(organization_id=workspace.organization_id, workspace_id=workspace.id,
                    user_id=reviewer.id, role="legal_reviewer", clearance="internal"))
                db.flush()
                for operation in ("read", "review_legal"):
                    db.add(DocumentAccess(document_id=received.document_id, organization_id=workspace.organization_id,
                        workspace_id=workspace.id, user_id=reviewer.id, operation=operation))
                token = "synthetic-ocr-review-session-only"
                db.add(AuthSession(user_id=reviewer.id, token_hash=hash_session_token(token), expires_at=now + timedelta(hours=1)))
                db.commit()
                fixture.client.cookies.set(settings.session_cookie_name, token)
                decision = fixture.client.post(correction + "/decisions", json={"outcome": "approved", "rationale": "Synthetic independent transcription review"})
                self.assertEqual(decision.status_code, 201)
                self.assertEqual(decision.json()["outcome"], "approved")
                self.assertEqual(fixture.client.get(correction).json()["original_quote"], source["quote"])
                self.assertEqual(fixture.client.get(correction).headers["cache-control"], "no-store")
                self.assertEqual(fixture.client.get(base + "/spans/" + span).json()["quote"], source["quote"])
                self.assertEqual(db.get(LegalExtraction, UUID(processed.json()["extraction_id"])).status, "needs_verification")
                self.assertEqual(fixture.client.post(correction + "/decisions", json={"outcome": "rejected", "rationale": "Conflicting retry"}).status_code, 409)
                self.assertEqual(fixture.client.post(correction + "/decisions", json={"outcome": "approved", "rationale": "Origin"},
                    headers={"Origin": "https://untrusted.invalid"}).status_code, 403)


if __name__ == "__main__":
    unittest.main()
