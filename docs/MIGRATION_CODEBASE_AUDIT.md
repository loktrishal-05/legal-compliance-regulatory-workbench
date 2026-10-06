# Migration codebase audit

Date: 2026-10-06. Status: architecture discovery, not runtime certification. The master PDF (all 80 pages, including appendices A-J) is the product authority. See `REPOSITORY_BOUNDARY_AUDIT.md` for custody and user-work details.

## Architecture and inventory

```text
React 19 / Vite / React Router browser
  -> same-origin /api proxy (prefix stripped)
  -> FastAPI routes + cookie identity + server-owned roles
  -> deterministic preflight / adaptive routing
  -> local gateway / LangGraph specialists / evidence validation
  -> immutable ActionRevision + evidence manifest
  -> authenticated decision ledger + advisory release gate

PostgreSQL: authoritative identity, source metadata, graph recovery, decisions, audit
Local files: source PDFs/images, extraction artifacts, manifests, model artifacts
Qdrant: dense/sparse index, rebuildable but currently industrial payload schema
Ollama: implemented local generation; vLLM adapter is a placeholder
```

| Area inspected | Contents / role |
|---|---|
| `backend/app/main.py`, `api/router.py`, `api/deps.py`, `api/routes/` | FastAPI registration, origin middleware, roles/terms guard, route families below |
| `backend/app/agents/`, `nodes/`, `prompts/`, `tools/` | Graph, SQL checkpointer, state/context, registry, evidence/citation enforcement, specialist prompts/tools |
| `backend/app/services/`, `services/model_gateway/` | Accounts, ingestion/extraction, retrieval, OCR/P&ID, governed knowledge, execution, governance/audit, integrations, industrial intelligence |
| `backend/app/db/`, `db/models/`, `schemas/` | UUID identity mixins, named constraints, ORM tables, Pydantic domain/API contracts |
| `backend/alembic/`, `versions/` | Eighteen files; linear source revision chain through staged terms acceptance |
| `backend/tests/`, `backend/scripts/` | 48 test modules; provisioning, retrieval/runtime evaluation, backup, seeds, smoke and migration tools |
| `frontend/package.json`, `src/`, `src/app/`, `src/features/`, `public/` | Shell/auth/terms/navigation, feature modules, tests, industrial branding/media/local fonts/resources |
| `infra/` | PostgreSQL/Qdrant Compose, backend/offline/test overlays, Dockerfile, launcher, frozen hashes, six n8n templates |
| `benchmark/` | Cases, industrial corpus, harness, mappings, reports/results; stage2/stage4/resume utilities and tests |
| `data/` | Manifests/evaluation, raw/processed/indexes, resources, ignored operational logs/backups/account fixture and recovery/staging sources |
| `models/` | Local BGE embedding/reranker, Docling, PaddleOCR, speech artifacts; ignored, not just directory markers |
| `docs/` | Historical phased design/validation/runbooks, current staged terms documentation; historical claims must not be re-labelled as current passes |
| `.github/`, `.codex/`, `.impeccable/`, `.claude/`, `.kilo/` | CI and agent/design configs; historical operational coupling and nested worktree pointers |
| `_incoming_phase10_bundle/` | Historical loose files and prepared corpus bundle; archive-only, not authoritative overlay |
| `claudex-loop/` | Third-party auxiliary tooling/gitlink with two nested Git repositories; not needed by application runtime, operational use stopped |

This audit inventories the whole architecture and reads its critical flows. It is not a line-by-line review of every test, asset, archived log or third-party tool. Every later checkpoint must read all files and callers it changes before implementation.

## Dependencies

Backend intent: FastAPI/Uvicorn, Pydantic Settings, SQLAlchemy 2, Psycopg 3, Alembic, Qdrant client 1.17, SentenceTransformers 5, Docling, PyMuPDF, PaddleOCR/PaddlePaddle, OpenCV/Pillow, HTTPX, pinned LangGraph 1.2.11 and LangChain Core 1.6.3, Argon2, Authlib and email-validator. Linux Python 3.11 CPU deployment uses `backend/requirements-linux.lock`; Windows intent file is not equivalent to a verified release lock. No new packages installed in discovery.

Frontend: React/ReactDOM 19.2, React Router 8.4, Vite 7.2, GSAP 3.15 plus React adapter; ESLint 9. JavaScript/JSX, not Next.js/TypeScript. Scripts exist for `test`, `lint`, `build`, `dev`, `preview`. Retain this stack initially; the PDF's Next.js/TypeScript recommendation does not require a shell rewrite.

## Current API families

Routes are root-relative, not `/v1`; frontend `/api` is a proxy convention.

| Family | Registered operations |
|---|---|
| Health / models / agents | `/health`, `/ready`, `/models/status`, `/agents/status` |
| Query | `POST /query` |
| Authentication | `/auth/capabilities`, signup/login/logout/me, sessions and revocation, terms/current/accept, password forgot/verify-otp/reset, email verification, Google start/callback |
| Administration | `/admin/users`, create user, role, recovery, lifecycle operations |
| Governance | `/approvals`, revision detail, decision, release; legacy placeholder endpoint coexists |
| Audit | `/audit/log`, `/audit/verify` |
| Document/RAG | `/documents/ingest`, `/knowledge/retrieve`; P&ID process/index/list/detail/page image |
| Structured industrial | `/equipment`, sensor channels/readings/latest/features/intelligence, sensor/maintenance ingestion, maintenance/history and work-order detail |
| Controlled knowledge | `/verified-knowledge` create/list/detail/history/revalidate/operations; `/knowledge-packs` create/list/detail/operations; `/execution/inspect`; knowledge-gap lifecycle |
| Operations | `/operator-notes`, `/shift-handover`, `/environmental-compliance` |
| Product/integrations | `/product/status`, local voice transcribe/synthesize, `/bi/operational`, `/automation/webhook`, `/sovereignty/proof` |
| Durable runs | `/executions` start/list/detail/resume |

No registered legal contract, regulatory source, requirement, control, legal obligation or remediation bounded-context API was identified. Industrial environmental compliance is not the target legal compliance model.

## Database and migrations

Registered tables by group:

- Identity: `users`, `auth_sessions`, `auth_identities`, `auth_challenges`, `auth_reset_capabilities`, `auth_attempts`, `auth_oidc_flows`.
- Documents: `documents`, `document_versions` (globally unique source hash today, JSONB ingestion metadata/status).
- Execution: `agents`, `agent_actions`, `agent_runs`, `agent_run_steps`, `durable_executions`, `graph_checkpoints`, `graph_writes`, `execution_operations`.
- Governance/evidence: `governance_requests`, `action_revisions`, `approval_decisions`, `evidence_manifests`, `evidence_manifest_items`.
- Audit: `audit_events`, `audit_chain_heads`, `audit_checkpoints`; legacy `audit_logs`, `approvals` remain distinct.
- Controlled knowledge: `verified_knowledge`, `knowledge_gaps`, `knowledge_packs`.
- Industrial/integration: `equipment`, `sensor_readings`, `incident_reports`, `structured_data_sources`, `maintenance_records`, `operator_notes`, `automation_receipts`.

No Organization/Workspace/membership or tenant ownership columns appeared in the model inventory. A global requester/reviewer/admin role and `internal` access-scope string are **not multi-tenant isolation**.

Revision chain:

```text
0001_phase2 -> 0002_document_versions -> 0003_structured_data -> 0004_agent_runs
-> 0005_governance_revisions -> 0006_phase5b_approvals -> 0007_phase5c_audit_chain
-> 0008_phase5d_evidence_integrity -> 0009_phase5e_preflight -> 0010_phase5f_repairs
-> 0011_verified_knowledge -> 0012_knowledge_packs -> 0013_operational_intelligence
-> 0014_product_integration -> 0015_durable_execution -> 0016_enterprise_knowledge
-> 0017_accounts_recovery -> 0018_terms_acceptance
```

The first file is named `0001_phase2_foundation.py` but its revision is `0001_phase2`. Revision 0018 is existing staged user work, not a newly delivered migration. DB applied revision is unknown: no DB connection occurred. Immutable revision/decision/audit/manifest tables use ORM protections, PostgreSQL CHECKs and UPDATE/DELETE triggers; 0010 adds TRUNCATE protection. Audit event vocabulary is constrained: adding legal event types requires an additive migration, not only a Python enum edit.

`scripts.validate_migrations` creates/drops disposable schemas in whatever database `settings.database_url` resolves to; it is not safe isolation by itself. Its existing-schema baseline is 0015. Legal validation must use a separately provisioned disposable database and test both fresh-to-head and current-0018-to-new-head, including immutable data/trigger preservation.

## Document processing and retrieval flow

`/documents/ingest` is admin-authorized and accepts a path inside `data/raw`, not a browser multipart upload. `resolve_source` enforces confinement, `.pdf`, 1 byte-20 MiB; `ingest` checks PDF magic, reads a single byte snapshot for hash/extraction, uses PostgreSQL advisory locks and checksum duplicate handling, persists version state, then extracts/chunks/embeds/upserts. On index failure the DB marks the version failed so partial index writes are not visible as ready.

`extraction.py` inspects 1-100 pages with PyMuPDF, rejects encrypted PDFs, flags scanned/mixed pages `ocr_required`, uses local Docling with remote services/OCR disabled, and reports native-text fallback explicitly. Separate PaddleOCR/P&ID machinery has region/image/box/confidence locators and optional local vision. Generic legal OCR correction and DOCX intake remain gaps. The snapshot used during ingest does not establish a complete immutable original object-store lifecycle: source files and local URI manifests need a version-preserving storage review.

Chunk metadata contains source SHA, document/version IDs, page bounds, section path, bounding boxes, extraction quality, revision/effective date and scope plus industrial facility/unit/equipment/instrument fields. BGE-base-en-v1.5 is fixed at 768 dimensions; Qdrant named dense and sparse/IDF vectors, RRF, deduplication and BGE reranker are implemented. Citation data is copied from stored chunks; point-ID mismatch fails. DB indexed-state filtering exists, but ready-version lookup is global and filters lack tenant/matter/jurisdiction/authority/effective-period policy. Route forces `internal` scope; this does not establish per-document ACLs.

Qdrant migration helpers include backfill/verified copies and optional promotion that deletes the original collection before alias creation. **Do not execute this for cosmetic renaming.** Prefer a new isolated legal collection, verified reindex and controlled reversible configuration cutover.

## Orchestration and local AI

LangGraph graph: router -> knowledge / maintenance / safety / combined-safety-maintenance / process-optimization / clarification / refusal, plus shift-handover and environmental-compliance routes. Durable mode adds governance -> approval interrupt -> terminal. Knowledge-only/MGS paths reuse nodes. Runs enforce bounded recursion/deadlines and record node/tool/timing provenance.

`durable_execution.py` and SQL checkpointer retain checkpoints, operation receipts, infrastructure retry classification, requester ownership/admin inspection, advisory locks and fresh ledger checks at approval resume. Start/resume invokes synchronously; there is no demonstrated durable calendar/timer scheduler or general ingestion worker queue. Keep recovery primitives but add/prove asynchronous job and timer behavior before calling legal monitoring continuous.

Gateway supports text, structured Pydantic output with bounded repairs, allowlisted tool-call names, health/listing, local/private URL policy and model profiles. Ollama works in source; vLLM remains unimplemented. Primary/fast profiles are constrained to Qwen 9B/4B. Current preflight/prompt/output/evidence heuristics are industrial and may refuse legitimate legal work. Replace them coherently with legal schemas/evidence policy; never simply remove guardrails.

## Authentication, authorization and confidentiality

Argon2 password hashing; opaque hashed server-side sessions; HttpOnly cookies; session expiry/revocation; signup approval; terms gate; reset/email challenge flows; optional Google OIDC and SMTP; no client-controlled role/identity. Main middleware rejects disallowed mutation origins and sets no-store/referrer protection for enumerated sensitive paths. Secure cookies are false for local HTTP by default and require TLS deployment configuration.

Roles are server-owned; reviewer authorization is re-read at the approval service boundary; self-approval is forbidden. Tenant/matter ACLs, auditor/business-owner separation, enterprise SAML/MFA/privileged re-auth and source confidentiality policies are not delivered by these mechanisms. New `/v1` paths must inherit origin/cache protections through shared policy, not escape prefix-based protections. Prompt-body logging defaults off, but query trace storage defaults on; assess secondary confidential copies in checkpoints/analysis/recovery/export/telemetry.

No generic upload malware scanner/quarantine/parser sandbox was identified in the inspected ingestion path. No S3/MinIO, Temporal service, or external regulatory feed is provisioned by current Compose. Treat those as missing capabilities or deployment choices, not live integrations.

## Governance, audit and evidence

Canonical request/proposal hashes bind immutable pending `ActionRevision` objects; ledger decisions compute approved/rejected/revoked/expired state. Model authority fields are removed from public output; LLM metadata can increase caution, not grant permissions. Release rechecks exact revision/hash/policy, evidence integrity and final locked approval state. Decisions and mandatory audit share transaction ownership.

Audit appends hash-linked events under a chain-head row lock; independent verification detects linkage/hash/sequence problems and complete truncation against retained head metadata. Checkpoints are local, not off-host anchoring; not tamper-proof. Existing chain/hash formats must remain verifiable.

Evidence manifests freeze deterministic content/provenance and reverify source files/chunks/CSV/P&ID/operational records. This covers useful primitives but hardcoded evidence types and industrial sufficiency categories need legal extensions. A valid empty manifest is possible in generic governance: legal material-output release must additionally require actual sufficient citations, not confuse structural manifest validity with supporting evidence. Current latest-source validity heuristics must support historical/effective-date legal replay without rewriting old manifests.

## Frontend

Public landing and auth are Sovereign cinematic dark; authenticated shell has calmer tokens, responsive sidebar, command palette, language/theme preferences, reusable UI state components and lazy route chunks. Identity is reloaded from `/auth/me`; no client-stored principal. Terms gate wraps `/app`; audit/admin UI guards complement backend checks.

Existing `/app` pages: dashboard, workspace, workspace/voice, agents, pid, maintenance, operations/{handover,compliance,notes}, knowledge, gaps, approvals, executions, audit, sovereignty, resources, help, admin, profile. Dashboard/knowledge/review/execution views consume backend APIs and preserve empty/error/loading states. Keep shell/reviewer/source-inspector patterns. Replace operational screens progressively; no fabricated legal metrics or relabelled industrial compliance score. Public icons/logos/manifest/help/terms/videos/fonts are separate identity assets; approved old logos cannot magically become legal logos.

## Deployment and operations

Actual defaults: PostgreSQL 17 on `5432`, DB `sovereign_workbench`; Qdrant 1.17.0 on `6333/6334`, collection `knowledge_chunks_v1`; backend `8000`; Vite `5173`; Ollama `11434`. Compose has no explicit project name, volumes `postgres_data`/`qdrant_data`, backend image `sovereign-workbench-backend:py311-cpu`. These can collide with historical application resources. Handoff's isolated `55432/16333/18000/15173` configuration is absent from actual files. Do not start services.

Docker image is digest-pinned Python 3.11 Linux CPU, non-root app user, offline/telemetry flags; backend image starts Uvicorn without the claimed health preflight in its CMD. Relative data/model/frontend mounts exist; offline overlay disables pulls and Qdrant telemetry. Test overlays use internal networks but old image tags. Six n8n templates cover error handling, ingestion, approval notification, sovereignty report, audit archive, operational summary. Adapt only approved summary/event contracts, not confidential export.

Backup utility requires explicit writer quiescence and checksums DB dump/local data/Qdrant snapshots; restore is a documented manual runbook, not a newly validated exercise. It enumerates all Qdrant collections and its Compose guard assumes 5432: isolate target resources and adapt before use. CI currently auto-triggers and has optional historical self-hosted live job; no dispatch/push performed.

## Tests and reusable/obsolete coverage

- Reusable: foundation invariants (identity wording coupled), gateway, native extraction/chunking/hybrid retrieval, governance 5A/5B, audit 5C, integrity 5D, security 5E/5F/phase11, accounts/terms/seed guards, execution/checkpoint, release and knowledge provenance.
- Mixed: agent-output/advanced/phase6-9/enterprise/voice/UI API tests; keep platform assertions and add legal counterparts.
- Historical industrial: maintenance/sensor/structured/P&ID/safety/optimization tests and frozen industrial benchmark expectations. Retain separately until dependency migration is complete; do not change frozen answers to claim legal success.
- New legal coverage needed: scoped ingestion/ACLs, clause provenance, approved obligation deadlines, regulatory authority/version/effectivity/diffs, requirement-control-evidence assessment/freshness, review/release, remediation/retest, citations/refusal, prompt injection, cross-tenant retrieval, retry/timer restart, exports/recovery and primary UI journeys.

Only newly executed non-runtime verification: repository commands, PDF SHA equality, ignore checks and frozen-integrity script. Frozen integrity **fails** at pre-existing modified `benchmark/reports/final_model_runtime_readiness.json`. No backend/frontend/migration/live-model suite was run in discovery; historic 39/890/etc. numbers are not current results.

## Migration risks

Highest priorities: unresolved cherry-pick/user work; contradictory handoff; nested/shared Git metadata; CI/service collision; no tenant/matter ACL; global source dedupe; mutable local originals; legal-only auth/review roles; industrial safety/evidence heuristics; absent durable timers/worker intake; constrained audit event types; index payload compatibility; historical-source replay; private runtime files/models present; frozen hash mismatch; legal OCR/quality/accuracy unproven. Each has an explicit gate in `LEGAL_DOMAIN_MIGRATION_PLAN.md`.

## Phase A update (baseline above remains historical)

Approved quit/switch resolved the active operation without discarding work; legal migration branch is active. CI and native/Compose/proxy defaults are now isolated, with project DB/collection names and ports 55432/16333/16334/18000/15173; private model endpoint defaults to dedicated candidate port 21434 and container configuration is required. A foreign-target Compose backup guard and six offline custody regressions were added. Active runbooks now link `LEGAL_RUNTIME_SETUP.md`; nested tooling stays quarantined. Frontend 39 tests/lint/build pass; no live backend/model/DB/migration acceptance or legal capabilities delivered. Private runtime overrides and all remaining domain/security risks still require their phase checks.
