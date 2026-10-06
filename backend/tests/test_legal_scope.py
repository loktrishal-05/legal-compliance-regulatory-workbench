"""Synthetic legal scope checks: in-memory SQLite only, no private settings/services."""
from datetime import datetime, timezone
from uuid import uuid4
import unittest

from sqlalchemy import create_engine, event, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models import User, Document
from app.db.models.legal_scope import (
    Organization, Workspace, WorkspaceMembership, Matter, MatterAccess,
    LegalDocumentScope, DocumentAccess,
)
from app.services.legal_policy import LegalAccessDenied, authorize_document, authorize_workspace


class LegalScopeTests(unittest.TestCase):
    def make_engine(self):
        engine = create_engine("sqlite:///:memory:")
        event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
        return engine

    def setUp(self):
        self.engine = self.make_engine()
        tables = [User.__table__, Document.__table__] + [m.__table__ for m in (
            Organization, Workspace, WorkspaceMembership, Matter, MatterAccess,
            LegalDocumentScope, DocumentAccess)]
        Base.metadata.create_all(self.engine, tables=tables)
        self.db = Session(self.engine, expire_on_commit=False)
        self.addCleanup(self.engine.dispose)
        self.addCleanup(self.db.close)
        self.actor = User(id=uuid4(), username="synthetic-analyst", role="requester",
                          terms_version="1.0", terms_accepted_at=datetime.now(timezone.utc))
        self.org = Organization(id=uuid4(), name="Synthetic tenant A")
        self.other_org = Organization(id=uuid4(), name="Synthetic tenant B")
        self.db.add_all([self.actor, self.org, self.other_org])
        self.db.flush()
        self.workspace = Workspace(id=uuid4(), organization_id=self.org.id, name="Synthetic A")
        self.other_workspace = Workspace(id=uuid4(), organization_id=self.other_org.id, name="Synthetic B")
        self.db.add_all([self.workspace, self.other_workspace])
        self.db.flush()
        self.member = WorkspaceMembership(organization_id=self.org.id, workspace_id=self.workspace.id,
            user_id=self.actor.id, role="analyst", clearance="confidential")
        self.matter = Matter(id=uuid4(), organization_id=self.org.id, workspace_id=self.workspace.id,
                             name="Synthetic contract matter")
        self.document = Document(id=uuid4(), filename="synthetic.txt", document_type="contract",
            source_path="synthetic/never-read.txt", classification="confidential", checksum="a" * 64)
        self.db.add_all([self.member, self.matter, self.document])
        self.db.flush()
        self.scope = LegalDocumentScope(document_id=self.document.id, organization_id=self.org.id,
            workspace_id=self.workspace.id, matter_id=self.matter.id, classification="confidential")
        self.db.add(self.scope)
        self.db.commit()

    def grant(self, operation="read"):
        self.db.add(DocumentAccess(organization_id=self.org.id, workspace_id=self.workspace.id,
            document_id=self.document.id, user_id=self.actor.id, operation=operation))
        if self.db.get(MatterAccess, (self.matter.id, self.actor.id)) is None:
            self.db.add(MatterAccess(organization_id=self.org.id, workspace_id=self.workspace.id,
                                    matter_id=self.matter.id, user_id=self.actor.id))
        self.db.commit()

    def authorize(self, operation="read", **kwargs):
        return authorize_document(self.db, self.actor.id, self.workspace.id, self.document.id,
                                  operation=operation, current_terms_version="1.0", **kwargs)

    def test_membership_does_not_grant_content_and_unknown_ids_look_identical(self):
        with self.assertRaises(LegalAccessDenied) as denied:
            self.authorize()
        with self.assertRaises(LegalAccessDenied) as missing:
            authorize_document(self.db, self.actor.id, self.workspace.id, uuid4(),
                               current_terms_version="1.0")
        self.assertEqual(str(denied.exception), str(missing.exception))
        self.grant()
        context = self.authorize()
        self.assertEqual((context.organization_id, context.workspace_id, context.actor_id),
                         (self.org.id, self.workspace.id, self.actor.id))

    def test_cross_workspace_and_unmapped_legacy_documents_are_denied(self):
        self.grant()
        for workspace in (self.other_workspace.id, uuid4()):
            with self.assertRaises(LegalAccessDenied):
                authorize_document(self.db, self.actor.id, workspace, self.document.id,
                                   current_terms_version="1.0")
        legacy = Document(id=uuid4(), filename="legacy.txt", document_type="manual",
                          source_path="legacy/never-read", classification="public")
        self.db.add(legacy)
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):
            authorize_document(self.db, self.actor.id, self.workspace.id, legacy.id,
                               current_terms_version="1.0")

    def test_matter_and_classification_narrow_document_grants(self):
        self.grant()
        self.db.execute(update(MatterAccess).values(is_active=False))
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):
            self.authorize()
        self.db.execute(update(MatterAccess).values(is_active=True))
        self.db.execute(update(WorkspaceMembership).values(clearance="internal"))
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):
            self.authorize()

    def test_revocation_is_reloaded_even_with_cached_orm_objects(self):
        self.grant()
        self.authorize()
        self.db.execute(update(WorkspaceMembership).values(is_active=False),
                        execution_options={"synchronize_session": False})
        self.db.commit()
        self.assertTrue(self.member.is_active)  # deliberately stale identity-map instance
        with self.assertRaises(LegalAccessDenied):
            self.authorize()

    def test_inactive_account_tenant_workspace_matter_and_document_deny(self):
        self.grant()
        for model in (User, Organization, Workspace, Matter, LegalDocumentScope, DocumentAccess):
            with self.subTest(model=model.__name__):
                self.db.execute(update(model).values(is_active=False))
                self.db.commit()
                with self.assertRaises(LegalAccessDenied):
                    self.authorize()
                self.db.execute(update(model).values(is_active=True))
                self.db.commit()
        self.actor.signup_pending = True
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):
            self.authorize()

    def test_terms_and_platform_admin_are_not_bypassed(self):
        self.actor.role = "admin"
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):
            self.authorize()
        self.grant()
        self.actor.terms_version = "old"
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):
            self.authorize()

    def test_operation_role_matrix_and_independent_review(self):
        for operation in ("read", "propose", "review_legal", "review_compliance"):
            self.grant(operation)
        expected = {
            "analyst": {"read", "propose"}, "legal_reviewer": {"read", "propose", "review_legal"},
            "compliance_reviewer": {"read", "propose", "review_compliance"},
            "business_owner": {"read"}, "auditor": {"read"}, "viewer": {"read"},
            "workspace_admin": {"read"},
        }
        self.actor.role = "reviewer"
        for role, operations in expected.items():
            self.member.role = role
            self.db.commit()
            for operation in ("read", "propose", "review_legal", "review_compliance", "delete"):
                with self.subTest(role=role, operation=operation):
                    if operation in operations:
                        self.authorize(operation, requester_id=uuid4())
                    else:
                        with self.assertRaises(LegalAccessDenied):
                            self.authorize(operation, requester_id=uuid4())
        self.member.role = "legal_reviewer"
        self.db.commit()
        for requester in (None, self.actor.id):
            with self.assertRaises(LegalAccessDenied):
                self.authorize("review_legal", requester_id=requester)
        self.actor.role = "requester"
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):
            self.authorize("review_legal", requester_id=uuid4())

    def test_workspace_context_requires_membership_even_for_admin(self):
        context = authorize_workspace(self.db, self.actor.id, self.workspace.id, current_terms_version="1.0")
        self.assertEqual(context.role, "analyst")
        self.actor.role = "admin"
        self.db.commit()
        with self.assertRaises(LegalAccessDenied):
            authorize_workspace(self.db, self.actor.id, self.other_workspace.id, current_terms_version="1.0")

    def test_database_rejects_cross_tenant_matter_scope_and_grant(self):
        foreign_matter = Matter(id=uuid4(), organization_id=self.other_org.id,
                               workspace_id=self.other_workspace.id, name="Synthetic foreign matter")
        self.db.add(foreign_matter)
        self.db.commit()
        bad_rows = [
            Matter(organization_id=self.org.id, workspace_id=self.other_workspace.id, name="Wrong tenant"),
            DocumentAccess(organization_id=self.other_org.id, workspace_id=self.other_workspace.id,
                document_id=self.document.id, user_id=self.actor.id, operation="read"),
            MatterAccess(organization_id=self.org.id, workspace_id=self.workspace.id,
                matter_id=foreign_matter.id, user_id=self.actor.id),
        ]
        for row in bad_rows:
            with self.subTest(model=type(row).__name__), self.assertRaises(IntegrityError):
                with self.db.begin_nested():
                    self.db.add(row)
                    self.db.flush()
        with self.assertRaises(IntegrityError):
            with self.db.begin_nested():
                self.db.execute(update(LegalDocumentScope).values(matter_id=foreign_matter.id))

    def test_roles_clearances_operations_and_duplicate_ownership_constrained(self):
        for model, values in (
            (WorkspaceMembership, {"role": "admin"}),
            (WorkspaceMembership, {"clearance": "unknown"}),
            (LegalDocumentScope, {"classification": "unknown"}),
        ):
            with self.subTest(values=values), self.assertRaises(IntegrityError):
                with self.db.begin_nested():
                    self.db.execute(update(model).values(**values))
        with self.assertRaises(IntegrityError):
            with self.db.begin_nested():
                self.db.add(DocumentAccess(organization_id=self.org.id, workspace_id=self.workspace.id,
                    document_id=self.document.id, user_id=self.actor.id, operation="delete"))
                self.db.flush()
        with self.assertRaises(IntegrityError):
            with self.db.begin_nested():
                self.db.execute(insert(LegalDocumentScope).values(document_id=self.document.id,
                    organization_id=self.other_org.id, workspace_id=self.other_workspace.id, classification="public"))
        self.assertEqual(self.db.scalar(select(Document.checksum)), "a" * 64)


if __name__ == "__main__":
    unittest.main()
