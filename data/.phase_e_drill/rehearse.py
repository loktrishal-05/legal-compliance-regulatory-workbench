import importlib.util
from pathlib import Path
import shutil
import subprocess
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import patch

import httpx
from sqlalchemy import create_engine, text, select, func
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from alembic import command
from alembic.config import Config
import test_advanced_c
from test_phase5a import state
from app.core.config import settings
from app.db.models import User, DurableExecution, VerifiedKnowledge, AuditEvent
from app.schemas.query import QueryRequest
from app.services.governance import create_revision
from app.services.audit import verify_chain, append_event

ROOT = Path('C:/Users/Lohith k/Desktop/sovereign-deployment')
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('drill_backup', HERE.parent / '.phase_e_stage/backend/scripts/backup.py')
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)
backup.ROOT = ROOT
names = ['phase_e_backup_' + uuid4().hex, 'phase_e_restore_' + uuid4().hex]
base = make_url(settings.database_url)
admin = create_engine(base, isolation_level='AUTOCOMMIT')
engines = []
created = []
folder = HERE / uuid4().hex
data = folder / 'source'
models = folder / 'models'
data.mkdir(parents=True)
models.mkdir()
(data / 'manifest.json').write_text('synthetic source manifest')
compose = ['docker', 'compose', '-f', str(ROOT / 'infra/docker-compose.yml')]

def run(args, **kwargs):
    return subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)

try:
    with admin.connect() as conn:
        for name in names:
            conn.execute(text(f'CREATE DATABASE "{name}"'))
            created.append(name)
    source_url, target_url = [base.set(database=name).render_as_string(hide_password=False) for name in names]
    with patch.object(settings, 'database_url', source_url):
        command.upgrade(Config(str(ROOT / 'backend/alembic.ini')), 'head')
    source = create_engine(source_url)
    engines.append(source)
    with Session(source) as session:
        user = User(username='recovery-test', role='requester')
        session.add(user)
        session.flush()
        rev = create_revision(session, QueryRequest(query='Synthetic recovery check'), state(), requester_user_id=user.id)
        append_event(session, event_type='LOGIN_SUCCESS', actor_id=user.id, actor_kind='user', payload={'synthetic': True})
        session.add(DurableExecution(id=uuid4(), user_id=user.id, request={'synthetic': True},
                    status='INTERRUPTED', selected_model='qwen3.5:9b', execution_path='graph', updated_at=datetime.now(timezone.utc)))
        session.add(VerifiedKnowledge(title='Recovery candidate', question='Synthetic?', match_key='a'*64,
                    statement='Synthetic only', evidence=[], source_snapshot=[], content_hash='b'*64,
                    access_scope='internal', approval_revision_id=rev.id, created_by=user.id,
                    updated_at=datetime.now(timezone.utc)))
        session.commit()
        original_chain = verify_chain(session)
        counts = {model: session.scalar(select(func.count()).select_from(model)) for model in (User, DurableExecution, VerifiedKnowledge, AuditEvent)}
    with httpx.Client(base_url='http://127.0.0.1:16333', trust_env=False, timeout=30) as client:
        client.delete('/collections/recovery_test')
        client.put('/collections/recovery_test', json={'vectors': {'size': 2, 'distance': 'Cosine'}}).raise_for_status()
        client.put('/collections/recovery_test/points?wait=true', json={'points': [{'id': 1, 'vector': [1, 0], 'payload': {'synthetic': True}}]}).raise_for_status()
    bundle = folder / 'backup'
    with patch.object(settings, 'database_url', source_url), patch.object(settings, 'data_root', data), patch.object(settings, 'model_root', models), patch.object(settings, 'qdrant_url', 'http://127.0.0.1:16333'):
        backup.create(bundle, quiesced=True, compose=True)
    manifest = backup.verify(bundle)
    with (bundle / 'postgres.dump').open('rb') as archive:
        run(compose + ['exec', '-T', 'postgres', 'pg_restore', '-U', 'postgres', '-d', names[1],
                       '--exit-on-error', '--single-transaction', '--no-owner', '--no-acl'], stdin=archive)
    restored = create_engine(target_url)
    engines.append(restored)
    with Session(restored) as session:
        for model, count in counts.items():
            assert count > 0 and session.scalar(select(func.count()).select_from(model)) == count, model
        assert verify_chain(session) == original_chain
        assert session.scalar(select(DurableExecution.status)) == 'INTERRUPTED'
    with patch.object(settings, 'database_url', target_url):
        command.check(Config(str(ROOT / 'backend/alembic.ini')))
    shutil.copytree(bundle / 'data', folder / 'restored-data')
    assert backup.checksum(folder / 'restored-data/manifest.json') == backup.checksum(data / 'manifest.json')
    with httpx.Client(base_url='http://127.0.0.1:16333', trust_env=False, timeout=60) as client:
        snapshot = bundle / manifest['qdrant'][0]['file']
        with snapshot.open('rb') as stream:
            response = client.post('/collections/restored_test/snapshots/upload?priority=snapshot&wait=true',
                                   files={'snapshot': (snapshot.name, stream, 'application/octet-stream')})
            response.raise_for_status()
        assert client.get('/collections/restored_test').json()['result']['points_count'] == 1
    print('RECOVERY DRILL PASS: PostgreSQL schema, user, candidate knowledge, audit chain, interrupted execution, nested file manifest and Qdrant point restored')
finally:
    for engine in engines:
        engine.dispose()
    with admin.connect() as conn:
        for name in created:
            assert name.startswith(('phase_e_backup_', 'phase_e_restore_')) and len(name.split('_')[-1]) == 32
            conn.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
    admin.dispose()
