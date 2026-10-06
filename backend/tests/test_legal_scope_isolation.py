"""Workspace-scoped dedupe (0022) and legacy-path isolation: SYNTHETIC tenants/bytes only."""
from pathlib import Path
import os
import unittest
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models import AuditEvent, Document, DocumentVersion
from app.db.models.legal_scope import LegalDocumentScope
from app.services import legal_provisioning as prov
from app.services.audit import append_event
from app.services.legal_policy import (
    LEGAL_AUDIT_EVENT_TYPES, is_legacy_document, is_legacy_version, legacy_version_clause, without_legal_audit,
)
import test_legal_scope_provisioning as fixtures

APP = Path(__file__).resolve().parents[1] / "app"
SERVICES = APP / "services"
# Every old industrial path that reads, dedupes or indexes DocumentVersion rows must apply the guard.
GUARDED = {"ingestion.py": "legacy_version_clause", "pid_processing.py": "legacy_version_clause",
           "retrieval.py": "legacy_version_clause", "pid_reads.py": "legacy_version_clause",
           "verified_knowledge.py": "is_legacy_version", "pid_evidence.py": "is_legacy_version",
           "evidence_integrity.py": "is_legacy_version", "knowledge_gaps.py": "is_legacy_version",
           "pid_indexing.py": "is_legacy_version", "evidence_sufficiency.py": "is_legacy_version"}


class LegalIsolationTests(unittest.TestCase):
    make_engine = fixtures.LegalProvisioningTests.make_engine
    setUp = fixtures.LegalProvisioningTests.setUp

    def version(self, document, sha, ws=None):
        row = DocumentVersion(document_id=document.id, source_sha256=sha, status="indexed", chunk_count=0,
                              ingestion_metadata={}, warnings=[],
                              organization_id=ws.organization_id if ws else None, workspace_id=ws.id if ws else None)
        self.db.add(row)
        self.db.flush()
        return row

    def scoped_document(self, ws, name):
        doc = Document(id=uuid4(), filename=name, document_type="contract", source_path="synthetic/x",
                       classification="internal", checksum="f" * 64)
        self.db.add(doc)
        self.db.flush()
        self.db.add(LegalDocumentScope(document_id=doc.id, organization_id=ws.organization_id,
                                       workspace_id=ws.id, classification="internal"))
        self.db.flush()
        return doc

    def assert_rejected(self, action):
        with self.assertRaises(IntegrityError):
            action()
        self.db.rollback()

    def test_same_bytes_allowed_across_workspaces_but_unique_within_one(self):
        doc_a, doc_b = self.scoped_document(self.ws, "a"), self.scoped_document(self.other, "b")
        self.version(doc_a, "1" * 64, self.ws)
        self.version(doc_b, "1" * 64, self.other)  # no global duplicate reveals tenant A's copy
        self.version(self.document, "1" * 64)  # legacy namespace is independent
        self.db.commit()
        doc_a2 = self.scoped_document(self.ws, "a2")
        self.assert_rejected(lambda: self.version(doc_a2, "1" * 64, self.ws))

    def test_legacy_global_uniqueness_preserved(self):
        self.version(self.document, "2" * 64)
        self.db.commit()
        self.assert_rejected(lambda: self.version(self.document, "2" * 64))

    def test_version_scope_must_match_its_document_scope(self):
        doc_a = self.scoped_document(self.ws, "a")
        self.db.commit()
        self.assert_rejected(lambda: self.version(doc_a, "3" * 64, self.other))  # foreign workspace
        self.assert_rejected(lambda: self.version(self.document, "4" * 64, self.ws))  # unscoped document

    def test_pair_check_rejects_half_scoped_version(self):
        def half():
            self.db.add(DocumentVersion(document_id=self.document.id, source_sha256="5" * 64, status="indexed",
                                        chunk_count=0, ingestion_metadata={}, warnings=[],
                                        organization_id=self.ws.organization_id))
            self.db.flush()
        self.assert_rejected(half)

    def test_legacy_clause_hides_scoped_and_mapped_content(self):
        legacy = self.version(self.document, "6" * 64)
        scoped = self.version(self.scoped_document(self.ws, "a"), "7" * 64, self.ws)
        self.db.commit()
        self.assertEqual(set(self.db.scalars(select(DocumentVersion.id).where(legacy_version_clause()))), {legacy.id})
        self.assertTrue(is_legacy_version(self.db, legacy))
        self.assertFalse(is_legacy_version(self.db, scoped))
        self.assertFalse(is_legacy_version(self.db, None))
        prov.map_legacy_document(self.db, operator_label="synthetic-operator", workspace_id=self.ws.id,
                                 document_id=self.document.id, classification="internal")
        self.db.commit()
        self.db.refresh(legacy)
        self.assertEqual((legacy.organization_id, legacy.workspace_id), (self.ws.organization_id, self.ws.id))
        self.assertEqual(set(self.db.scalars(select(DocumentVersion.id).where(legacy_version_clause()))), set())
        self.assertFalse(is_legacy_document(self.db, self.document.id))
        mapped = self.db.scalars(select(AuditEvent).where(AuditEvent.event_type == "LEGAL_LEGACY_DOCUMENT_MAPPED")).one()
        self.assertEqual(mapped.payload["version_ids"], [str(legacy.id)])

    def test_owned_document_hides_unstamped_legacy_namespace_version(self):
        doc = self.scoped_document(self.ws, "owned")
        unstamped = self.version(doc, "9" * 64)  # NULL workspace, but its document has legal ownership
        self.db.commit()
        self.assertNotIn(unstamped.id, set(self.db.scalars(select(DocumentVersion.id).where(legacy_version_clause()))))
        self.assertFalse(is_legacy_version(self.db, unstamped))

    def test_mapping_refuses_duplicate_bytes_in_target_workspace(self):
        self.version(self.document, "8" * 64)
        self.version(self.scoped_document(self.ws, "a"), "8" * 64, self.ws)
        self.db.commit()
        with self.assertRaises(ValueError):
            prov.map_legacy_document(self.db, operator_label="op", workspace_id=self.ws.id,
                                     document_id=self.document.id, classification="internal")

    def test_every_legacy_path_applies_the_guard(self):
        for name, guard in GUARDED.items():
            self.assertIn(guard, (SERVICES / name).read_text(encoding="utf-8"), name)
        self.assertIn("without_legal_audit(", (APP / "api" / "routes" / "audit.py").read_text(encoding="utf-8"))

    def test_root_audit_reads_exclude_legal_events(self):
        append_event(self.db, event_type="LOGIN_FAILURE", actor_id=None, actor_kind="anonymous",
                     payload={"fixture": "synthetic industrial event"})
        append_event(self.db, event_type="SECURITY_POLICY_DENIED", actor_id=None, actor_kind="system", payload={})
        self.db.commit()
        all_types = set(self.db.scalars(select(AuditEvent.event_type)))
        self.assertTrue({"LEGAL_WORKSPACE_BOOTSTRAPPED", "SECURITY_POLICY_DENIED"} <= all_types)
        visible = set(self.db.scalars(without_legal_audit(select(AuditEvent.event_type))))
        self.assertEqual(visible, {"LOGIN_FAILURE"})
        self.assertFalse(visible & set(LEGAL_AUDIT_EVENT_TYPES))


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not explicitly selected")
class LegalIsolationPostgresTests(LegalIsolationTests):
    make_engine = fixtures.LegalProvisioningPostgresTests.make_engine


if __name__ == "__main__":
    unittest.main()
