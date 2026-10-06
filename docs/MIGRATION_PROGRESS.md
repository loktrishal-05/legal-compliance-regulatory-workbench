# Migration progress

Date: 2026-10-06. **Phase A source custody/configuration complete; Phase B next.**

## Current state

| Checkpoint | Status |
|---|---|
| A custody/report/discovery | Complete: preserved branch activation, isolated defaults/CI/runbooks, offline regression/frontend checks |
| B architecture/reuse | Proposal documents prepared, not approved |
| C-M implementation/validation | Not started |

Phase A changed configuration/backup guards and current operational documentation. Legal feature code, schema and migrations have not been built. No sibling/external repository changed. No staging, commit, push, service deployment, DB connection/migration or model execution occurred.

## Changes made in this discovery

| Path / reference | Change | Why |
|---|---|---|
| `docs/Legal_Regulatory_Assurance_Platform_Master_Report.pdf` | Byte-for-byte copy from Downloads; all 80 pages read | Primary specification preserved |
| `AGENTS.md` | Added current-root/historical/nested/push/user-work constraints to existing untracked user instruction file | Strengthen custody without overwriting existing rules |
| `docs/REPOSITORY_BOUNDARY_AUDIT.md` | New | SHA/branch/remotes/status/worktrees/siblings/reference classification and blockers |
| `docs/MIGRATION_CODEBASE_AUDIT.md` | New | Architecture/components/routes/schema/execution/RAG/security/deployment/test inventory |
| `docs/LEGAL_PLATFORM_REUSE_MATRIX.md` | New | KEEP/ADAPT/RETIRE/REBUILD/NEW with dependency gates |
| `docs/LEGAL_PLATFORM_TARGET_ARCHITECTURE.md` | New proposal | PDF-grounded relational bounded contexts, authority/temporal/security/UI design |
| `docs/LEGAL_DOMAIN_MIGRATION_PLAN.md` | New proposal | A-M checkpoints, FR ownership, compatibility/test gates/decisions |
| `docs/MIGRATION_PROGRESS.md` | New | Living record of actual changes and remaining work |
| `docs/VALIDATION_REPORT.md` | New, discovery-only | Actual checks/failures/deferred acceptance; no false green status |
| `refs/heads/feat/legal-regulatory-platform-migration` | Branch created at `831c14909afc4ed1d2b778359df07f9e6b21b5cc` | Requested migration reference; active branch remains master to preserve cherry-pick |

No root origin correction required. No correction to nested/unrelated remotes attempted. Existing index fingerprint recorded for final preservation verification. Branch creation is not a snapshot of unstaged/untracked bytes; no full backup is claimed.

## Checks performed

Repository custody/status/config/worktree commands; eleven sibling pointer reads and failed read-only Git resolution attempts; hidden root/nested metadata/config discovery; PDF SHA-256 equality; directory/route/model/migration/source inspections; reference searches; sampled private path ignore/index exclusion checks; `python -B backend/scripts/frozen_integrity.py`.

Results: authorized root/origin pass; PDF copy pass; siblings unsafe to rename; root Git operation unresolved; deployment isolation fails inspection; frozen integrity fails at pre-existing readiness report edit. Wider `rg` count command unavailable, dedicated search used. No application test pass is newly claimed. See `VALIDATION_REPORT.md`.

Final preservation verification: HEAD and active branch unchanged; index hash matches the recorded baseline exactly; tracked staged/unstaged diff summaries unchanged. Intended-text whitespace checks for AGENTS and the seven markdown outputs emitted no findings. PDF destination hash was rechecked unchanged. No files staged.

## Remaining work / risks

1. Completed: user approved building and preservation-first quit/switch; migration branch is active.
2. Completed source-level custody/default repairs and nested-tool quarantine; private runtime ownership remains unaccepted and no historical worktree repairs were performed.
3. Confirm initial legal pack, roles/ACLs/retention/IdP/model policy and MVP ambiguity decisions.
4. Execute controlled C-M with additive migrations, real legal APIs/UI, citation integrity, independent review, durable timers and source freshness.
5. Resolve historical frozen hash mismatch through explicit owner decision, without falsifying benchmark evidence.
6. Provision isolated runtime resources, run all applicable regression/integration/security/UI/migration/recovery checks, record actual failures/limitations, show full validation report before any separately requested push.

Highest migration risks remain cross-tenant leakage, source/version loss, unauthorized review/state changes, timer loss, fabricated legal authority, private secondary data copies, inherited runtime collisions and accidental unrelated Git operations. Current reports document proposals; they do not establish operational-pilot readiness.

## Living build guide — 2026-10-06 follow-up

At the user's request, `LEGAL_DOMAIN_MIGRATION_PLAN.md` is now the canonical phase-by-phase execution guide. It includes a phase status/resume table, concrete A-M checklists, mandatory before/during/after phase procedures and a plan-change log. `AGENTS.md` requires reading the guide before every phase and synchronizing it with implementation changes, related architecture/reuse decisions, this progress record and validation evidence.

Files changed: `AGENTS.md`, `docs/LEGAL_DOMAIN_MIGRATION_PLAN.md`, `docs/MIGRATION_PROGRESS.md`, `docs/VALIDATION_REPORT.md`. Documentation only; no implementation phase started. Verified root/origin and unchanged index hash; intended-text whitespace checks emitted no findings. Next action remains Phase A custody resolution, followed by Phase B decision confirmation. The inherited cherry-pick and other recorded blockers remain unresolved. Changes are saved locally, not committed or pushed.

## Phase A start — 2026-10-06

User authorized phased building and requested a done/remaining report after each phase. Separately selected approval to `git cherry-pick --quit` and switch to the existing migration branch. Operation completed at unchanged HEAD `831c14909afc4ed1d2b778359df07f9e6b21b5cc`; before/after staged and unstaged binary diffs matched exactly. No abort, reset, stash, commit or push occurred.

Current step: tests-first configuration/CI isolation, active runbook correction and preservation-first quarantine of nested tooling. Existing local private `.env` is not overwritten; runtime services/models remain unexecuted until configuration ownership is verified. Product identity/feature conversion remains later phases.

## Phase A completion — 2026-10-06

### Delivered

- Activated `feat/legal-regulatory-platform-migration` at original HEAD after approved `git cherry-pick --quit`; exact pre/post binary diff comparison passed. Existing terms/auth staged work remains separate; Phase A edits are unstaged.
- Explicit main/test Compose project identities and project-scoped resources; DB `legal_compliance_workbench` on host 55432, Qdrant 16333/16334, backend 18000, frontend 15173, separate legal collection and model endpoint default 21434.
- Backend Compose requires explicit private model endpoint/host. No old 11434 fallback. Model provisioning/ownership is not claimed.
- Native settings/env template/proxy/CORS/launcher/offline profile agree with isolated defaults. Existing private `.env` was not overwritten.
- CI is manual-only, exact-repository gated and GitHub-hosted; removed old self-hosted environment and live-inference execution job.
- Compose backup command pins the legal project and rejects historical/foreign DB and Qdrant targets before external commands/network dispatch.
- Current runtime guide supersedes old setup links; historical handoff/deployment text remains truthfully labelled provenance. Nested tools/worktrees stay quarantined with no metadata changes.

### Files changed

Configuration/code: `.github/workflows/regression.yml`, `.env.example`, `backend/app/core/config.py`, `backend/scripts/backup.py`, `backend/tests/test_legal_repository_custody.py`, `backend/tests/test_phase_e.py`, `frontend/vite.config.js`, `infra/docker-compose.yml`, `infra/docker-compose.backend.yml`, `infra/docker-compose.auth-test.yml`, `infra/docker-compose.ui-api-test.yml`, `infra/offline.env.example`, `infra/start-backend.ps1`.

Operational docs: new `docs/LEGAL_RUNTIME_SETUP.md`, `README.md`, `backend/README.md`, `PROJECT_HANDOFF.md`, `docs/offline_deployment_and_release.md`. Living documents: plan/progress/validation/boundary/codebase audit/target architecture/reuse matrix.

### Verification

- Tests-first RED: four intentional custody assertion failures plus missing new backup guard import; GREEN: six custody tests pass, no app settings import or live service access.
- Base/backend/auth-test/UI-test Compose render-only validation passes; missing container model fields fail closed as expected.
- Vite syntax and imported config assertions pass. Frontend suite 39/39 passes; inherited WebSocket 24678 collision warnings remain. ESLint passes with two existing fast-refresh warnings; production build passes.
- A supplemental benchmark unit attempt could not collect because the selected system Python lacks Pydantic; not counted as a pass and no dependencies installed. Full backend/security/migration/runtime acceptance is pending.
- Broad diff whitespace check found inherited CRLF/whitespace warnings; focused Phase A check with `core.whitespace=cr-at-eol` passed without changing Git config or normalizing user files.

### Remaining and next action

Phase B: confirm initial public/synthetic source pack, local/private profile, role/ACL/review contracts, SSO/MFA scope, legal-pack ownership and acceptance thresholds. Phase C branding/UI identity, D-M legal capabilities and full validation remain unfinished. Existing private runtime config requires ownership review before use; frozen-readiness-report mismatch remains unchanged. No legal accuracy or operational-pilot completion is claimed.

Final checks: active branch/origin and unchanged HEAD verified; `.git/CHERRY_PICK_HEAD` absent; master PDF hash still matches its original bytes. Focused code/docs whitespace checks passed with CRLF recognition. Git status distinguishes inherited staged work from unstaged Phase A edits; nothing newly staged, committed or pushed. Per the user's request, report this phase's delivered work and remaining scope before advancing to B.

## Local checkpoint authorization — 2026-10-06

User requested regular commits while continuing the phased build. Root/origin/common metadata/hooks/status/diffs/recent log were rechecked. The user explicitly chose a separate preservation commit for the 17 inherited staged terms/auth files. Commit `34dc7af` (`Preserve inherited terms acceptance work`) records that original index without adding Phase A or unrelated frontend/benchmark work. Exact unstaged binary diff comparison passed across the commit. This is preservation evidence, not fresh backend/migration acceptance.

Next checkpoint records Phase A configuration, tests, current operational instructions and discovery/planning/provenance documents. Existing private/runtime files, nested Git/tooling, incoming archives, unrelated frontend work and modified frozen readiness report are excluded. Regular local commits are now authorized; pushes remain unauthorized.
