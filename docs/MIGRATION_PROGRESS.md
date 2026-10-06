# Migration progress

Date: 2026-10-06. **Phase A committed; Phase B development contracts complete; Phase C next.**

## Current state

| Checkpoint | Status |
|---|---|
| A custody/report/discovery | Complete: preserved branch activation, isolated defaults/CI/runbooks, offline regression/frontend checks |
| B architecture/reuse | Complete: approved development baseline; domain/permission/state/provenance contracts and all 66 FR acceptance mappings |
| C identity | In progress; neutral identity and legacy-terms treatment explicitly approved |
| D-M implementation/validation | Not started |

Phase A changed configuration/backup guards and operational documentation; Phase B defined development contracts. Legal feature code/schema/migrations remain planned. Local checkpoints are now authorized and recorded below. No sibling/external repository, deployment, DB or model operation occurred; no push.

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

Completed Phase A checkpoint: `dfea5db` (`Isolate legal migration workspace and document phased build`), 29 explicit paths including immutable master PDF and preserved audit/handoff provenance. Custody suite revalidated 6/6 immediately before staging; PDF hash unchanged; staged whitespace check passed with CRLF recognition. Unrelated frontend/benchmark/runtime/tool content remains outside the commit.

## Phase B start — 2026-10-06

Read the living guide/progress/validation and target/reuse decisions. Master-report anchors: detailed FR catalogue pp.17-19, roles p.21, source/RAG/data contracts pp.27-29, guardrails/review pp.37-39, MVP/acceptance pp.52/59 and workflow/output/pack appendices pp.72/74/77. User explicitly approved the development baseline described in the guide. Deployment legal packs/IdP/retention policies remain unconfigured release gates.

Current step: document executable domain invariants, scoped role policy, review/status transitions, immutable/effective-date provenance and per-FR implementation/acceptance ownership. Phase B is an architecture/contract checkpoint, not feature delivery or legal accuracy acceptance.

## Phase B completion — 2026-10-06

Delivered `LEGAL_DOMAIN_BUILD_CONTRACTS.md`: initial end-to-end operational slice; tenant/matter/document ownership; additive source/hash/revision migration strategy; scoped role matrix and administrator boundaries; six assessment states, independent review/remediation transitions; immutable source spans/effective-vs-recorded time; legal AI proposal/API contracts; deterministic deadline/recovery semantics and pilot gates.

Delivered `LEGAL_REQUIREMENT_TRACEABILITY.md`: FR-001 through FR-066, preserving catalogue Must/Should priorities, with owning phases, core/extended/pilot/later sequencing, deliverables and planned verification. Every legal FR remains **planned**, not delivered by these documents. Related target/reuse/guide records synchronized.

Approval: user explicitly selected the development baseline (React/Vite, private/local AI, public/synthetic fixtures, local auth development-only, enterprise identity pilot gate, manual approved imports, no automatic deletion/signing/filing). Unknown legal pack/IdP/retention/RPO/RTO values are named release gates, not guessed settings.

Verification: inspected current session/dependency, immutable ActionRevision, Document/DocumentVersion, Query and S1-S7 output contracts to avoid incompatible redesign. Content search returned 66 ordered distinct FR table rows (001-066); catalogue priorities reviewed against the master report; permission/source/review/state/deadline invariants reviewed for consistency. No runtime tests are represented as Phase B domain acceptance. New and changed documentation whitespace/diff checks are recorded in the validation report.

Files changed: new domain contracts/requirement registry; target architecture, reuse matrix, living guide, progress and validation. Next phase C safely adapts product/service/package/UI identity without claiming unimplemented legal capability. D-M models/workflows/UI/security/runtime validation and pilot-specific approvals remain unfinished. Existing unrelated frontend/benchmark/tool/runtime work is preserved outside checkpoint scope.

Checkpoint preparation: seven explicit Phase B document paths only, with requirement coverage and whitespace/diff checks complete. Local commit message: `Define legal domain contracts and requirement acceptance`. Record the resulting commit ID in the next phase/session log; never amend a checkpoint to insert its own hash. No push authorized.

## Phase C start — 2026-10-06

Phase B committed as `3f94383`. Read guide/progress/validation and inspected coupled service/UI identities and current branding/copy. User approved retaining layout/fonts/palette, a neutral LRA development mark and full PDF product name; active industrial footage/branding stops while original assets/motion infrastructure are retained. Separately approved retaining exact v1.0 legacy terms and acceptance history, visibly labelled until a new legal-platform version is approved.

Current scope: health title/validator identity, package/HTML/manifest/assets, shared logo/page titles, landing/auth/shell migration copy, help/legacy terms notices and product/design documentation. Existing industrial runtime routes remain legacy until their validated replacement phases; no cosmetic database/index rename or new legal feature claims. Existing uncommitted frontend work must be preserved and separated before checkpointing overlapping files.

User separately approved frontend preservation. Commit `1968d2e` records 29 existing frontend/resource/help paths; 39/39 frontend tests passed immediately beforehand; unrelated binary diffs matched across commit. This snapshot is not legal-domain acceptance. Benchmark/private/runtime/nested-tool/cache work stayed excluded.

Phase C RED: new backend identity target has two expected assertion failures; focused frontend identity/API target has five expected failures (metadata/logo/landing/auth/help/legal service mismatch) and nine existing passes. No missing dependency caused these failures. Current local venv's FastAPI import is blocked by OS Application Control on `ujson`; do not disable protection. Backend identity checks execute the actual pure health function via AST and inspect title metadata without private settings/services/native DLLs. Full backend HTTP/runtime acceptance remains a later supported-environment gate.
