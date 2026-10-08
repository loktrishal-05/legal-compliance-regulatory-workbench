# Legal platform runtime setup — current workspace only

Status: isolated defaults plus approved disposable D tests/migrations. Private application/model/deployment acceptance remains pending. Read SESSION_RESUME -> CLAUDE_HANDOFF and the living phase guide; historical setup instructions are superseded.

## 1. Verify custody before setup

Only work in `C:\Users\Lohith k\Desktop\OLD hard work\legal-compliance-regulatory-workbench`, with origin exactly `https://github.com/loktrishal-05/legal-compliance-regulatory-workbench.git`. Do not clone/overlay sibling worktrees, fetch old history, initialize/update submodules, execute nested `claudex-loop`, or use historical `.kilo` worktrees. Their content/metadata is preserved as quarantined reference material.

Run root/origin/status inspection before operational commands. The assistant uses the existing authorized root; teammates may clone assigned branches in their own approved checkouts. Regular coherent verified local commits are authorized. Development/review publication follows recorded approval and protected PR rules; main reconciliation/promotion and private runtime/model/deployment remain separately gated. See AGENTS and CLAUDE_HANDOFF.

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

Full regression remains manual, repository-gated and GitHub-hosted; old self-hosted/live inference jobs stay removed. New legal-backend-checks baseline CI runs automatically on assigned team/development pushes and PRs using disposable resources. Credential-free/non-recursive checkout correction is in PR #4 pending independent approval. Baseline CI is not future-feature acceptance. Frozen-readiness mismatch remains recorded, not rewritten.

Approved synthetic legal-core validation (verify Docker context/targets first):

```powershell
docker compose -f infra/docker-compose.legal-core-test.yml config --quiet
docker compose -f infra/docker-compose.legal-core-test.yml build tests
docker compose -f infra/docker-compose.legal-core-test.yml run --rm tests
docker compose -f infra/docker-compose.legal-core-test.yml run --rm tests python -B -m scripts.validate_legal_migrations
docker compose -f infra/docker-compose.legal-core-test.yml down --volumes
```

This dedicated project uses an internal network, no host ports/persistent volumes, selected read-only backend mounts, no private .env/data/models and unused loopback model/vector targets. 27 scoped checks and fresh/0018-to-0020 migrations/parity/idempotency/source-audit-trigger preservation passed; no full app/legal/restore/private schema acceptance. Test container/network was removed after validation.

## 6. Later approved provisioning and validation

After effective private configuration and resource ownership are accepted, start only this project's PostgreSQL/Qdrant with its explicit project name; never use inherited ambiguous Compose commands. Keep disposable migration testing separate from the development DB. Test fresh and existing schema upgrades before any real-data migration.

Backend/native launcher uses port `18000`; frontend uses `15173`. Use one browser hostname consistently for cookies. The backend Docker image runs Python 3.11/Linux with the existing lock; native Windows inference compatibility is not certified by an offline configuration check.

Never execute old seed/restore/staging scripts as setup. Keep credentials/model weights/operational data out of Git. Full legal ingestion, API/UI journeys, tenant isolation, backups, restores and live model acceptance belong to their documented build gates.

## 7. Backup compatibility

The `--compose` backup path now accepts only this project's native loopback database on `55432`, DB `legal_compliance_workbench`, and isolated Qdrant on `16333`. It pins the Compose project name. Foreign/historical targets are rejected before command execution. It still requires operator-quiesced writers and verified protected storage; no backup/restore was executed in Phase A. Native/site-specific backup remains an independently reviewed operation.

## 8. Optional legal upload malware scanner — adapter delivered, engine unconfigured

The continuation backend supports ClamAV `clamd` via a **local Unix-domain socket** using INSTREAM. Set `WORKBENCH_LEGAL_CLAMD_SOCKET` to the approved absolute socket path as visible inside the backend runtime (at most 107 UTF-8 bytes), and `WORKBENCH_LEGAL_SCAN_TIMEOUT_SECONDS` to a positive value at most 30 seconds. Blank socket is the default. No TCP/public scanner address, shell command, source filename or storage path is sent; only the already-authorized, bounded upload bytes stream to the local engine. Native Windows engine integration is not delivered; use an approved Linux runtime for this adapter.

HTTP-configured policy v2 first queries VERSION and validates the daily signature timestamp before sending bytes. `WORKBENCH_LEGAL_SIGNATURE_MAX_AGE_HOURS` defaults provisionally to 72 (allowed 1–168); operational deployments must approve their freshness threshold. Run clamd in UTC for this timestamp contract. Stale/future/invalid/unavailable signatures quarantine; freshness preflight and streaming share the same total deadline. Direct `ClamdScanner(path)` also checks freshness by default. Explicit `max_signature_age_hours=None` is reserved for raw protocol fixtures; application routes use `configured_scanner(settings)` with mandatory freshness.

Only the exact complete `stream: OK` NUL-terminated reply permits a new upload to become `received`. Detection, malformed/oversized/truncated responses, socket failure and total-deadline timeout keep it `quarantined`. Structural quarantine reasons still apply even after a clean scan. Ingestion metadata and the transactional intake audit record scan policy/outcome; signatures, socket paths and raw scanner errors are omitted. Duplicate upload never releases an existing quarantine or rewrites history. A rescan/release workflow remains to be built.

Before enabling on real application uploads, the operator must provision the deployment's dedicated least-privilege engine/socket mount, approve pinned engine/signature update policy and freshness monitoring, and configure ClamAV stream/scan/archive limits to cover the 25 MiB input / 100 MiB permitted DOCX expansion. Enable/verify limit-exceeded alerts so partial scans cannot report a clean result (`AlertExceedsMax` and applicable encrypted-content alerts). The separate synthetic profile below validates current signatures, clean text/PDF/DOCX, harmless EICAR, encryption/limits and actual engine outage/restart. Those checks do not provision the private application or certify broad malware-detection accuracy. Existing application Compose files do not provision/mount ClamAV; that is still a deployment-specific approved step. Exact engine/signature snapshot per upload and historical quarantine rescan/release remain pending.

Runnable adapter check (synthetic Unix-socket protocol peers, no live scanner):

```powershell
docker compose -f infra/docker-compose.legal-core-test.yml run --rm tests python -B -m unittest discover -s tests -p test_legal_scope_scanner.py -v
```

## 9. Reproduce isolated real-engine validation

Use `infra/docker-compose.legal-scanner-test.yml` **only as an overlay on the synthetic legal-core test project**. It pins official ClamAV 1.5.4 by digest. Scanner runs UID 100/GID 101, with no network, no capabilities, read-only root/signatures, bounded tmpfs/CPU/memory/processes; shared Unix socket directory is UID/GID-owned mode 0770, socket 0660. The updater has a separate public-signature egress network and never mounts application data. No host ports, private `.env`, models or confidential fixture documents are mounted. Public signature cache is a dedicated project-named Docker volume, retained between runs; refresh it before acceptance, since the pinned image's bundled signatures can be stale. Do not delete/recreate other projects' volumes or change the private application's configuration to run this validation.

```powershell
docker compose -f infra/docker-compose.legal-core-test.yml -f infra/docker-compose.legal-scanner-test.yml config --quiet
docker compose -f infra/docker-compose.legal-core-test.yml -f infra/docker-compose.legal-scanner-test.yml stop scanner
docker compose -f infra/docker-compose.legal-core-test.yml -f infra/docker-compose.legal-scanner-test.yml --profile signature-update run --rm signature-update
docker compose -f infra/docker-compose.legal-core-test.yml -f infra/docker-compose.legal-scanner-test.yml run --rm tests
docker compose -f infra/docker-compose.legal-core-test.yml -f infra/docker-compose.legal-scanner-test.yml stop scanner
docker compose -f infra/docker-compose.legal-core-test.yml -f infra/docker-compose.legal-scanner-test.yml run --rm --no-deps -e LEGAL_SCANNER_EXPECT_OUTAGE=1 tests python -B -m unittest discover -s tests -p test_legal_malware_outage.py -v
docker compose -f infra/docker-compose.legal-core-test.yml -f infra/docker-compose.legal-scanner-test.yml run --rm tests
docker compose -f infra/docker-compose.legal-core-test.yml -f infra/docker-compose.legal-scanner-test.yml --profile signature-update down
```

Stop on update failure; never mark detection acceptance green on a stale signature database. `down` removes only the dedicated containers/networks and retains the owned public-signature cache (no `--volumes`). Scans/tests create synthetic and harmless EICAR content only in container memory/temporary storage. Current evidence: 7 engine checks + 1 stopped-engine HTTP check passed, daily 28147 dated 2026-10-08, 142 scoped regressions. Engine tests are opt-in; baseline CI alone does not execute this external-image/signature acceptance profile.
