# Legal platform runtime setup — current workspace only

Status: Phase A configuration isolation. Services, migrations, model execution and deployment are **not provisioned or validated by this document**. Read the living migration plan before the relevant phase. This guide supersedes operational commands in historical phase/handoff/deployment documents.

## 1. Verify custody before setup

Only work in `C:\Users\Lohith k\Desktop\OLD hard work\legal-compliance-regulatory-workbench`, with origin exactly `https://github.com/loktrishal-05/legal-compliance-regulatory-workbench.git`. Do not clone/overlay sibling worktrees, fetch old history, initialize/update submodules, execute nested `claudex-loop`, or use historical `.kilo` worktrees. Their content/metadata is preserved as quarantined reference material.

Run root/origin/status inspection before operational commands. Use the existing application checkout; no new clone is needed. Do not commit or push without separate authorization.

## 2. Review private configuration without overwriting it

The existing `.env` is user work. Phase A deliberately did not edit, print or certify it. Process environment variables override this file. **Do not start an app, test against services, or apply migrations until the effective DB/Qdrant/model/data targets are verified to belong to this application.** New defaults do not override old explicit values.

If no private file exists, create one without overwriting anything:

```powershell
if (Test-Path -LiteralPath ".env") { throw 'Review the existing private .env; do not overwrite it.' }
Copy-Item -LiteralPath ".env.example" -Destination ".env" -ErrorAction Stop
```

Use a protected editor to configure new credentials, exact CORS origins, the dedicated model endpoint and absolute data/model directories inside this application. Passwords in the template are development examples, not production credentials. Match `POSTGRES_PASSWORD`, native `DATABASE_URL` and container `BACKEND_DATABASE_URL`. Do not copy secrets from another application.

Review stale process overrides including `DATABASE_URL`, `QDRANT_URL`, `QDRANT_COLLECTION`, `MODEL_BASE_URL`, `WORKBENCH_DATA_ROOT`, `WORKBENCH_MODEL_ROOT`, `WORKBENCH_API_PROXY` and `COMPOSE_PROJECT_NAME`. Review their values privately; do not dump environment or resolved Compose configuration to shared logs. Use a fresh terminal with approved overrides only.

## 3. Isolated resource contract

| Resource | Native host / identity | Container endpoint |
|---|---|---|
| Compose project | `legal-compliance-regulatory-workbench` | Separate project-scoped network/volumes |
| PostgreSQL | `127.0.0.1:55432`, database `legal_compliance_workbench` | `postgres:5432` with the same database |
| Qdrant | HTTP `127.0.0.1:16333`, gRPC `127.0.0.1:16334` | `qdrant:6333` |
| Vector collection | `legal_knowledge_chunks_v1` | Same isolated collection |
| Backend | `127.0.0.1:18000` | App listens on `8000` internally |
| Frontend dev/preview | `127.0.0.1:15173` or `localhost:15173` | Same-origin `/api` proxy -> backend `18000` |
| Ollama candidate | Dedicated private instance on `127.0.0.1:21434` | Explicit `BACKEND_MODEL_BASE_URL` and exact allowed host |
| Backend image | `legal-compliance-workbench-backend:py311-cpu` | Build only from this application's Dockerfile |
| Disposable test projects | `legal-compliance-regulatory-workbench-auth-test` / `...-ui-api-test` | Internal networks, no host DB ports |

Changing configuration creates a separate resource namespace; it does not migrate or rename existing databases/volumes/collections. Do not point the new namespace at old data to make it look initialized. Legal data model migrations and scoped retrieval arrive in later phases.

## 4. Model boundary

Do not reuse an Ollama service/model store serving another app. Provision a separate instance/store through an approved runtime step; keep local/private inference and cloud-disabled policy. No models were downloaded or executed in Phase A.

For container access, set `BACKEND_MODEL_BASE_URL` and `BACKEND_MODEL_ALLOWED_HOSTS` explicitly. An approved Docker Desktop setup may use `http://host.docker.internal:21434` with host `host.docker.internal`, but reachability and instance ownership must be verified first. Do not expose a public listener or weaken the firewall to make it work. The overlay refuses missing values rather than silently using another app's port 11434.

## 5. Safe offline configuration checks

These commands validate source configuration only, without starting Docker services or loading `.env`:

```powershell
$env:PYTHONPATH = 'backend'
python -B -m unittest discover -s backend/tests -p test_legal_repository_custody.py -v
docker compose --env-file .env.example -f infra/docker-compose.yml config --quiet
node --check frontend/vite.config.js
```

The backend overlay additionally requires explicit container model values. Use approved synthetic values for render-only tests; do not interpret configuration rendering as connectivity, schema or security acceptance.

CI is manual-only, exact-repository gated and GitHub-hosted. The historical self-hosted/live inference job was removed. No workflow was dispatched. The pre-existing frozen-readiness-report mismatch remains a regression/release issue; its manifest and user edits were not rewritten.

## 6. Later approved provisioning and validation

After effective private configuration and resource ownership are accepted, start only this project's PostgreSQL/Qdrant with its explicit project name; never use inherited ambiguous Compose commands. Keep disposable migration testing separate from the development DB. Test fresh and existing schema upgrades before any real-data migration.

Backend/native launcher uses port `18000`; frontend uses `15173`. Use one browser hostname consistently for cookies. The backend Docker image runs Python 3.11/Linux with the existing lock; native Windows inference compatibility is not certified by an offline configuration check.

Never execute old seed/restore/staging scripts as setup. Keep credentials/model weights/operational data out of Git. Full legal ingestion, API/UI journeys, tenant isolation, backups, restores and live model acceptance belong to their documented build gates.

## 7. Backup compatibility

The `--compose` backup path now accepts only this project's native loopback database on `55432`, DB `legal_compliance_workbench`, and isolated Qdrant on `16333`. It pins the Compose project name. Foreign/historical targets are rejected before command execution. It still requires operator-quiesced writers and verified protected storage; no backup/restore was executed in Phase A. Native/site-specific backup remains an independently reviewed operation.
