# Legal, Compliance & Regulatory Workbench — project handoff

> Current custody update (2026-10-06): this handoff is retained as historical provenance.
> Discovery found inherited Git/runtime state that differs from its isolation claims.
> Use `docs/REPOSITORY_BOUNDARY_AUDIT.md` for current custody, `docs/LEGAL_DOMAIN_MIGRATION_PLAN.md`
> for build status, and `docs/LEGAL_RUNTIME_SETUP.md` for operational instructions.

## Start here

This is an isolated technical foundation for a new hackathon problem statement:

- Contract analysis.
- Compliance monitoring.
- Document summarization.

**Domain migration has not started.** The application still displays Sovereign branding and implements industrial workflows. This snapshot is not a completed legal/compliance product.

New local root: `C:\Users\Lohith k\Desktop\legal-compliance-regulatory-workbench`.

Intended private repository: `https://github.com/loktrishal-05/legal-compliance-regulatory-workbench`.

Only that repository may be used for this project's commits and pushes. Do not touch the original Sovereign folders, their shared Git metadata, the existing remote application, or eRTMAC-NWIS. Do not deploy or link an existing hosting project.

## Source provenance and isolation

The source is `C:\Users\Lohith k\Desktop\OLD hard work\sovereign-agentic-workbench`, branch `master`, HEAD `831c14909afc4ed1d2b778359df07f9e6b21b5cc`.

The requested source directly under Desktop no longer exists. Eleven sibling Sovereign folders are linked worktrees, not independent repositories. Their pointers still reference the former Desktop location. They were inspected through the relocated common Git metadata without repairing or modifying it.

The canonical working directory was copied, including staged terms-acceptance changes and uncommitted frontend improvements. It was in an unfinished cherry-pick; this new repository does not inherit that operation or its history. The cached remote-tracking master is 43 commits ahead and contains newer NWIS code. It was not pulled, copied or merged.

The main folder already includes the feature worktrees' integrated capabilities. Older `frontend/src/App.jsx` and `frontend/src/styles.css` in sibling worktrees belong to superseded frontend structure; they were not overlaid. Vercel demo instructions and configurations were not imported.

Before detaching Git, all 948 selected files passed byte-for-byte SHA-256 comparison. Private environment files, private admin fixtures, operational database backups, caches, installed dependencies and downloaded model weights were excluded. Required source, tests, migrations, prompts, benchmark definitions, documentation and frontend assets were retained. Git metadata was removed only from the verified new copy.

See `SOURCE_AUDIT.md` for worktree details, limitations and the integrity inventory.

## Architecture and reusable capabilities

```text
React/Vite frontend
  -> FastAPI HTTP API
  -> LangGraph orchestration and specialist agents
  -> evidence/guardrail validation
  -> immutable advisory revision
  -> authenticated human review and release

PostgreSQL / SQLAlchemy / Alembic: accounts, documents, execution state, approvals, audit
Qdrant: local dense/sparse retrieval
Ollama: local model generation and optional local vision
Local extraction / OCR / embeddings / reranking
Optional local speech adapters and reviewed public-resource integrations
```

| Capability | Existing implementation | Legal-domain reuse |
|---|---|---|
| Web application | React 19, React Router, Vite; auth, dashboard, workspace, knowledge, reviews, executions, audit, profile/admin | Keep the shell and authenticated workflows; transform pages later |
| API | FastAPI, Pydantic request/response models and server-owned authorization | New legal endpoints can reuse the API structure |
| Relational storage | SQLAlchemy, PostgreSQL, 18 Alembic migrations through terms acceptance | Reuse persistence patterns; design legal schemas in a later phase |
| Document ingestion | Extraction, document versions, chunking, ingestion manifests | Contract and regulatory-document processing |
| OCR and multimodal | PaddleOCR, image/PDF processing, OCR evidence locators, optional local vision and P&ID evidence fusion | Scanned contracts and document figures; industrial assumptions need review |
| RAG | Qdrant dense/sparse retrieval, reciprocal-rank fusion, BGE reranking, cited evidence | Contract clauses and approved regulatory sources |
| Graph execution | LangGraph, durable execution/checkpoint state, adaptive routing, bounded steps/timeouts, observability | Reviewable long-running legal-analysis workflows |
| Agents | Knowledge, safety, maintenance, optimization, routing/terminal/guardrail components | Keep orchestration and evidence enforcement; replace specialist purpose/prompts later |
| Enterprise knowledge | Verified knowledge, knowledge packs, gaps and approval workflows | Controlled policy/regulatory knowledge collections |
| Auth/RBAC | Argon2 password hashing, opaque cookie sessions, requester/reviewer/admin roles, signup approval, account administration | Reuse permissions and reviewer separation |
| Recovery/OIDC | Admin recovery plus optional SMTP/Google integration | Configure fresh credentials only when explicitly needed |
| Audit/governance | Audit chain, immutable revisions, evidence integrity, approval/revoke/release controls | Traceable contract/compliance findings with human review |
| Local voice | Speech adapters, transcription review and technical-identifier correction | Optional hands-free intake; legal terminology needs later evaluation |
| Infrastructure | Compose, backend image, offline preflight, backup/restore utilities and n8n templates | Reuse in a separately provisioned environment |
| Validation | Backend tests, frontend Node tests, retrieval checks and frozen benchmark harness/corpus | Preserve industrial regression evidence; add legal evaluation separately |

These are source-level capabilities. They were not newly certified through a live deployment during isolation.

## Repository structure

- `backend/app/api/`: FastAPI router, dependencies and route modules.
- `backend/app/agents/`: graph, registry, state, specialist nodes, prompts and tools.
- `backend/app/services/`: ingestion, retrieval, OCR, model gateway, durable execution, accounts, governance and audit.
- `backend/app/db/` and `backend/app/schemas/`: relational models and API schemas.
- `backend/alembic/versions/`: migration history, including `0018_terms_acceptance.py`.
- `backend/tests/` and `backend/scripts/`: tests, provisioning, runtime/health/evaluation utilities.
- `frontend/src/app/`: routing, shell, session and navigation.
- `frontend/src/features/`: auth, agents, approvals, dashboard, insights, knowledge, executions, maintenance, P&ID, voice and resources.
- `frontend/public/`: branding, local fonts, auth media and help/terms resources.
- `infra/`: Compose configurations, Dockerfile, frozen benchmark hashes and n8n definitions.
- `benchmark/`: industrial evaluation definitions, corpus, harness and historical reports.
- `data/`: tracked schemas/manifests/evaluation definitions; copied input examples and recovery-development scripts. Private operational state is not included.
- `models/`: directory marker only; provision approved model artifacts separately.
- `docs/`: historical phase contracts/validation; some descriptions and commands are outdated.
- `_incoming_phase10_bundle/`: preserved historical extraction inputs; not another application to execute or overlay.
- `claudex-loop/`: preserved auxiliary development tooling, including a nested historical copy. It is not required by the application; embedded Git histories were not carried into the new repository.

## Local setup — use isolated resources only

No servers, containers, migrations or model inference were started during isolation. Do not execute old setup commands against existing services. Older docs mention original ports and shared resource names; this handoff takes precedence for the new project.

The main Compose file now declares project name `legal-compliance-regulatory-workbench`. Its new volumes/network are project-scoped. Host ports are PostgreSQL `55432`, Qdrant HTTP `16333`, Qdrant gRPC `16334`, backend `18000`, frontend `15173`. The optional backend image is `legal-compliance-workbench-backend:py311-cpu`.

From the new repository root, create private configuration:

```powershell
Copy-Item .env.example .env
```

Review `.env` before running anything. Supply a newly generated auth secret, new database credentials, exact installed model names, and absolute `WORKBENCH_DATA_ROOT` / `WORKBENCH_MODEL_ROOT` paths inside the new project. Set `POSTGRES_PASSWORD` consistently with the password in `DATABASE_URL`. Do not copy the old `.env` or admin credential files. Machine environment variables override `.env`; remove stale `DATABASE_URL`, `QDRANT_URL`, proxy and data-root overrides from the new terminal before startup.

The application source still has historical fallback settings. **Always configure the new root `.env` before running backend code.** Do not point it to the old database, Qdrant instance, data directory or model gateway that serves the active application.

Provision separate local model inference if the old Ollama service is actively used. The template's loopback inference URL is an example, not proof of a dedicated instance. Set `MODEL_BASE_URL` to the new instance and maintain the local/private allowlist.

After a separate controlled runtime-setup phase, the development commands are:

```powershell
docker compose --env-file .env -f infra/docker-compose.yml up -d
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
$env:PYTHONPATH = "$PWD;$PWD/backend"
backend/.venv/Scripts/python.exe -m alembic -c backend/alembic.ini upgrade head
backend/.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 18000
```

In another terminal rooted in the new repository:

```powershell
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run dev -- --host 127.0.0.1
```

Visit `http://127.0.0.1:15173`. Vite's `/api` proxy defaults to the new backend port `18000`. Use one browser hostname consistently for cookies. The template CORS origins use port `15173`.

The documented supported release environment is Linux x86_64 / Python 3.11 using `backend/requirements-linux.lock`, including CPU Torch wheels. Native Windows development uses `backend/requirements.txt` and may need platform-specific OCR/model dependencies. Do not assume an old `.venv` can be moved or reused.

If using the backend Compose overlay, set private `BACKEND_DATABASE_URL` to the **new Compose project's** `postgres` service hostname and matching credentials. The internal PostgreSQL/Qdrant ports remain `5432`/`6333`. Provision models and frontend build artifacts first; the image intentionally runs offline checks.

## Models, RAG and agents

- Primary generation/routing profile: `qwen3.5:9b`; fast profile: `qwen3.5:4b`. Verify actual installed tags and hardware requirements; preserve configured digests for reproducible evaluation.
- Ollama is the implemented runtime. The vLLM adapter is a registered placeholder, not an accepted complete runtime.
- Embeddings: `BAAI/bge-base-en-v1.5`, 768 dimensions.
- Reranker: `BAAI/bge-reranker-base`.
- Extraction: Docling/PyMuPDF; OCR: PaddleOCR/PaddlePaddle; image processing: Pillow/OpenCV.
- Retrieval uses chunking, dense and sparse candidates, RRF fusion, optional reranking and source citations. Relevant model artifacts and Qdrant indexes must be provisioned/rebuilt in the new environment.
- Model downloads and private runtime caches are not committed. Existing download/provisioning scripts are available for review before use.
- Prompts and specialist logic are still industrial. No legal prompts or claims of legal accuracy were introduced.

## Auth, audit and migration status

Requester/reviewer/admin authorization remains server-controlled. Human approval authorizes advisory release, not physical control. Optional SMTP/Google resources are unconfigured; fresh credentials and callback URLs must be provisioned separately. Terms acceptance is preserved from the original staged changes, including its migration and frontend gate.

The copied code includes 18 migration files. No existing database was copied, connected, migrated, stamped or reset. New database migration status is therefore **not applied / not live-verified**.

The existing benchmark manifest references 168 files; all are present. One pre-existing mismatch remains: `benchmark/reports/final_model_runtime_readiness.json`. The historical integration report already documents it as a runtime-readiness edit. It was copied unchanged, not silently replaced. A frozen-integrity check will fail until a separately authorized decision resolves that report; do not rewrite benchmark expectations merely to make checks pass. BLIND inference was not executed.

Inherited automatic CI triggers were disabled. The old self-hosted runner/environment linkage was removed from the active regression workflow; live inference is disabled. No Vercel or Cloudflare linkage exists in the new copy. No deployment has been performed.

Isolation verification also ran the frontend suite in the new copy: **39 tests passed**, and Vite configuration syntax passed. Dependencies were installed from the lockfile with install scripts disabled. The transformation harness emitted an existing WebSocket port collision warning; no old process was changed. Backend/live/database acceptance remains a separate future step.

## Later legal/compliance transformation

Still industrial: branding, landing/help/terms wording, equipment and sensor schemas, maintenance/P&ID/operations pages, specialist prompts, industrial corpora and evaluation expectations. Preserve these until a controlled migration plan decides which are adapted, retained as historical tests or retired.

The next phase should define contract document/version/clause models, jurisdiction/source provenance, policy/control mappings, reviewable findings, obligation/deadline monitoring and evidence-grounded summaries. Define appropriate human review and legal-domain evaluation before changing prompts or making compliance claims. Existing industrial benchmark results do not establish legal correctness.

## Constraints for the next conversation

1. Work only inside the new repository and use only its new remote.
2. Do not repair, clean, reset, stash, commit, push or deploy any original folder.
3. Do not reuse old hosting IDs, CI runners, database volumes, credentials or Cloudflare tunnels.
4. Preserve source/evidence provenance and explicitly review schema migrations.
5. Keep secrets, model weights, operational data and real account credentials out of commits.
6. Do not run tests against the old or production database. Use a newly provisioned disposable test database.
7. Do not convert the domain or deploy until the user explicitly authorizes the next phase.
