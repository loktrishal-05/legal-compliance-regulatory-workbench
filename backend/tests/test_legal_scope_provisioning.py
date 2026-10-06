"""Audited independent provisioning and explicit legacy mapping: SYNTHETIC tenants only.

SQLite in-memory by default; the PostgreSQL subclass reruns the matrix on the approved disposable DB.
"""
from datetime import datetime, timezone
import os
import unittest
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import create_engine, event, select, text
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models import AuditChainHead, AuditEvent, Document, User
from app.db.models.legal_scope import (
    DocumentAccess, LegalDocumentScope, Matter, MatterAccess, Organization, Workspace, WorkspaceMembership,
)
from app.services import legal_provisioning as prov
from app.services.audit import AuditChainError, verify_chain
from app.services.legal_policy import LegalAccessDenied, authorize_document, authorize_workspace

TERMS = "1.0"


class LegalProvisioningTests(unittest.TestCase):
    def make_engine(self):
        engine = create_engine("sqlite:///:memory:")
        event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
        return engine

    def setUp(self):
        self.engine = self.make_engine()
        tables = {m.__table__ for m in (User, Document, AuditEvent, AuditChainHead, Organization, Workspace,
                                        WorkspaceMembership, Matter, MatterAccess, LegalDocumentScope, DocumentAccess)}
        pending = list(tables)
        while pending:  # audit events reference approval tables; include every FK target
            for fk in pending.pop().foreign_keys:
                if fk.column.table not in tables:
                    tables.add(fk.column.table)
                    pending.append(fk.column.table)
        Base.metadata.create_all(self.engine, tables=list(tables))
        self.db = Session(self.engine, expire_on_commit=False)
        self.addCleanup(self.engine.dispose)
        self.addCleanup(self.db.close)
        now = datetime.now(timezone.utc)
        self.admin, self.alice, self.bob = (User(id=uuid4(), username=f"synthetic-{n}", role=r, terms_version=TERMS,
                                                 terms_accepted_at=now)
                                            for n, r in (("admin", "admin"), ("alice", "requester"), ("bob", "reviewer")))
        self.document = Document(id=uuid4(), filename="synthetic-legacy.txt", document_type="contract",
                                 source_path="synthetic/never-read.txt", classification="internal", checksum="a" * 64)
        self.db.add_all([self.admin, self.alice, self.bob, self.document])
        self.db.commit()
        self.ws = prov.bootstrap_workspace(self.db, operator_label="synthetic-operator", organization_name="Tenant A",
                                           workspace_name="Synthetic A", admin_user_id=self.admin.id)
        self.other = prov.bootstrap_workspace(self.db, operator_label="synthetic-operator", organization_name="Tenant B",
                                              workspace_name="Synthetic B", admin_user_id=self.bob.id)
        self.db.commit()

    def events(self, event_type):
        return list(self.db.scalars(select(AuditEvent).where(AuditEvent.event_type == event_type)
                                    .order_by(AuditEvent.sequence_number)))

    def grant(self, user, role="analyst", clearance="internal", admin=None, ws=None):
        member = prov.grant_membership(self.db, admin_id=(admin or self.admin).id, workspace_id=(ws or self.ws).id,
                                       user_id=user.id, role=role, clearance=clearance, current_terms_version=TERMS)
        self.db.commit()
        return member

    def test_bootstrap_is_operator_audited_and_grants_no_review_authority(self):
        boot = self.events("LEGAL_WORKSPACE_BOOTSTRAPPED")
        self.assertEqual(len(boot), 2)
        self.assertEqual((boot[0].actor_kind, boot[0].actor_id), ("system", None))
        self.assertEqual(boot[0].payload["operator_label"], "synthetic-operator")
        context = authorize_workspace(self.db, self.admin.id, self.ws.id, current_terms_version=TERMS)
        self.assertEqual(context.role, "workspace_admin")
        with self.assertRaises(ValueError):
            prov.bootstrap_workspace(self.db, operator_label=" ", organization_name="x", workspace_name="x",
                                     admin_user_id=self.admin.id)
        self.alice.is_active = False
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):
            prov.bootstrap_workspace(self.db, operator_label="op", organization_name="x", workspace_name="x",
                                     admin_user_id=self.alice.id)
        self.assertTrue(verify_chain(self.db)["valid"])

    def test_independent_grant_and_audit(self):
        self.grant(self.alice)
        self.assertEqual(authorize_workspace(self.db, self.alice.id, self.ws.id, current_terms_version=TERMS).role,
                         "analyst")
        granted = self.events("LEGAL_ACCESS_GRANTED")[-1]
        self.assertEqual((granted.actor_id, granted.actor_kind), (self.admin.id, "user"))
        self.assertEqual(granted.payload["target_user_id"], str(self.alice.id))
        self.assertEqual(granted.payload["workspace_id"], str(self.ws.id))

    def test_self_non_admin_cross_workspace_and_over_clearance_grants_denied(self):
        with self.assertRaises(LegalAccessDenied):  # no self-provisioning, including self-elevation
            prov.grant_membership(self.db, admin_id=self.admin.id, workspace_id=self.ws.id, user_id=self.admin.id,
                                  role="legal_reviewer", clearance="internal", current_terms_version=TERMS)
        self.grant(self.alice)
        with self.assertRaises(LegalAccessDenied):  # analysts cannot provision
            prov.grant_membership(self.db, admin_id=self.alice.id, workspace_id=self.ws.id, user_id=self.bob.id,
                                  role="analyst", clearance="public", current_terms_version=TERMS)
        with self.assertRaises(LegalAccessDenied):  # admin of A has no authority in B
            prov.grant_membership(self.db, admin_id=self.admin.id, workspace_id=self.other.id, user_id=self.alice.id,
                                  role="analyst", clearance="public", current_terms_version=TERMS)
        with self.assertRaises(LegalAccessDenied):  # never above the granting admin's clearance
            self.grant(self.bob, clearance="restricted")
        with self.assertRaises(ValueError):
            self.grant(self.bob, role="superuser")
        with self.assertRaises(LegalAccessDenied):  # stale terms deny the admin
            prov.grant_membership(self.db, admin_id=self.admin.id, workspace_id=self.ws.id, user_id=self.bob.id,
                                  role="analyst", clearance="public", current_terms_version="2.0")

    def test_legacy_mapping_document_grants_and_revocation(self):
        doc_kwargs = dict(admin_id=self.admin.id, workspace_id=self.ws.id, document_id=self.document.id,
                          user_id=self.alice.id, current_terms_version=TERMS)
        self.grant(self.alice)
        with self.assertRaises(LegalAccessDenied):  # unmapped legacy document stays quarantined
            prov.set_document_access(self.db, operation="read", active=True, **doc_kwargs)
        prov.map_legacy_document(self.db, operator_label="synthetic-operator", workspace_id=self.ws.id,
                                 document_id=self.document.id, classification="internal")
        self.db.commit()
        mapped = self.events("LEGAL_LEGACY_DOCUMENT_MAPPED")[-1]
        self.assertEqual((mapped.actor_kind, mapped.payload["document_id"]), ("system", str(self.document.id)))
        with self.assertRaises(ValueError):
            prov.map_legacy_document(self.db, operator_label="op", workspace_id=self.other.id,
                                     document_id=self.document.id, classification="internal")
        prov.set_document_access(self.db, operation="read", active=True, **doc_kwargs)
        self.db.commit()
        authorize_document(self.db, self.alice.id, self.ws.id, self.document.id, current_terms_version=TERMS)
        with self.assertRaises(LegalAccessDenied):  # analyst role cannot hold review grants
            prov.set_document_access(self.db, operation="review_legal", active=True, **doc_kwargs)
        prov.set_document_access(self.db, operation="read", active=False, **doc_kwargs)
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):
            authorize_document(self.db, self.alice.id, self.ws.id, self.document.id, current_terms_version=TERMS)
        self.assertEqual(self.events("LEGAL_ACCESS_REVOKED")[-1].payload["operation"], "read")
        self.assertTrue(verify_chain(self.db)["valid"])

    def test_membership_revocation_removes_access_immediately(self):
        prov.map_legacy_document(self.db, operator_label="op", workspace_id=self.ws.id,
                                 document_id=self.document.id, classification="public")
        self.grant(self.alice)
        prov.set_document_access(self.db, admin_id=self.admin.id, workspace_id=self.ws.id,
                                 document_id=self.document.id, user_id=self.alice.id, operation="read",
                                 active=True, current_terms_version=TERMS)
        self.db.commit()
        prov.revoke_membership(self.db, admin_id=self.admin.id, workspace_id=self.ws.id, user_id=self.alice.id,
                               current_terms_version=TERMS)
        self.db.commit()
        for check in (lambda: authorize_workspace(self.db, self.alice.id, self.ws.id, current_terms_version=TERMS),
                      lambda: authorize_document(self.db, self.alice.id, self.ws.id, self.document.id,
                                                 current_terms_version=TERMS)):
            with self.assertRaises(LegalAccessDenied):
                check()

    def test_matter_access_scoped_to_workspace(self):
        matter = Matter(id=uuid4(), organization_id=self.ws.organization_id, workspace_id=self.ws.id, name="M")
        foreign = Matter(id=uuid4(), organization_id=self.other.organization_id, workspace_id=self.other.id, name="F")
        self.db.add_all([matter, foreign])
        self.db.commit()
        self.grant(self.alice)
        kwargs = dict(admin_id=self.admin.id, workspace_id=self.ws.id, user_id=self.alice.id,
                      current_terms_version=TERMS)
        prov.set_matter_access(self.db, matter_id=matter.id, active=True, **kwargs)
        self.db.commit()
        self.assertTrue(self.db.get(MatterAccess, (matter.id, self.alice.id)).is_active)
        with self.assertRaises(LegalAccessDenied):
            prov.set_matter_access(self.db, matter_id=foreign.id, active=True, **kwargs)
        with self.assertRaises(LegalAccessDenied):
            prov.map_legacy_document(self.db, operator_label="op", workspace_id=self.ws.id,
                                     document_id=self.document.id, classification="public", matter_id=foreign.id)

    def test_audit_failure_rolls_back_state_change(self):
        with patch.object(prov, "append_event", side_effect=AuditChainError("synthetic failure")):
            with self.assertRaises(AuditChainError):
                prov.grant_membership(self.db, admin_id=self.admin.id, workspace_id=self.ws.id,
                                      user_id=self.alice.id, role="analyst", clearance="public",
                                      current_terms_version=TERMS)
        self.db.rollback()
        self.assertIsNone(self.db.get(WorkspaceMembership, (self.ws.id, self.alice.id)))


@unittest.skipUnless(os.environ.get("LEGAL_TEST_DATABASE_URL"), "Disposable PostgreSQL not explicitly selected")
class LegalProvisioningPostgresTests(LegalProvisioningTests):
    def make_engine(self):
        from scripts.validate_legal_migrations import disposable_url
        url = disposable_url()
        admin = create_engine(url, connect_args={"connect_timeout": 5})
        schema = "legal_provisioning_" + uuid4().hex
        with admin.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))

        def cleanup():
            with admin.begin() as conn:
                conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            admin.dispose()
        self.addCleanup(cleanup)
        return create_engine(url.update_query_dict({"options": "-csearch_path=" + schema}),
                             connect_args={"connect_timeout": 5})


if __name__ == "__main__":
    unittest.main()
