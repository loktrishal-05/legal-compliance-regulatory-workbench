"""Synthetic rasterized/mixed PDFs, real local OCR; no customer documents/models."""
import hashlib
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
        data = scanned_pdf()
        parsed = extraction.run_parser(data, "pdf", ocr=True)
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
        with pymupdf.open() as pdf:
            pdf.new_page()
            parsed = extraction.run_parser(pdf.tobytes(), "pdf", ocr=True)
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


if __name__ == "__main__":
    unittest.main()
