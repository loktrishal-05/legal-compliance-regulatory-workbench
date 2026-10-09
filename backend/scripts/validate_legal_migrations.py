"""Fresh/0018-to-head acceptance on the explicitly approved disposable DB only."""
import os
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, insert, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session


def disposable_url():
    value = os.environ.get("LEGAL_TEST_DATABASE_URL", "")
    if not value:
        raise ValueError("Explicit LEGAL_TEST_DATABASE_URL is required")
    url = make_url(value)
    if (url.drivername != "postgresql+psycopg" or url.host != "postgres" or url.port != 5432
            or url.database != "legal_core_test" or url.username != "legal_core_test" or url.query):
        raise ValueError("Only the isolated legal-core Compose test database is allowed")
    return url


def main():
    url = disposable_url()  # Reject before settings import, engine or connection.
    from app.core.config import settings
    from app.db.models import AuditEvent, Document, DocumentVersion
    from app.services.audit import AuditChainError, append_event, verify_chain
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    engine = create_engine(url, connect_args={"connect_timeout": 5})
    try:
        for baseline in (None, "0018_terms_acceptance"):
            schema = "legal_migration_" + uuid4().hex
            with engine.begin() as conn:
                conn.execute(text(f'CREATE SCHEMA "{schema}"'))
            scoped_url = url.update_query_dict({"options": "-csearch_path=" + schema})
            scoped_engine = create_engine(scoped_url, connect_args={"connect_timeout": 5})
            try:
                with patch.object(settings, "database_url", scoped_url.render_as_string(hide_password=False)):
                    if baseline:
                        command.upgrade(config, baseline)
                        with Session(scoped_engine) as db:
                            source = Document(filename="synthetic legacy.txt", document_type="manual",
                                source_path="synthetic/never-read", classification="confidential", checksum="c" * 64)
                            db.add(source)
                            db.flush()
                            version_id = uuid4()  # explicit columns: the 0018 schema predates 0022 scope columns
                            db.execute(insert(DocumentVersion.__table__).values(id=version_id, document_id=source.id,
                                source_sha256="c" * 64, status="ready", chunk_count=0, ingestion_metadata={},
                                warnings=[]))
                            event = append_event(db, event_type="LOGIN_FAILURE", actor_id=None,
                                actor_kind="anonymous", payload={"fixture": "synthetic migration preservation"})
                            db.commit()
                            preserved = (source.id, version_id, event.id, event.event_hash)
                        with scoped_engine.connect() as conn:
                            triggers = conn.execute(text("SELECT tgname, pg_get_triggerdef(oid) FROM pg_trigger "
                                "WHERE NOT tgisinternal ORDER BY tgname")).all()
                    command.upgrade(config, "head")
                    command.check(config)
                    command.upgrade(config, "head")
                    if baseline:
                        with Session(scoped_engine) as db:
                            source_id, version_id, event_id, event_hash = preserved
                            assert db.get(Document, source_id).checksum == "c" * 64
                            assert db.get(DocumentVersion, version_id).source_sha256 == "c" * 64
                            assert db.get(AuditEvent, event_id).event_hash == event_hash
                            assert verify_chain(db)["valid"]
                            assert db.execute(text("SELECT COUNT(*) FROM legal_document_scopes")).scalar() == 0
                        with scoped_engine.connect() as conn:
                            current = dict(conn.execute(text("SELECT tgname, pg_get_triggerdef(oid) FROM pg_trigger "
                                "WHERE NOT tgisinternal ORDER BY tgname")).all())
                            assert all(current.get(name) == definition for name, definition in triggers)
                            assert {"immutable_legal_extractions", "immutable_legal_source_spans",
                                    "immutable_truncate_legal_extractions", "immutable_truncate_legal_source_spans",
                                    "immutable_legal_corrections", "immutable_legal_correction_decisions"} <= current.keys()
                    # 0021: reversible without history, accepts provisioning events, refuses lossy downgrade.
                    command.downgrade(config, "0020_legal_policy_audit")
                    command.upgrade(config, "head")
                    with Session(scoped_engine) as db:
                        append_event(db, event_type="LEGAL_ACCESS_GRANTED", actor_id=None, actor_kind="system",
                                     payload={"fixture": "synthetic 0021"})
                        db.commit()
                        try:
                            append_event(db, event_type="UNKNOWN_SYNTHETIC_EVENT", actor_id=None,
                                         actor_kind="system", payload={})
                            db.commit()
                            unknown_accepted = True
                        except AuditChainError:
                            db.rollback()
                            unknown_accepted = False
                        assert not unknown_accepted, "unknown audit event type accepted"
                    # 0022: reversible without scoped versions; per-workspace dedupe; legacy uniqueness kept.
                    command.downgrade(config, "0021_legal_provisioning_audit")
                    command.upgrade(config, "head")
                    org, ws, doc, legacy_doc = uuid4(), uuid4(), uuid4(), uuid4()
                    with scoped_engine.begin() as conn:
                        conn.execute(text("INSERT INTO legal_organizations (id, name) VALUES (:o, 'Synthetic')"), {"o": org})
                        conn.execute(text("INSERT INTO legal_workspaces (id, organization_id, name) "
                                          "VALUES (:w, :o, 'Synthetic')"), {"w": ws, "o": org})
                        for d in (doc, legacy_doc):
                            conn.execute(text("INSERT INTO documents (id, filename, document_type, source_path, "
                                "classification, checksum) VALUES (:d, 's', 'contract', 'synthetic/x', 'internal', "
                                "'d')"), {"d": d})
                        conn.execute(text("INSERT INTO legal_document_scopes (document_id, organization_id, "
                            "workspace_id, classification) VALUES (:d, :o, :w, 'internal')"), {"d": doc, "o": org, "w": ws})
                        version_sql = text("INSERT INTO document_versions (id, document_id, source_sha256, status, "
                            "chunk_count, ingestion_metadata, warnings, organization_id, workspace_id) VALUES (:id, :d, "
                            "'e', 'ready', 0, '{}', '[]', :o, :w)")
                        conn.execute(version_sql, {"id": uuid4(), "d": doc, "o": org, "w": ws})
                        conn.execute(version_sql, {"id": uuid4(), "d": legacy_doc, "o": None, "w": None})
                    for d, o, w in ((doc, org, ws), (legacy_doc, None, None)):
                        try:
                            with scoped_engine.begin() as conn:
                                conn.execute(version_sql, {"id": uuid4(), "d": d, "o": o, "w": w})
                            duplicate_accepted = True
                        except Exception:
                            duplicate_accepted = False
                        assert not duplicate_accepted, "duplicate source bytes accepted in one namespace"
                    try:
                        command.downgrade(config, "0021_legal_provisioning_audit")
                        scoped_downgrade = True
                    except Exception:
                        scoped_downgrade = False
                    assert not scoped_downgrade, "downgrade dropped workspace-scoped versions"
                    with scoped_engine.begin() as conn:
                        conn.execute(text("DELETE FROM document_versions WHERE workspace_id IS NOT NULL"))
                    try:
                        command.downgrade(config, "0020_legal_policy_audit")
                        lossy_downgrade = True
                    except Exception:
                        lossy_downgrade = False
                    assert not lossy_downgrade, "downgrade dropped provisioning audit vocabulary with history"
                    # 0024: qualified FK, raw SQL/ORM-independent immutability and non-lossy downgrade.
                    actor, version, artifact, span = uuid4(), uuid4(), uuid4(), uuid4()
                    sha = "f" * 64
                    with scoped_engine.begin() as conn:
                        conn.execute(text("INSERT INTO users (id, username, role) VALUES (:a, 'synthetic-extractor', 'requester')"), {"a": actor})
                        conn.execute(text("INSERT INTO document_versions (id, document_id, source_sha256, status, chunk_count, "
                            "ingestion_metadata, warnings, organization_id, workspace_id) VALUES "
                            "(:v, :d, :s, 'received', 0, '{}', '[]', :o, :w)"),
                            {"v": version, "d": doc, "s": sha, "o": org, "w": ws})
                        conn.execute(text("INSERT INTO legal_extractions (id, organization_id, workspace_id, document_id, "
                            "version_id, source_sha256, policy_version, extractor, status, text, artifact_sha256, warnings, actor_id) "
                            "VALUES (:id, :o, :w, :d, :v, :s, 'synthetic-v1', 'synthetic', 'ready', 'SYNTHETIC', :s, '[]', :a)"),
                            {"id": artifact, "o": org, "w": ws, "d": doc, "v": version, "s": sha, "a": actor})
                        conn.execute(text('INSERT INTO legal_source_spans (id, organization_id, workspace_id, extraction_id, start, "end", locator) '
                            "VALUES (:id, :o, :w, :e, 0, 9, '{}')"), {"id": span, "o": org, "w": ws, "e": artifact})
                    # New empty dependent tables would fire their own CASCADE guard first.
                    # Verify the original 0024 trigger message at its own revision, then reupgrade.
                    command.downgrade(config, "0024_legal_extraction")
                    for table in ("legal_extractions", "legal_source_spans"):
                        for statement in (f"DELETE FROM {table}", f"UPDATE {table} SET id=id", f"TRUNCATE {table} CASCADE"):
                            try:
                                with scoped_engine.begin() as conn:
                                    conn.execute(text(statement))
                                raise AssertionError("immutable extraction history changed")
                            except Exception as error:
                                if isinstance(error, AssertionError):
                                    raise
                                assert "Legal extractions and source spans are immutable" in str(error)
                    try:
                        command.downgrade(config, "0023_legal_intake_audit")
                        extraction_downgrade = True
                    except Exception as error:
                        assert "Legal extraction history exists" in str(error)
                        extraction_downgrade = False
                    assert not extraction_downgrade, "downgrade dropped immutable extraction history"
                    command.upgrade(config, "head")
                    correction, reviewer = uuid4(), uuid4()
                    with scoped_engine.begin() as conn:
                        conn.execute(text("INSERT INTO users (id, username, role) VALUES (:a, 'synthetic-correction-reviewer', 'reviewer')"), {"a": reviewer})
                        conn.execute(text("INSERT INTO legal_corrections (id, organization_id, workspace_id, span_id, extraction_id, "
                            "actor_id, idempotency_key, original_quote_sha256, correction_sha256, corrected_text, rationale) "
                            "VALUES (:c, :o, :w, :s, :e, :a, :k, :h, :h, 'SYNTHETIC correction', 'Synthetic review')"),
                            {"c": correction, "o": org, "w": ws, "s": span, "e": artifact, "a": actor, "k": uuid4(), "h": sha})
                    decision_sql = text("INSERT INTO legal_correction_decisions (id, organization_id, workspace_id, correction_id, "
                        "correction_sha256, requester_id, reviewer_id, outcome, rationale) "
                        "VALUES (:id, :o, :w, :c, :h, :a, :r, 'approved', 'Synthetic independent review')")
                    try:
                        with scoped_engine.begin() as conn:
                            conn.execute(decision_sql, {"id": uuid4(), "o": org, "w": ws, "c": correction, "h": sha, "a": actor, "r": actor})
                        raise AssertionError("database accepted self-review")
                    except Exception as error:
                        if isinstance(error, AssertionError):
                            raise
                        assert "independent_reviewer" in str(error)
                    with scoped_engine.begin() as conn:
                        conn.execute(decision_sql, {"id": uuid4(), "o": org, "w": ws, "c": correction, "h": sha, "a": actor, "r": reviewer})
                    for table in ("legal_corrections", "legal_correction_decisions"):
                        for statement in (f"DELETE FROM {table}", f"UPDATE {table} SET id=id", f"TRUNCATE {table} CASCADE"):
                            try:
                                with scoped_engine.begin() as conn:
                                    conn.execute(text(statement))
                                raise AssertionError("immutable correction history changed")
                            except Exception as error:
                                if isinstance(error, AssertionError):
                                    raise
                                assert "Legal correction records are immutable" in str(error)
                    try:
                        command.downgrade(config, "0024_legal_extraction")
                        raise AssertionError("downgrade dropped correction history")
                    except Exception as error:
                        if isinstance(error, AssertionError):
                            raise
                        assert "Legal correction history exists" in str(error)
                print(f"PASS: {baseline or 'fresh'} -> head, metadata parity, idempotent upgrade, legacy preservation, "
                      "scope/dedupe, immutable extraction/correction and independent review checks")
            finally:
                scoped_engine.dispose()
                with engine.begin() as conn:
                    conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
