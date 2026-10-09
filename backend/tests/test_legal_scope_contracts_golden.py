"""Real fixture metrics across TXT/generated DOCX/generated PDF; no invented thresholds."""
import io
import json
import unittest
from uuid import uuid4
from xml.sax.saxutils import escape
import zipfile
from test_legal_scope_contracts import CORPUS, EXPECTED


def generated(text, format):
    if format == "txt":
        return text.encode()
    if format == "docx":
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", "<Types/>")
            archive.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' +
                "".join("<w:p><w:r><w:t>" + escape(line) + "</w:t></w:r></w:p>" for line in text.splitlines()) + '</w:body></w:document>')
        return buffer.getvalue()
    import pymupdf
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        fits = page.insert_textbox(pymupdf.Rect(40, 40, 555, 800), text, fontsize=8)
        if fits < 0:
            raise AssertionError("Synthetic fixture did not fit; do not truncate benchmark")
        return pdf.tobytes()


def scores(expected, actual):
    tp, fp, fn = len(expected & actual), len(actual - expected), len(expected - actual)
    return {"true_positive": tp, "false_positive": fp, "false_negative": fn,
        "precision": tp/(tp+fp) if tp+fp else 0.0, "recall": tp/(tp+fn) if tp+fn else 0.0}


class ContractGoldenTests(unittest.TestCase):
    def test_report_real_fixture_metrics_for_clauses_parties_fields_obligations(self):
        from app.services.legal_contract_analysis import analyze_sources
        from app.services.legal_parser_worker import parse
        gold = json.loads((CORPUS / "expected.json").read_text())
        report = {}
        for format in ("txt", "docx", "pdf"):
            wanted = {key: set() for key in ("clauses", "parties", "fields", "obligations")}
            produced = {key: set() for key in wanted}
            for name, clause_types in EXPECTED.items():
                text = (CORPUS / (name + ".txt")).read_text()
                parsed = parse(generated(text, format), format)
                sources = [{"span_id": str(uuid4()), "quote": parsed["text"][s["start"]:s["end"]], "locator": s["locator"]}
                    for s in parsed["spans"]]
                result = analyze_sources(sources, quality=parsed["status"])
                wanted["clauses"].update((name, pos, kind) for pos, kind in enumerate(clause_types, 1))
                produced["clauses"].update((name, c["ordinal"], c["clause_type"]) for c in result["clauses"])
                wanted["parties"].update((name, value) for value in gold[name]["parties"])
                produced["parties"].update((name, p["name"]) for p in result["parties"])
                wanted["fields"].update((name, kind, value) for kind,value in gold[name]["fields"])
                produced["fields"].update((name, f["kind"], f["value"] if f["kind"] == "date" else f["name"]) for f in result["facts"])
                wanted["obligations"].update((name, actor, kind) for actor,kind in gold[name]["obligations"])
                produced["obligations"].update((name, o["actor"], o["obligation_type"]) for o in result["obligations"])
                self.assertTrue(all(o["normalized_deadline"] is None and o["review_required"] for o in result["obligations"]))
            report[format] = {key: scores(wanted[key], produced[key]) for key in wanted}
            # Authored fixtures specify exact labels; this is not a tuned customer/legal threshold.
            for key in wanted:
                self.assertEqual(wanted[key], produced[key], (format, key, report[format][key]))
        print("B_GOLDEN_METRICS=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
