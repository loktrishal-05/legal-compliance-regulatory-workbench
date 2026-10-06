# Controlled legal-domain migration plan

Status: phased building and regular local checkpoint commits authorized by the user on 2026-10-06; Phase A source custody/configuration complete. Phase B product-policy decisions remain pending. No push authorized. Preserve all existing user work, historic migrations, immutable records and frozen industrial evidence.

## How this guide must be used

This is the canonical execution checklist for rebuilding the **existing** codebase into the Legal & Regulatory Assurance Platform. The unchanged master PDF remains the product authority; this guide translates it into ordered implementation work, not a claim of delivered capabilities.

**Before starting or resuming every phase:**

1. Read this guide, `MIGRATION_PROGRESS.md` and `VALIDATION_REPORT.md`; identify the first unfinished step and its blockers.
2. Read the relevant PDF pages/FRs, target architecture and reuse decisions. Verify the actual implementation rather than relying on historical completion claims.
3. Recheck repository/service custody and existing user changes. Resolve the phase's entry requirements before commands that can affect Git state, data or runtime services.
4. Inspect every intended change location and its callers; select the smallest coherent reuse-first implementation.
5. Mark the phase `in progress` and record its concrete scope and next step before implementation. Do not silently skip prerequisites or broaden scope.

**During implementation:** update this guide in the same work whenever discoveries or changes alter steps, paths, models, interfaces, dependencies, scope, acceptance criteria or phase ordering. Record why the plan changed and which FRs/phases are affected. Update target architecture/reuse decisions when necessary. Material legal/security/provider/retention choices still require approval; do not silently resolve them by editing the plan.

**Before ending a phase or session:** record files changed, actual commands/results, known issues, decisions and the next unfinished step in `MIGRATION_PROGRESS.md`; synchronize phase status here and evidence in `VALIDATION_REPORT.md`. Mark `complete` only after the phase's exit checks pass. If blocked or partial, say so. No unattended updater is required: keeping these documents current is a mandatory part of each build change.

## Phase status and resume point

| Phase | Current status | Next action |
|---|---|---|
| A | Complete: source custody, isolated defaults/CI, offline checks | Private runtime provisioning and acceptance remain gated for later phases |
| B | Architecture/reuse/plan prepared; decisions pending | Confirm initial slice, scope ambiguities and legal/security policies |
| C | Not started | Begin identity/config adaptation after A/B entry gates |
| D | Not started | Scoped legal core and additive migrations |
| E | Not started | Secure generic document intake and provenance |
| F | Not started | Contract analysis and grounded summaries |
| G | Not started | Approved regulatory imports and version changes |
| H | Not started | Requirement/control/evidence assessment and digital twin |
| I | Not started | Durable obligations, deadlines and notifications |
| J | Not started | Expanded legal review, remediation and audit |
| K | Not started | Incremental real-data legal frontend |
| L | Not started | Legal evaluation and security hardening |
| M | Not started | Full isolated acceptance and recovery validation |

**Resume at B.** Read the Phase A evidence in `VALIDATION_REPORT.md`, then confirm the initial slice and remaining product-policy decisions. No private runtime targets are yet accepted: before any service, DB migration, backup or model execution, follow `LEGAL_RUNTIME_SETUP.md` and verify effective configuration ownership. Do not treat new defaults as proof that an old `.env` is safe.

## Prerequisite decisions

The inherited cherry-pick operation was quit (not aborted or committed) with explicit user approval; staged and unstaged diffs matched exactly before/after switching to `feat/legal-regulatory-platform-migration` at the original HEAD. Current-workspace CI/service repairs are part of the authorized Phase A build. Nested tools remain quarantined from application operations; no nested metadata replacement/deletion or historical worktree repair is authorized. Record actual DB schema only after an isolated test environment is explicitly provisioned.

## Checkpoints and exit evidence

| Checkpoint | Scope / candidate paths | Required verification / exit |
|---|---|---|
| A: custody/report/audit | PDF, AGENTS, seven migration markdowns, branch reference; approved follow-up CI/config/runbook custody repair | Exact root/origin, user index preservation, worktree classifications, complete PDF/hash; unresolved custody blockers visible |
| B: architecture/reuse | Reuse matrix/target/plan, requirement mapping and role/state/source contracts | Approve boundaries, MVP vs catalogue, jurisdiction assumptions and no destructive schema/index renames |
| C: safe product identity | `main.py`, health route+frontend health validator, packages/locks/index/manifest, UI copy/resources, README/PRODUCT/DESIGN, env/Compose/Vite/launcher/CI | Relevant identity/auth/frontend tests/lint/build; isolated config review; no existing DB/Qdrant rename or deployment |
| D: legal core + authorization | Add scoped ORM/Pydantic/services/routes and migrations after 0018; reusable auth/deps and model registration | Fresh/current-to-head on disposable DB; cross-workspace FK/ACL/role tests; preserve old immutability/hash chains |
| E: document intelligence | Ingestion/extraction/OCR/chunk/citation contracts, generic upload/storage/source spans | PDF/DOCX/scan/malformed/path/size/quarantine tests, exact original/version/page lineage, correction provenance, retry/duplicate behavior |
| F: contract intelligence | Contract/parties/clauses/playbook analysis, structured legal output/prompts/gateway integration, cited summaries | Synthetic/public golden clauses/obligations/summary coverage, source jump, deviations/missing clauses/redline, missing-evidence refusal and review-only promotion |
| G: regulatory intelligence | Source registry/manual import/version/diff/effective date/requirement/applicability mappings | Authority/version/amendment/effectivity tests, manual freshness, human applicability, change impact; live connectors explicitly not configured |
| H: compliance assurance | Requirements/controls/policies/evidence/assessment/finding relations | Six-state rule/evidence tests, missing/stale evidence, drift, control mapping and relational blast radius; visible reasons |
| I: obligations/deadlines | Owner/trigger/approved due date/recurrence/notification/escalation/task persistence | Timezone/ambiguous date tests, clock/restart/retry/duplicate occurrence and deterministic scheduler behavior |
| J: governance/review | Legal revision linkage, decision vocabulary, new audit events/migrations, remediation closure/retest/release | Independent reviewer, self-approval denial, request-changes history, concurrent revoke/release, exact evidence/policy/hash binding, audit atomicity |
| K: frontend migration | Keep shell/session/components; add legal domain feature pages/routes/source review; adapt dashboard/knowledge/audit/admin/resources | Backend-fed journeys, loading/empty/error/degraded states, keyboard/responsive accessibility, role gating, tests/lint/build; no fake numbers |
| L: evaluation/security | Legal fixtures/evaluation, scoped retrieval/prompt injection/upload/logging/privacy, role and tenant matrix | Grounding/refusal/coverage/extraction/temporal-version gates, cross-tenant denial, malicious document containment; no live inference without explicit approval |
| M: full validation | Disposable runtime acceptance, migrations/backup restore/API/integration/retrieval/UI/security, docs | Reproducible commands and failures, acceptance journeys/restart/restore, known limitations and remaining FRs; full report shown before any requested push |

Security and tenant isolation start at D/E and apply to every subsequent checkpoint; L is additional hardening, not permission to postpone controls. Finding review must gate authoritative promotion in F-H even before J expands review UX/state vocabulary. Checkpoint K can deliver domain pages incrementally once their APIs exist; no mock-first legal dashboard.

## Step-by-step implementation checklist

Checked steps denote verified work only. The table above and exit evidence remain authoritative for phase completion.

### Phase A — repository custody and discovery

- [x] Verify exact root/origin; record HEAD, active branch, staged/unstaged/untracked state and registered worktrees.
- [x] Inspect sibling/nested metadata read-only; classify historical pointers and prevent unrelated operations.
- [x] Copy the master PDF unchanged, verify its hash and read all 80 pages.
- [x] Save codebase audit, reuse matrix, target architecture, build plan, progress and validation documents.
- [x] Obtain explicit user direction on the unfinished cherry-pick and existing work; safely activate the migration branch only after resolution.
- [x] Approve and apply current-workspace-only CI/runbook/service isolation; decide nested-tool custody without modifying historical repositories.
- [x] Recheck index/user-work preservation and resource targets; document any remaining custody blockers before advancing.

Phase A exit: exact legal branch/origin confirmed; quit/switch preserved staged/unstaged diffs; six offline custody regressions pass; four Compose configurations render; missing dedicated model endpoint is rejected; frontend 39 tests/lint/build pass. Nested tools and historical pointers remain **quarantined, unchanged, excluded from application operations**, not repaired. Runtime/private `.env` ownership, actual DB/model provisioning, full backend acceptance and frozen hash mismatch are explicitly deferred gates, not passed checks.

### Phase B — approve the target and acceptance contracts

- [ ] Confirm the first operational slice against PDF pp. 52/59 and map all FR-001..066 to implemented or explicitly planned scope.
- [ ] Resolve identity/MFA, collision-detection, jurisdiction/source/playbook, retention/legal hold, model policy and SLO/RPO/RTO decisions.
- [ ] Specify workspace/matter/document role permissions, six assessment states and independent review authority.
- [ ] Specify immutable source spans, version/effectivity semantics and legal AI output contracts.
- [ ] Confirm reuse-first topology and additive DB/index compatibility strategy; record approved decisions and remaining release blockers.

### Phase C — safe identity and configuration

- [ ] Trace backend health identity through frontend validation and tests; change the coupled contract coherently.
- [ ] Update active titles, package/lock metadata, public manifest, navigation/copy/help and product/design documentation using the PDF name.
- [ ] Decide replacement branding assets and versioned legal terms; retain prior acceptance/history and truthful provenance.
- [x] Configure independently named Compose resources, ports, DB/index targets, launcher/proxy/CORS and CI without touching existing shared resources. Delivered early in A because shared defaults were a custody risk; actual provisioning remains gated.
- [ ] Run relevant regression/frontend checks; verify no functional legal claims or cosmetic destructive storage renames were introduced.

### Phase D — legal core and access control

- [ ] Reuse UUID/version/audit conventions; add Organization/Workspace/Membership/Matter and document-level access policy.
- [ ] Add scoped source/domain references and validated API schemas; enforce server-derived context and tenant-qualified relationships.
- [ ] Design explicit legacy ownership/quarantine and tenant-scoped deduplication; never guess private ownership.
- [ ] Create reviewed additive migrations after the actual existing head; register ORM models without rewriting prior migrations.
- [ ] Test fresh/current-to-head upgrades, cross-workspace access/mapping denial and old immutable/audit record preservation in a disposable database.

### Phase E — document intelligence

- [ ] Add secure upload/import with hash-preserved originals, type/size/archive limits, quarantine/scanning and isolated processing.
- [ ] Adapt PDF extraction and add DOCX/approved formats; reuse OCR with legal layout/quality handling and correction revisions.
- [ ] Persist exact version/page/section/offset/box source spans and derived-artifact lineage.
- [ ] Propagate authorization/source metadata into dense/sparse retrieval, reranking and source viewers; use a controlled legal index rebuild.
- [ ] Verify duplicates, malformed/scanned documents, low-confidence correction, retry/failure state and scoped citations before accepting intake.

### Phase F — contract intelligence and summaries

- [ ] Add Contract/ContractVersion/Party/Clause and versioned approved playbooks linked to document spans.
- [ ] Implement constrained party/term/clause/duty/right/prohibition/trigger/deadline proposals with schema and provenance checks.
- [ ] Implement reviewable deviations, missing clauses, conflicts and exact/semantic version differences within approved scope.
- [ ] Generate executive/detailed/risk/obligation/action/change summaries with material-statement citations and coverage checks.
- [ ] Use existing immutable review primitives to gate accepted findings/obligations; validate source accuracy, missing-evidence refusal and golden fixtures.

### Phase G — regulatory intelligence

- [ ] Add authoritative-source registry, trust/jurisdiction metadata and manual approved import; keep external acquisition separate from confidential content.
- [ ] Persist publication/effective periods, source hashes, amendments and supersession/version relationships.
- [ ] Extract proposed requirements and retain exact text/structural differences beside semantic change explanations.
- [ ] Require human applicability/materiality approval; map accepted changes to affected objects and persist watchlist/alert state.
- [ ] Verify historical version selection, provenance, freshness failure and change impact; label unconfigured live connectors honestly.

### Phase H — compliance assurance and digital twin

- [ ] Add separate Requirement/Policy/Control/Evidence/Assessment/Finding revisions and scoped relational mappings.
- [ ] Implement approved deterministic evaluations and provisional grounded AI interpretation with six explainable states.
- [ ] Implement evidence expiry/replacement and source/control/contract drift invalidation without deleting historical assessments.
- [ ] Traverse relational links for change blast radius; expose component status and evidence sufficiency instead of opaque scores.
- [ ] Test mapping integrity, insufficient/stale evidence, applicability, review requirements and current-versus-historical state.

### Phase I — obligations, deadlines and monitoring

- [ ] Promote reviewed obligations into persistent owner/trigger/condition/source-linked records.
- [ ] Normalize approved deadlines/notice windows with timezone/calendar/recurrence policy; route ambiguous dates to review.
- [ ] Implement durable occurrence dispatch, reminder/escalation receipts and in-app notifications using deterministic logic.
- [ ] Add task/dependency tracking and evidence requests; model unconfigured external notification delivery explicitly.
- [ ] Kill/restart/retry workers and duplicate events in isolation; prove no lost timers or duplicate authoritative actions.

### Phase J — legal governance, remediation and audit

- [ ] Extend independent legal/compliance review with approve/reject/request-changes/escalation while retaining immutable prior decisions.
- [ ] Bind findings/accepted obligations to exact source, evidence, analysis, prompt/model/rule/policy versions.
- [ ] Add audited remediation submission, closure evidence, reviewer approval, retest and reopening behavior.
- [ ] Extend constrained audit event vocabulary through migrations; add scoped historical snapshots/basic evidence exports.
- [ ] Verify self-approval denial, concurrent revoke/release, citation sufficiency, audit atomicity and replay integrity.

### Phase K — legal frontend, incrementally by validated API

- [ ] Retain shell/session/terms/role/loading/empty/error patterns and build contract/document/source-clause review surfaces.
- [ ] Add regulatory source/version/diff/impact views, requirement/control/evidence/assessment and finding/remediation views.
- [ ] Add obligations/calendar/alerts/review queue and adapt assistant/knowledge/executions/audit/admin/profile.
- [ ] Replace active industrial navigation/pages only after callers and generic components are separated; dashboards use real scoped data.
- [ ] Validate complete journeys, keyboard/focus/responsive behavior, source jumps, role denial and frontend tests/lint/build.

### Phase L — legal evaluation and security hardening

- [ ] Create public/synthetic legal golden fixtures and approved extraction/summary/grounding/refusal/temporal acceptance thresholds.
- [ ] Test access across every resource/retrieval/export/audit path and roles/tenants, including index and model context leakage.
- [ ] Test malicious files, indirect prompt injection, source poisoning, tool misuse and unsupported authority claims.
- [ ] Review log/checkpoint/export secondary copies, session/origin controls, quotas, secrets and least-privilege deployment settings.
- [ ] Preserve platform regression and historical industrial benchmark integrity; record unresolved findings without changing expectations to obtain green results.

### Phase M — full acceptance and handoff

- [ ] Execute applicable backend/frontend/integration/API/retrieval/security/migration checks in verified isolated resources.
- [ ] Demonstrate all three pillars end to end, source/version change, evidence expiry, independent review and deterministic restart-safe monitoring.
- [ ] Rehearse backup/restore/reindex and configuration/key recovery; measure approved performance and recovery gates.
- [ ] Reconcile every FR with actual code/tests/demo evidence; list incomplete features, unconfigured integrations, blockers and jurisdiction validation.
- [ ] Synchronize this guide, progress, architecture/reuse and full validation report; inspect final diff and present the report to the user.
- [ ] Push only if separately and explicitly authorized after the report is presented; reverify the exact authorized repository first.

## Plan-change log

| Date | Change / reason | Affected phases / requirements | Approval or delivery status |
|---|---|---|---|
| 2026-10-06 | User requested a permanent phased build document that must be read before each phase and kept synchronized during building; expanded existing plan into an execution checklist and added AGENTS instructions | A-M; process for all FRs | Documentation workflow requested; implementation not started; existing custody/product-policy decisions remain open |
| 2026-10-06 | User authorized building and explicitly approved quit-with-preservation/branch activation. Moved C's service/proxy/default isolation into A, added offline custody regression and current runtime guide; quarantined nested tools instead of altering metadata | A/C/M; security/isolation NFRs, FR-065/066 operational support (not full delivery) | A source/config exit checks passed; no deployment/private configuration acceptance; B product-policy decisions still pending |

Append a row when an implementation discovery changes the plan. Include the reason, old/new decision or step, affected FRs/phases, and any approval dependency. Routine progress belongs in `MIGRATION_PROGRESS.md`; actual verification belongs in `VALIDATION_REPORT.md`.

## Requirements traceability plan

Use the detailed PDF catalogue, not its shifted p.67 overview ranges:

| IDs | Ownership / checkpoint |
|---|---|
| FR-001..005 identity/isolation/ACL/re-auth | C/D/L; enterprise identity gate approval required |
| FR-006..011 secure formats/OCR/hash/correction | E/L |
| FR-012..019 contract facts/clauses/obligations/playbook/conflicts/redlines/accepted reminders | F/I/J |
| FR-020..025 audience summaries/citations/uncertainty/synthesis/exports | F/K/M |
| FR-026..032 authoritative sources/version/diff/applicability/watchlists | G/H/I |
| FR-033..040 separated compliance entities/mappings/rules/states/freshness/drift/explainable scoring | D/H/L |
| FR-041..045 durable reviews/tasks/comments/timers | I/J/K |
| FR-046..047 exceptions/bulk triage | Later extension; retain as Should backlog |
| FR-048..053 hybrid authorized search/citations/refusal/memory | E/F/L |
| FR-054..060 audit/provenance/replay/dashboards/packs/export/archive | J/K/M; high-assurance archive profile later |
| FR-061..066 governed connectors/service scopes/events/config/model policy/recovery-retention | G/I/L/M and explicitly tracked post-pilot integrations |

Every implemented requirement must point to source page/ID, changed component, runnable check and demonstration evidence. Unimplemented FRs remain planned; historic industrial tests do not satisfy legal accuracy gates.

## Compatibility/data strategy

1. Keep old table names, IDs, migration files and audit envelopes intact. Add legal entities and scoped links; no destructive industrial table drop.
2. Explicitly assign/quarantine legacy ownership before adding tenant constraints. Do not infer tenants from equipment/facility names. Hash dedupe becomes workspace/tenant-scoped without rewriting evidence hashes.
3. Use separately provisioned DB and Qdrant for the legal environment. Naming changes via configuration/new storage, not destructive rename of shared volumes or collections.
4. Index cutover: new schema-versioned legal collection, authorize/payload backfill/rebuild from immutable originals, verify counts/hash/citation/ACL parity, controlled config/alias cutover with rollback. Do not execute inherited delete/promote helper as cosmetic rename.
5. Old industrial endpoints/tools/prompts/tests remain until callers are mapped and legal replacements validated; disable active industrial navigation/routing coherently. Preserve archives/provenance instead of deleting old-looking files.
6. Version legal terms and preserve prior acceptances; legal wording requires owner review. Do not relabel existing industrial legal disclaimers as counsel-approved terms.

## Verification commands (planned, not executed here)

- Backend: existing `python -m unittest discover -s backend/tests -v`, plus targeted legal/security modules, with explicitly verified disposable DB/data/model settings; no live model flags by default.
- Frontend: `npm.cmd --prefix frontend test`, `npm.cmd --prefix frontend run lint`, `npm.cmd --prefix frontend run build` after isolated dependency availability is checked.
- Migration: adapt/use `scripts.validate_migrations` against a dedicated disposable PostgreSQL; baseline current 0018 and fresh; `alembic check`; immutable-table/trigger survival and preserved old records.
- Retrieval/API integration: mocked adapters first; explicit disposable Qdrant/documents/role-scoped HTTP smoke next; no production/private service probing.
- E2E: contract source -> proposed analysis -> independent review -> accepted obligation; requirement/control/evidence -> freshness change -> finding -> remediation/retest; approved regulatory version -> diff/impact -> audit snapshot; restart timers; unauthorized-user attempts.
- AI/security: curated public/synthetic golden set, ungrounded output refusal, citation/version integrity, prompt injection, malicious files, cross-tenant search/exports/audit, secondary-copy logging checks. Separate approved live local evaluation from ordinary suite.
- Recovery: isolated backup/restore/reindex and configuration/key recovery rehearsal before operational-pilot readiness.

At each checkpoint: inspect callers -> minimal coherent diff -> relevant tests -> document commands/results/failures -> inspect root/origin/diff/status/recent log -> stage only intended paths -> local checkpoint commit -> verify committed paths and remaining user work. Stop if custody target unsafe. Do not include unrelated user changes or push. Commit at verified phase boundaries or coherent intermediate milestones, not after every tool call. Failed commits/hooks require correction and a new commit attempt; no hook bypass, amend or history rewriting.

## Decisions requested with discovery approval

- Resolved: user approved quit-with-preservation and migration-branch activation; no commit or loss of staged/unstaged work.
- Delivered: current CI/defaults/runbooks isolated; nested tools/worktrees quarantined unchanged. Private runtime acceptance still required before operational commands.
- Approve retaining React/Vite and private/local inference for the initial slice, rather than adopting recommended Next.js/hosted AI automatically.
- Select initial jurisdiction/industry/source/playbook and reviewer acceptance policy, or approve explicitly synthetic packs until those exist.
- Resolve SSO/MFA and advanced conflict-detection scope inconsistencies; define operational-pilot identity, retention/legal hold and performance/recovery acceptance gates.
