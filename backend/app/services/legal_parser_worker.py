"""Native/opt-in English OCR subprocess: bounded input/output; no DB, settings or private/network adapters.

Resource limits are a development containment boundary, not a deployment-grade OS sandbox.
"""
import hashlib
import io
import json
from pathlib import Path
import sys
from xml.parsers import expat
import xml.etree.ElementTree as ET
import zipfile

MAX_INPUT = 25 * 1024 * 1024
MAX_TEXT = 2 * 1024 * 1024
MAX_SPANS = 2000
OCR_MAX_PAGES = 5
OCR_MAX_PIXELS = 8_000_000
OCR_TESSDATA = "/usr/share/tesseract-ocr/5/tessdata"
WORD = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def parse(data: bytes, fmt: str, *, ocr: bool = False) -> dict:
    if not data or len(data) > MAX_INPUT:
        raise ValueError("parser_input_limit")
    if ocr and fmt != "pdf":
        raise ValueError("ocr_requires_pdf")
    blocks, warnings = [], []
    extractor = "stdlib_native"
    if fmt == "txt":
        for number, line in enumerate(data.decode("utf-8-sig").splitlines(keepends=True), 1):
            blocks.append((line, {"kind": "line", "line": number}))
    elif fmt == "docx":
        warnings.append("docx_native_structure_requires_verification")
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            parts = [n for n in archive.namelist() if n == "word/document.xml" or
                     (n.startswith("word/") and n.endswith(".xml") and
                      Path(n).stem.startswith(("header", "footer", "footnotes", "endnotes", "comments")))]
            for part in sorted(parts, key=lambda p: (p != "word/document.xml", p)):
                xml = archive.read(part)
                # Parent E1 already bounds/validates the archive; independently reject declarations here.
                parser = expat.ParserCreate()
                def reject_declaration(*args):
                    raise ValueError("xml_declaration_forbidden")
                parser.StartDoctypeDeclHandler = reject_declaration
                parser.EntityDeclHandler = reject_declaration
                parser.ExternalEntityRefHandler = reject_declaration
                parser.Parse(xml, True)
                root = ET.fromstring(xml)
                tags = {element.tag for element in root.iter()}
                if tags & {WORD + tag for tag in ("drawing", "pict", "altChunk", "fldChar", "instrText", "ins", "del", "numPr")}:
                    warnings.append("docx_dynamic_image_revision_or_numbering_requires_verification")
                for number, paragraph in enumerate(root.iter(WORD + "p"), 1):
                    pieces = []
                    for element in paragraph.iter():
                        if element.tag in {WORD + "t", WORD + "delText"}:
                            pieces.append(element.text or "")
                        elif element.tag == WORD + "tab":
                            pieces.append("\t")
                        elif element.tag in {WORD + "br", WORD + "cr"}:
                            pieces.append("\n")
                    content = "".join(pieces)
                    if content:
                        blocks.append((content, {"kind": "paragraph", "part": part, "paragraph": number}))
    elif fmt == "pdf":
        # Reuse the inspected native parser, retain headings for legal coverage; never run Docling/models.
        from app.services.extraction import inspect_pdf
        import pymupdf
        native, report = inspect_pdf(data, retain_headings=True)
        extractor = "pymupdf_native_" + pymupdf.VersionBind
        if report["ocr_required_pages"] or any(p["native_characters"] < 30 for p in report["pages"]):
            warnings.append("pdf_low_text_or_scanned_pages")
        warnings.append("pdf_native_layout_requires_verification")  # no silently accepted reading order/tables
        for block in native:
            blocks.append((block.text, {"kind": "page_region", "page": block.page_start,
                "bbox": block.bounding_boxes[0]["coordinates"], "origin": "TOPLEFT"}))
        if ocr:
            image_pages = {page["page"] for page in report["pages"] if page["images"]}
            if len(image_pages) > OCR_MAX_PAGES:
                raise ValueError("ocr_page_limit")
            if image_pages:
                warnings.append("ocr_text_requires_human_verification")
                with open(Path(OCR_TESSDATA) / "eng.traineddata", "rb") as language:
                    model_data = language.read(16 * 1024 * 1024 + 1)
                if len(model_data) > 16 * 1024 * 1024:
                    raise ValueError("ocr_language_limit")
                extractor = "pymupdf_ocr_" + pymupdf.VersionBind + "_eng200_" + hashlib.sha256(model_data).hexdigest()
            else:
                extractor = "pymupdf_ocr_no_images_" + pymupdf.VersionBind
            blocks = []
            with pymupdf.open(stream=data, filetype="pdf") as pdf:
                for number, page in enumerate(pdf, 1):
                    if number not in image_pages:
                        for block in native:
                            if block.page_start == number:
                                blocks.append((block.text, {"kind": "page_region", "page": number,
                                    "bbox": block.bounding_boxes[0]["coordinates"], "origin": "TOPLEFT",
                                    "extraction_method": "native"}))
                        continue
                    if page.rect.width * page.rect.height * (200 / 72) ** 2 > OCR_MAX_PIXELS:
                        raise ValueError("ocr_render_limit")
                    if sum(image["width"] * image["height"] for image in page.get_image_info()) > OCR_MAX_PIXELS:
                        raise ValueError("ocr_image_limit")
                    textpage = page.get_textpage_ocr(language="eng", dpi=200, full=False, tessdata=OCR_TESSDATA)
                    for item in page.get_text("dict", textpage=textpage, sort=True)["blocks"]:
                        if item["type"] != 0:
                            continue
                        content = "\n".join("".join(s["text"] for s in line["spans"]) for line in item["lines"]).strip()
                        if content:
                            derived = any(s["font"] == "GlyphLessFont" for line in item["lines"] for s in line["spans"])
                            blocks.append((content, {"kind": "page_region", "page": number,
                                "bbox": list(item["bbox"]), "origin": "TOPLEFT",
                                "extraction_method": "ocr" if derived else "native"}))
    else:
        raise ValueError("unsupported_parser_format")
    pieces, spans, offset = [], [], 0
    for content, locator in blocks:
        if fmt != "txt" and pieces:
            pieces.append("\n\n")
            offset += 2
        start = offset
        pieces.append(content)
        offset += len(content)
        if offset > MAX_TEXT:
            raise ValueError("parser_output_limit")
        if content.strip():
            locator["offset_unit"] = "unicode_codepoint"
            spans.append({"start": start, "end": offset, "locator": locator})
        if len(spans) > MAX_SPANS:
            raise ValueError("parser_span_limit")
    if not spans:
        warnings.append("no_native_text")
    return {"text": "".join(pieces), "spans": spans, "warnings": sorted(set(warnings)),
            "status": "needs_verification" if warnings else "ready", "extractor": extractor,
            "source_sha256": hashlib.sha256(data).hexdigest()}


def main():
    import resource  # fail closed outside the supported Linux test/runtime profile
    ocr = sys.argv[2:] == ["--ocr"]
    cpu = 20 if ocr else 5
    memory = (768 if ocr else 512) * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
    resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024 * 1024, 8 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    try:
        result = parse(sys.stdin.buffer.read(MAX_INPUT + 1), sys.argv[1], ocr=ocr)
        sys.stdout.write(json.dumps(result, ensure_ascii=True, separators=(",", ":")))
    except Exception:
        return 1  # no source text, file paths or parser internals on stderr
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
