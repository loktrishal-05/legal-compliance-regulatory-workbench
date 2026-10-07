"""Secure legal intake (E1): SYNTHETIC bytes only, temporary data root, SQLite + disposable PostgreSQL."""
import io
import hashlib
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4
import zipfile

from sqlalchemy import func, select

from app.db.models import AuditEvent, Document, DocumentVersion, User
from app.db.models.legal_scope import DocumentAccess, Matter
from app.services import legal_intake as intake
from app.services import legal_provisioning as prov
from app.services.audit import AuditChainError
from app.services.legal_policy import LegalAccessDenied, authorize_document
import test_legal_scope_provisioning as fixtures

TXT = b"SYNTHETIC contract: Party A shall pay Party B within 30 days of invoice.\n"
PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
CLEAN = lambda data: (True, "clean")  # noqa: E731 synthetic scanner


def docx(extra=(), rels=b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", "<w:document>SYNTHETIC clause 1.1</w:document>")
        for name, content in extra:
            archive.writestr(name, content)
    return buffer.getvalue()


class LegalIntakeTests(unittest.TestCase):
    make_engine = fixtures.LegalProvisioningTests.make_engine

    def setUp(self):
        fixtures.LegalProvisioningTests.setUp(self)
        self.root = Path(tempfile.mkdtemp(prefix="legal-intake-"))
        self.grant(self.alice, role="analyst", clearance="internal")

    def grant(self, user, role="analyst", clearance="internal", admin=None, ws=None):
        return fixtures.LegalProvisioningTests.grant(self, user, role, clearance, admin, ws)

    def receive(self, data, filename="synthetic.txt", user=None, ws=None, scanner=CLEAN, **kw):
        result = intake.receive(self.db, actor_id=(user or self.alice).id, workspace_id=(ws or self.ws).id,
                                filename=filename, document_type=kw.pop("document_type", "contract"),
                                classification=kw.pop("classification", "internal"), data=data,
                                current_terms_version=fixtures.TERMS, data_root=self.root, scanner=scanner, **kw)
        self.db.commit()
        return result

    def events(self, event_type):
        return list(self.db.scalars(select(AuditEvent).where(AuditEvent.event_type == event_type)))

    def test_clean_upload_preserves_original_scopes_and_grants_read_only(self):
        result = self.receive(TXT)
        self.assertEqual((result.status, result.duplicate, result.quarantine_reasons), ("received", False, ()))
        version = self.db.get(DocumentVersion, result.version_id)
        document = self.db.get(Document, result.document_id)
        self.assertEqual((version.organization_id, version.workspace_id), (self.ws.organization_id, self.ws.id))
        stored = Path(self.root, *document.source_path.split("/"))
        self.assertEqual(stored.read_bytes(), TXT)
        self.assertEqual(stat.S_IMODE(stored.stat().st_mode) & 0o222, 0)  # write-once, read-only original
        self.assertEqual(document.checksum, version.source_sha256)
        authorize_document(self.db, self.alice.id, self.ws.id, document.id, current_terms_version=fixtures.TERMS)
        with self.assertRaises(LegalAccessDenied):  # uploader gets read only, never propose/review
            authorize_document(self.db, self.alice.id, self.ws.id, document.id, operation="propose",
                               current_terms_version=fixtures.TERMS)
        received = self.events("LEGAL_DOCUMENT_RECEIVED")[-1]
        self.assertEqual(received.payload["version_id"], str(version.id))
        self.assertNotIn("synthetic.txt", str(received.payload))

    def test_quarantine_reasons(self):
        cases = [(TXT, "a.txt", None, "malware_scanner_not_configured"),
                 (TXT + b"x", "b.txt", lambda d: (False, "SYNTHETIC-SIGNATURE"), "malware_scan:SYNTHETIC-SIGNATURE"),
                 (PDF.replace(b"<<>>endobj", b"<</JavaScript 1>>endobj"), "c.pdf", CLEAN, "pdf_active_content:JavaScript"),
                 (PDF.replace(b"trailer", b"PK\x03\x04 trailer"), "d.pdf", CLEAN, "embedded_archive"),
                 (docx(rels=b'<Relationship TargetMode="External" Target="http://x.invalid"/>'), "e.docx", CLEAN,
                  "external_reference"),
                 (docx([("word/embeddings/oleObject1.bin", b"x")]), "f.docx", CLEAN, "embedded_object")]
        for data, name, scanner, reason in cases:
            result = self.receive(data, name, scanner=scanner)
            self.assertEqual(result.status, "quarantined", name)
            self.assertIn(reason, result.quarantine_reasons, name)
            self.assertEqual(self.db.get(Document, result.document_id).ingestion_status, "quarantined")

    def test_clean_pdf_and_docx_received(self):
        self.assertEqual(self.receive(PDF, "contract.pdf").status, "received")
        self.assertEqual(self.receive(docx(), "contract.docx").status, "received")

    def test_rejections_are_audited_and_store_nothing(self):
        bomb = docx([("word/media/zeros.xml", b"\0" * (20 * 1024 * 1024))])
        cases = {"empty": (b"", "a.txt"), "macro_content": (docx([("word/vbaProject.bin", b"x")]), "a.docx"),
                 "unsafe_archive_path": (docx([("../escape.txt", b"x")]), "a.docx"), "archive_limits": (bomb, "a.docx"),
                 "type_mismatch": (TXT, "contract.pdf"), "binary_content": (b"SYNTHETIC\x00\x01", "a.txt"),
                 "unsupported_type": (b"\x89PNG\r\n\x1a\n\xff\xfe", "a.png"), "malformed_pdf": (b"%PDF-1.4 no end", "a.pdf"),
                 "malformed_docx": (docx().replace(b"word/document.xml", b"word/documenX.xml"), "a.docx"),
                 "invalid_filename": (TXT, "..")}
        for code, (data, name) in cases.items():
            with self.assertRaises(intake.IntakeRejected) as rejected:
                self.receive(data, name)
            self.assertEqual(rejected.exception.code, code)
        with patch.object(intake, "MAX_BYTES", 10), self.assertRaises(intake.IntakeRejected) as large:
            self.receive(TXT)
        self.assertEqual(large.exception.code, "too_large")
        with self.assertRaises(intake.IntakeRejected):  # validated before inspection, so not audited
            self.receive(TXT, document_type="Contract; DROP")
        self.assertEqual(len(self.events("LEGAL_INTAKE_REJECTED")), len(cases) + 1)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(Document)), 1)  # fixture legacy doc only
        self.assertEqual([p for p in self.root.rglob("*") if p.is_file()], [])

    def test_workspace_dedupe_is_idempotent_and_never_cross_tenant(self):
        first = self.receive(TXT)
        again = self.receive(TXT)
        self.assertEqual((again.duplicate, again.version_id), (True, first.version_id))
        self.grant(self.bob, role="analyst", clearance="internal")  # same workspace, no read grant
        with self.assertRaises(intake.IntakeConflict):
            self.receive(TXT, user=self.bob)
        carol = User(id=uuid4(), username="synthetic-carol", role="requester", terms_version=fixtures.TERMS,
                     terms_accepted_at=self.alice.terms_accepted_at)
        self.db.add(carol)
        self.db.commit()
        self.grant(carol, role="analyst", clearance="internal", admin=self.bob, ws=self.other)
        other = self.receive(TXT, user=carol, ws=self.other)
        self.assertFalse(other.duplicate)
        self.assertNotEqual(other.version_id, first.version_id)
        sha = self.db.get(DocumentVersion, first.version_id).source_sha256
        self.assertEqual(self.db.scalar(select(func.count()).select_from(DocumentVersion)
                                        .where(DocumentVersion.source_sha256 == sha)), 2)

    def test_access_rules(self):
        self.grant(self.bob, role="viewer", clearance="internal")
        with self.assertRaises(LegalAccessDenied):  # viewers cannot upload
            self.receive(TXT, user=self.bob)
        with self.assertRaises(LegalAccessDenied):  # never above own clearance
            self.receive(TXT, classification="restricted")
        with self.assertRaises(LegalAccessDenied):  # not a member of the other workspace
            self.receive(TXT, ws=self.other)
        foreign = Matter(id=uuid4(), organization_id=self.other.organization_id, workspace_id=self.other.id, name="F")
        local = Matter(id=uuid4(), organization_id=self.ws.organization_id, workspace_id=self.ws.id, name="L")
        self.db.add_all([foreign, local])
        self.db.commit()
        for matter in (foreign, local):  # foreign matter, or local matter without matter access
            with self.assertRaises(LegalAccessDenied):
                self.receive(TXT, matter_id=matter.id)
        prov.set_matter_access(self.db, admin_id=self.admin.id, workspace_id=self.ws.id, matter_id=local.id,
                               user_id=self.alice.id, active=True, current_terms_version=fixtures.TERMS)
        self.db.commit()
        result = self.receive(TXT, matter_id=local.id)
        authorize_document(self.db, self.alice.id, self.ws.id, result.document_id, current_terms_version=fixtures.TERMS)

    def test_stored_original_tampering_detected(self):
        sha = hashlib.sha256(TXT).hexdigest()
        relative = intake.store_original(self.root, self.ws.organization_id, self.ws.id, sha, "txt", TXT)
        path = Path(self.root, *relative.split("/"))
        os.chmod(path, 0o600)
        path.write_bytes(b"tampered")
        with self.assertRaises(intake.IntakeIntegrityError):
            intake.store_original(self.root, self.ws.organization_id, self.ws.id, sha, "txt", TXT)

    def test_duplicate_rechecks_original_integrity(self):
        result = self.receive(TXT)
        document = self.db.get(Document, result.document_id)
        path = self.root / document.source_path
        os.chmod(path, 0o600)
        path.write_bytes(b"SYNTHETIC tampering")
        with self.assertRaises(intake.IntakeIntegrityError):
            self.receive(TXT)

    def test_missing_duplicate_original_is_not_silently_recreated(self):
        result = self.receive(TXT)
        path = self.root / self.db.get(Document, result.document_id).source_path
        path.unlink()
        with self.assertRaises(intake.IntakeIntegrityError):
            self.receive(TXT)
        self.assertFalse(path.exists())

    def test_original_symlink_is_not_followed(self):
        sha = hashlib.sha256(TXT).hexdigest()
        relative = intake.store_original(self.root, self.ws.organization_id, self.ws.id, sha, "txt", TXT)
        path = self.root / relative
        path.unlink()
        target = self.root / "synthetic-target.txt"
        target.write_bytes(TXT)
        path.symlink_to(target)
        with self.assertRaises(intake.IntakeIntegrityError):
            intake.store_original(self.root, self.ws.organization_id, self.ws.id, sha, "txt", TXT)
        self.assertTrue(path.is_symlink())
        self.assertEqual(target.read_bytes(), TXT)

    def test_content_address_must_match_bytes_before_storage(self):
        with self.assertRaises(intake.IntakeIntegrityError):
            intake.store_original(self.root, self.ws.organization_id, self.ws.id, "a" * 64, "txt", TXT)
        self.assertFalse((self.root / "legal").exists())

    def test_existing_original_is_not_replaced_during_publication_race(self):
        sha = hashlib.sha256(TXT).hexdigest()
        path = self.root / "legal" / "originals" / str(self.ws.organization_id) / str(self.ws.id) / f"{sha}.txt"
        real_open = open

        def race_open(name, mode="r", *args, **kwargs):
            if mode == "xb":
                path.write_bytes(b"SYNTHETIC concurrent corrupt original")
            return real_open(name, mode, *args, **kwargs)

        with patch("builtins.open", side_effect=race_open):
            with self.assertRaises(intake.IntakeIntegrityError):
                intake.store_original(self.root, self.ws.organization_id, self.ws.id, sha, "txt", TXT)
        self.assertEqual(path.read_bytes(), b"SYNTHETIC concurrent corrupt original")
        self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_ambiguous_docx_rejection_keeps_audit_and_no_original(self):
        data = docx([("WORD/DOCUMENT.XML", "<document>SYNTHETIC conflicting text</document>")])
        with self.assertRaises(intake.IntakeRejected) as rejected:
            self.receive(data, "ambiguous.docx")
        self.assertEqual(rejected.exception.code, "ambiguous_archive")
        self.assertEqual(self.events("LEGAL_INTAKE_REJECTED")[-1].payload["code"], "ambiguous_archive")
        self.assertFalse((self.root / "legal").exists())

    def test_audit_failure_rolls_back_intake_rows(self):
        with patch.object(intake, "append_event", side_effect=AuditChainError("synthetic failure")):
            with self.assertRaises(AuditChainError):
                intake.receive(self.db, actor_id=self.alice.id, workspace_id=self.ws.id, filename="a.txt",
                               document_type="contract", classification="internal", data=TXT,
                               current_terms_version=fixtures.TERMS, data_root=self.root, scanner=CLEAN)
        self.db.rollback()
        self.assertEqual(self.db.scalar(select(func.count()).select_from(DocumentAccess)), 0)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(DocumentVersion)), 0)


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not explicitly selected")
class LegalIntakePostgresTests(LegalIntakeTests):
    make_engine = fixtures.LegalProvisioningPostgresTests.make_engine


class LegalArchiveInspectionTests(unittest.TestCase):
    """Synthetic OOXML edge cases; never execute links, entities or embedded content."""

    def test_external_relationship_xml_spellings_are_quarantined(self):
        for attribute in ("TargetMode='External'", 'TargetMode = "External"',
                          'TargetMode="Ext&#101;rnal"'):
            with self.subTest(attribute=attribute):
                xml = f'<Relationships><Relationship {attribute} Target="https://synthetic.invalid"/></Relationships>'
                self.assertIn("external_reference", intake.inspect(docx(rels=xml.encode()), "a.docx").quarantine_reasons)
        xml = '<Relationships><Relationship TargetMode="External" Target="https://synthetic.invalid"/></Relationships>'
        self.assertIn("external_reference", intake.inspect(docx(rels=xml.encode("utf-16")), "a.docx").quarantine_reasons)

    def test_invalid_relationship_xml_rejected(self):
        for xml in (b"<Relationships>", b"<!DOCTYPE R [<!ENTITY x 'External'>]><R/>"):
            with self.subTest(xml=xml):
                with self.assertRaises(intake.IntakeRejected) as error:
                    intake.inspect(docx(rels=xml), "a.docx")
                self.assertEqual(error.exception.code, "malformed_docx")

    def test_duplicate_and_case_colliding_members_rejected(self):
        for name in ("word/document.xml", "WORD/DOCUMENT.XML"):
            with self.subTest(name=name):
                with self.assertRaises(intake.IntakeRejected) as error:
                    intake.inspect(docx([(name, "<document/>")]), "a.docx")
                self.assertEqual(error.exception.code, "ambiguous_archive")

    def test_unsupported_compression_has_stable_rejection(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_BZIP2) as archive:
            archive.writestr("[Content_Types].xml", "<Types/>")
            archive.writestr("word/document.xml", "<document/>")
        with self.assertRaises(intake.IntakeRejected) as error:
            intake.inspect(buffer.getvalue(), "a.docx")
        self.assertEqual(error.exception.code, "unsupported_archive_compression")

    def test_xml_limit_and_macro_content_type_rejected(self):
        with patch.object(intake, "DOCX_MAX_XML_BYTES", 8), self.assertRaises(intake.IntakeRejected) as error:
            intake.inspect(docx(), "a.docx")
        self.assertEqual(error.exception.code, "archive_limits")
        data = docx([("word/macro-types.xml", '<Override ContentType="application/vnd.ms-word.document.macroEnabled.main+xml"/>')])
        with self.assertRaises(intake.IntakeRejected) as error:
            intake.inspect(data, "a.docx")
        self.assertEqual(error.exception.code, "macro_content")


if __name__ == "__main__":
    unittest.main()
