"""Native text parser subprocess: bounded input/output; no DB, settings, models or network adapters.

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
WORD = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def parse(data: bytes, fmt: str) -> dict:
    if not data or len(data) > MAX_INPUT:
        raise ValueError("parser_input_limit")
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
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024 * 1024, 8 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    try:
        result = parse(sys.stdin.buffer.read(MAX_INPUT + 1), sys.argv[1])
        sys.stdout.write(json.dumps(result, ensure_ascii=True, separators=(",", ":")))
    except Exception:
        return 1  # no source text, file paths or parser internals on stderr
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
