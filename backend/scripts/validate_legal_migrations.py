"""Fresh/0018-to-head acceptance on the explicitly approved disposable DB only."""
import os
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
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
                            version = DocumentVersion(document_id=source.id, source_sha256="c" * 64,
                                status="ready", chunk_count=0, ingestion_metadata={}, warnings=[])
                            db.add(version)
                            event = append_event(db, event_type="LOGIN_FAILURE", actor_id=None,
                                actor_kind="anonymous", payload={"fixture": "synthetic migration preservation"})
                            db.commit()
                            preserved = (source.id, version.id, event.id, event.event_hash)
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
                            assert triggers == conn.execute(text("SELECT tgname, pg_get_triggerdef(oid) FROM pg_trigger "
                                "WHERE NOT tgisinternal ORDER BY tgname")).all()
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
                    try:
                        command.downgrade(config, "0020_legal_policy_audit")
                        lossy_downgrade = True
                    except Exception:
                        lossy_downgrade = False
                    assert not lossy_downgrade, "downgrade dropped provisioning audit vocabulary with history"
                print(f"PASS: {baseline or 'fresh'} -> head, metadata parity, idempotent upgrade, 0021 audit vocabulary")
            finally:
                scoped_engine.dispose()
                with engine.begin() as conn:
                    conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
