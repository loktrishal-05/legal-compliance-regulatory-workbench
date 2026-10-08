# Controlled legal-domain migration plan

Status: **three-team backend checkpoint published on 2026-10-06**. A/B complete; C backend identity verified; initial D slice tested, phase still in progress. User owns frontend/landing. Shared base 496f903 is published; three team branches/issues exist; main/development are protected. PR #4 holds handoff/CI corrections pending independent approval. Read `SESSION_RESUME.md` -> `CLAUDE_HANDOFF.md` and `TEAM_WORK_ALLOCATION.md`; main reconciliation is separate.

Current continuation (2026-10-07): E1 hardening is on open PR #13; development still `b3dcf4f`. Owner requests E2, ongoing verified commits/pushes and a README architecture/system-design/flowchart refresh. E2a locally verified: bounded native TXT/DOCX/PDF subprocess, immutable tenant/source-bound extraction/spans (head 0024), exact quote resolver and scoped APIs. 126 scoped checks and 32 focused checks pass; fresh/0018-to-0024 upgrades, old-trigger preservation and new immutable UPDATE/DELETE/TRUNCATE/lossy-downgrade rejection pass. Reuse PyMuPDF inspection with headings retained; no live model, real scanner enablement or frontend implementation. OCR execution/correction workflow, durable async dispatch and deployment-grade parser sandbox remain later E2 gates; DOCX/PDF native layout stays needs verification. Show checkpoint evidence before authorized publication; review/merge remains gated.

## How this guide must be used

2026-10-08 phase E resumed at owner request. First scope: remove the HTTP route's hardcoded absent scanner by adding an optional local ClamAV Unix-socket INSTREAM adapter, bounded deadline/output, fail-closed results and current-policy recheck after scanning (FR-007, supporting FR-002/003/010/054; E/L). Default remains unconfigured. Validate with synthetic protocol peers and scoped HTTP/DB journeys before any real scanner enablement. Actual engine/signature freshness/deployment approval remain separate acceptance gates; OCR/corrections/durable jobs/sandbox and E3 follow. Migration head remains 0024.

Owner-requested documentation promotion (2026-10-07): README-only PR #14 merged to main as 04d719f after full diff/rendering review and required CI, under explicit main visibility instruction. Main code baseline unchanged (only README differs from a85494d). Backend #13 remains open; independent feature/pilot review and all phase exit gates remain. Current root continuation/source head 0024; next implementation is unfinished E2 gates then E3. This documentation change does not approve a new architecture or legal policy.

Documentation/integration follow-up (2026-10-07): E2a published as `35f9e1b`; processed-upload replay corrected in the shared response contract after RED `2e033ba` and 6/6 API confirmation. README now documents actual source/runtime authority boundaries and labels future workflow diagrams explicitly. This changes presentation/evidence, not phase/FR acceptance or approved architecture. Remaining backend and owner-managed frontend/pilot gates stay open.

This is the canonical execution checklist for rebuilding the **existing** codebase into the Legal & Regulatory Assurance Platform. The unchanged master PDF remains the product authority; this guide translates it into ordered implementation work, not a claim of delivered capabilities.

Phase B's detailed [domain/permission/workflow/source contracts](LEGAL_DOMAIN_BUILD_CONTRACTS.md) and [66-requirement acceptance registry](LEGAL_REQUIREMENT_TRACEABILITY.md) are execution inputs for every relevant implementation phase. Update their actual component/test/demo evidence as work lands; no planning row is an implementation pass.

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
| B | Complete: approved development scope and domain/FR contracts | Operational-pilot pack/IdP/retention/recovery approvals remain release gates |
| C | Backend identity verified; frontend acceptance deferred to user | Preserve existing frontend changes; no further frontend implementation |
| D | Complete for development exit checks (head 0022); industrial regression suites not executable in available runtimes (recorded gap) | Start E secure intake on scoped versions |
| E | In progress — E1 hardened; E2a native spans/API verified (head 0024 on continuation PR) | Validated OCR/correction workflow, durable jobs and parser sandbox; E3 scoped retrieval |
| F | Not started | Contract analysis and grounded summaries |
| G | In progress — deterministic core tested | Registry/import/version persistence after merged source-span predecessor; allocate actual next revision centrally |
| H | In progress — deterministic core tested | Persist entities/mappings/assessments after source contracts; review binding with J |
| I | Not started | Durable obligations, deadlines and notifications |
| J | Not started | Expanded legal review, remediation and audit |
| K | Owner-managed, not accepted | User builds frontend; real-data/accessibility/end-to-end exit checks remain required |
| L | Not started | Legal evaluation and security hardening |
| M | Not started | Full isolated acceptance and recovery validation |

**Current instruction:** proceed with backend changes; the user will handle frontend and landing later. C frontend exit/design acceptance and K remain deferred, not passed. D backend work may proceed under this explicit scope change. Private service targets remain unaccepted.

Approved B baseline (2026-10-06): retain React/Vite and local/private AI; public/synthetic fixtures clearly labelled; no validated jurisdiction-compliance claim; local session auth for development only, enterprise SSO/MFA required for operational pilot; manual approved regulatory imports first; no automatic deletion/signing/filing. Deployment-specific legal packs, identity provider, retention and recovery acceptance stay release gates. This approval does not enable live services/models, deployment or a push.

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

- [x] Confirm the first operational slice against PDF pp. 52/59 and map all FR-001..066 to implemented or explicitly planned scope.
- [x] Resolve development scope and record operational-pilot approval gates for identity/MFA, collision-detection, jurisdiction/source/playbook, retention/legal hold, model policy and SLO/RPO/RTO; no deployment values are invented.
- [x] Specify workspace/matter/document role permissions, six assessment states and independent review authority.
- [x] Specify immutable source spans, version/effectivity semantics and legal AI output contracts.
- [x] Confirm reuse-first topology and additive DB/index compatibility strategy; record approved decisions and remaining release blockers.

Phase B exit: user-approved development profile; inspected mature session/revision/source/output models; domain contracts and all 66 catalogue FRs mapped to phase/deliverable/planned check; priorities preserved; version/ACL/state/AI/deadline invariants specified. This is design acceptance for development, not completed FRs or a legally validated operational pilot.

### Phase C — safe identity and configuration

- [x] Trace backend health identity through frontend validation and tests; change the coupled contract coherently.
- [x] Update active titles, package/lock metadata, public manifest, navigation/copy/help and product/design documentation using the PDF name. Browser fit/interaction acceptance is still pending.
- [x] Decide replacement branding assets and versioned legal terms; user approved neutral LRA assets and exact legacy terms preservation/labeling; new legal-platform terms remain a separate approval gate.
- [x] Configure independently named Compose resources, ports, DB/index targets, launcher/proxy/CORS and CI without touching existing shared resources. Delivered early in A because shared defaults were a custody risk; actual provisioning remains gated.
- [ ] Run relevant regression/frontend checks; verify no functional legal claims or cosmetic destructive storage renames were introduced.

C historical pause evidence: isolated backend identity 2/2, custody 6/6, focused frontend 14/14 and full frontend 44/44 passed; lint/build passed. The user subsequently authorized backend D progress while taking frontend/C/K acceptance themselves; bounded mocked browser observations and published saved identity evidence are in VALIDATION_REPORT. Do not resume frontend work or treat deferred frontend acceptance as passed. The old C-only pause dependency is superseded by this explicit scope decision.

### Phase D — legal core and access control

Current step: coordinate/review remaining D gates. Seven scoped ORM tables, DB-derived policy, two metadata APIs and migrations 0019/0020 were checkpointed/published in 87cd2bd; shared base is 496f903. 27 targeted checks and fresh/0018-to-head upgrades pass. 2026-10-06 (integrator, all teams unavailable): audited independent provisioning, operator bootstrap and explicit legacy mapping delivered with migration 0021 (`legal_provisioning.py`, `scripts/legal_provisioning_cli.py`); 41 scoped tests + migration validator pass on disposable PostgreSQL. Then 0022 workspace-scoped dedupe (legacy NULL-workspace namespace keeps global uniqueness; scoped versions unique per workspace; composite FK to the document's own scope), legacy-path guard on ten industrial read/dedupe/index sites, mapped versions stamped, and legal events excluded from the root audit log. 57/57 scoped tests + validator (fresh/0018 -> 0022, parity, reversibility, lossy-downgrade refusal) pass on disposable PostgreSQL. No legal intake/pilot acceptance yet. The user approved the existing tested identity snapshot; no new frontend implementation.

- [x] Reuse UUID/version/audit conventions; add Organization/Workspace/Membership/Matter and document-level access policy.
- [x] Add scoped source/domain references and validated API schemas; enforce server-derived context and tenant-qualified relationships.
- [x] Design explicit legacy ownership/quarantine and tenant-scoped deduplication; never guess private ownership. Done: unmapped documents stay denied; mapping is an audited operator command refusing re-mapping/foreign matters/duplicate bytes; 0022 dedupe per workspace without revealing other tenants' copies.
- [x] Audited independent provisioning: workspace admins grant/revoke others only, never self, never above own clearance, never beyond role operations; operator-only bootstrap; state + audit share one transaction (rollback tested).
- [x] Create reviewed additive migrations after baseline 0018 and register ORM models. Delivered 0019 legal scope and 0020 policy-denial audit vocabulary; source head is 0020.
- [x] Test fresh/current-to-head upgrades, cross-workspace access/mapping denial and old immutable/audit record preservation in a disposable database.
- [x] Isolate old paths: ingestion/P&ID dedupe and document reuse, retrieval ready-set, P&ID reads/evidence/indexing, verified knowledge, evidence integrity/sufficiency and knowledge-gap resolution use `legacy_version_clause`/`is_legacy_version`; root `/audit/log` uses `without_legal_audit`. Industrial suites could not run (bounded image lacks qdrant_client/langgraph; Windows Application Control blocks psycopg/ujson) — identical baseline/branch results for the runnable ones (agents_knowledge 25, knowledge 11, release_retrieval 7 OK; model_routing 4 pre-existing errors).

### Phase E — document intelligence

2026-10-07 continuation: E1 hardening verified locally on `integration/backend-continuation-20261007`, based on merged development `b3dcf4f`. Shared intake policy `legal-intake-v2` uses bounded streaming XML validation with DTD/entity rejection and decoded relationship attributes; rejects duplicate/case-colliding ZIP entries and unsupported compression; checks byte/hash lineage and duplicate originals; publishes originals with atomic create-only hard links instead of overwrite. FR-007/009/010 and E/L are affected. 93 scoped checks, 33 focused intake checks (96% service line coverage) and fresh/0018-to-0023 migrations pass. No new migration or extraction enablement. Next: E2 isolated extraction and exact source spans/corrections, then E3 authorized retrieval. A real approved malware scanner remains required before releasing real uploads from quarantine. Root AGENTS review/publication boundaries remain binding despite GitHub's current zero required approvals.

Current step (2026-10-06, integrator for Parts 1/2): E1 `app/services/legal_intake.py` + `POST /v1/workspaces/{id}/documents` (raw body, bounded read). Bytes decide PDF/DOCX/TXT; empty/oversize/macro/unsafe-path/archive-bomb/encrypted/type-mismatch/binary/unsupported/malformed input is rejected and audited, never stored. Active PDF content, embedded archives/objects, external references, scanner findings, and the absence of a configured malware scanner all quarantine. Originals are write-once, read-only, content-addressed per workspace and re-verified on reuse; dedupe is idempotent within a workspace and never reveals other tenants; uploader gets read only. Migration 0023 adds intake audit events. Next: E2 extraction for `received` versions only.

- [ ] Add secure upload/import with hash-preserved originals, type/size/archive limits, quarantine/scanning and isolated processing. Upload/limits/quarantine/originals done (E1); no malware engine is configured, so every real upload stays quarantined until one is approved; isolated processing comes with E2.
- [ ] Adapt PDF extraction and add DOCX/approved formats; reuse OCR with legal layout/quality handling and correction revisions.
- [ ] Persist exact version/page/section/offset/box source spans and derived-artifact lineage.
  E2a verified partial: immutable `legal_extractions`/`legal_source_spans`, composite version/hash/tenant FK, `POST .../versions/{id}/extractions`, `GET .../versions/{id}/spans/{id}`. TXT Unicode line offsets, DOCX part/paragraph coordinates (tables/headers/footnotes), PDF page/box locators with headings retained. Current grants checked before source load and after parser success/failure; read alone cannot invoke extraction. Byte snapshot/hash is reverified on idempotent retries. CPU/memory/file/output/deadline bounds are development containment, not a kernel network/filesystem sandbox; actual OCR, corrections and durable job dispatch are still pending.
- [ ] Propagate authorization/source metadata into dense/sparse retrieval, reranking and source viewers; use a controlled legal index rebuild.
- [ ] Verify duplicates, malformed/scanned documents, low-confidence correction, retry/failure state and scoped citations before accepting intake.

### Phase F — contract intelligence and summaries

- [ ] Add Contract/ContractVersion/Party/Clause and versioned approved playbooks linked to document spans.
- [ ] Implement constrained party/term/clause/duty/right/prohibition/trigger/deadline proposals with schema and provenance checks.
- [ ] Implement reviewable deviations, missing clauses, conflicts and exact/semantic version differences within approved scope.
- [ ] Generate executive/detailed/risk/obligation/action/change summaries with material-statement citations and coverage checks.
- [ ] Use existing immutable review primitives to gate accepted findings/obligations; validate source accuracy, missing-evidence refusal and golden fixtures.

### Phase G — regulatory intelligence

Current step (2026-10-06): owner reassigned Part 2 to the integrator. Pure `app/services/regulatory_versions.py` (half-open as-of selection, unknown/overlap -> needs verification, exact structural diff, failed check = unavailable) is tested. No persistence, registry approval, import or semantic AI proposal yet; persistent work waits for agreed/merged 0021.

- [ ] Add authoritative-source registry, trust/jurisdiction metadata and manual approved import; keep external acquisition separate from confidential content.
- [ ] Persist publication/effective periods, source hashes, amendments and supersession/version relationships.
- [ ] Extract proposed requirements and retain exact text/structural differences beside semantic change explanations.
- [ ] Require human applicability/materiality approval; map accepted changes to affected objects and persist watchlist/alert state.
- [ ] Verify historical version selection, provenance, freshness failure and change impact; label unconfigured live connectors honestly.

### Phase H — compliance assurance and digital twin

Current step (2026-10-06): pure `app/services/compliance_assessment.py` implements versioned declarative rules, six states with fixed precedence and reasons, accepted/expired/stale/superseded/conflicting evidence, drift reasons without rewriting history, and workspace-bounded blast radius. Visible component counts only; no weights/score. Entities, FKs, review binding and AI interpretation remain unbuilt.

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
| 2026-10-06 | User authorized regular local commits and separately approved preserved staged work; explicitly approved B development baseline. Added detailed domain contracts and 66-row FR registry; resolved development sequencing while retaining enterprise/legal/deployment gates | B/C-M; FR-001..066 and NFRs | Development architecture/contract checkpoint complete; no new legal feature/runtime pass; next C |
| 2026-10-06 | User takes ownership of frontend/landing and requests other changes only. Split C backend exit from deferred frontend acceptance so backend D-M can proceed without a frontend redesign; K deferred to user | C/D/K; identity/isolation FR-001..005 | Explicit user scope change; preserve frontend work, no further frontend edits; runtime/security gates remain |
| 2026-10-06 | User approved disposable PostgreSQL/backend tests; initial scope/API/policy and migrations 0019/0020 implemented | D/J/L; partial FR-002..004/054 | Initial slice tested; remaining D/intake/pilot gates stay open |
| 2026-10-06 | User requests three human teammate workstreams and publishing/review; remote main has unrelated history | D-M/all FRs, owner-managed K | `TEAM_WORK_ALLOCATION.md` defines ownership/dependencies/PR checks; no skipped gates, no force-push/main overwrite |

Append a row when an implementation discovery changes the plan. Include the reason, old/new decision or step, affected FRs/phases, and any approval dependency. Routine progress belongs in `MIGRATION_PROGRESS.md`; actual verification belongs in `VALIDATION_REPORT.md`.

## Requirements traceability plan

Handoff plan-change note (2026-10-06; all phases/FRs, documentation only): user requested one Claude continuation reference. CLAUDE_HANDOFF consolidates approvals/state/team/review instructions; SESSION_RESUME points to it, old notes are archived, and actual migration/CI/publication instructions are synchronized. Existing PR #4 carries the documentation; no implementation gate or approval is waived.

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
- Migration: approved bounded checks use `scripts.validate_legal_migrations` via legal-core-test Compose, fresh and historical 0018 to actual head 0020; Alembic parity/idempotency/source-audit-trigger preservation. Future changes append after verified head and extend immutable-record checks. Private applied schema remains unaccepted; do not run the older validator against private settings blindly.
- Retrieval/API integration: mocked adapters first; explicit disposable Qdrant/documents/role-scoped HTTP smoke next; no production/private service probing.
- E2E: contract source -> proposed analysis -> independent review -> accepted obligation; requirement/control/evidence -> freshness change -> finding -> remediation/retest; approved regulatory version -> diff/impact -> audit snapshot; restart timers; unauthorized-user attempts.
- AI/security: curated public/synthetic golden set, ungrounded output refusal, citation/version integrity, prompt injection, malicious files, cross-tenant search/exports/audit, secondary-copy logging checks. Separate approved live local evaluation from ordinary suite.
- Recovery: isolated backup/restore/reindex and configuration/key recovery rehearsal before operational-pilot readiness.

At each checkpoint: inspect callers -> minimal coherent diff -> relevant tests -> document commands/results/failures -> inspect root/origin/diff/status/recent log -> stage explicit intended paths -> local checkpoint commit -> verify committed paths and remaining user work. Stop if custody target unsafe. Do not include unrelated user work or push beyond recorded authorization/protected PR rules. Commit coherent verified milestones, not every tool call. Failed commits/hooks require correction/new attempt; no hook bypass, amend or history rewriting.

## Decisions requested with discovery approval

- Resolved: user approved quit-with-preservation and migration-branch activation; no commit or loss of staged/unstaged work.
- Delivered: current CI/defaults/runbooks isolated; nested tools/worktrees quarantined unchanged. Private runtime acceptance still required before operational commands.
- Approved: React/Vite and private/local inference for development; no automatic Next.js/hosted-AI switch.
- Approved: explicitly public/synthetic fixtures and manual approved imports for development; no actual jurisdiction/playbook authority or legal compliance claim. Scoped independent review contracts are defined.
- Development sequencing defined: basic source-grounded conflict/collision workflow; advanced simulations later. Enterprise SSO/MFA/re-auth, real legal packs/retention/hold and deployment performance/RPO/RTO remain operational-pilot gates, not silently waived requirements.
