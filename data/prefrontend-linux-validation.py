import os, shutil, subprocess, tempfile
from pathlib import Path
source=Path('/source')
subprocess.run(['git','config','--global','--add','safe.directory','/source/.git'],check=True)
changed='''.dockerignore
.github/workflows/regression.yml
backend/requirements.txt
backend/requirements-linux.lock
backend/app/services/local_voice.py
backend/scripts/local_speech_runtime.py
backend/scripts/seed_dev_users.py
backend/scripts/seed_phase9.py
backend/tests/test_browser_audio.py
backend/tests/test_seed_guards.py
infra/Dockerfile.backend
infra/docker-compose.backend.yml
infra/offline.env.example
docs/local_voice_and_language_resources.md
docs/offline_deployment_and_release.md'''.splitlines()
with tempfile.TemporaryDirectory(prefix='prefrontend-') as directory:
    repo=Path(directory)/'workbench'
    subprocess.run(['git','-c','safe.directory=/source','-c','safe.directory=/source/.git','clone','--no-hardlinks','--quiet','/source',str(repo)],check=True)
    for name in changed:
        target=repo/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source/name,target)
    env=dict(os.environ,PYTHONPATH=f'{repo}:{repo}/backend:{repo}/backend/tests',WORKBENCH_DATA_ROOT=str(repo/'data'))
    with Path('/output/prefrontend-full-final.log').open('w') as log:
        result=subprocess.run(['python','-m','unittest','discover','-s','backend/tests','-v'],cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT)
    print('Full Linux suite exit:',result.returncode,flush=True)
    raise SystemExit(result.returncode)
