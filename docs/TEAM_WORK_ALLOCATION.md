# Three-team backend build and integration handoff

Date: 2026-10-06. This divides all remaining backend work; it does not reduce the master requirements or waive phase gates. Frontend/landing implementation belongs to the user. The master PDF stays unchanged.

## Published checkpoint and work tickets

Reviewed implementation checkpoint: `87cd2bd` on the shared development base. The owner explicitly approved publishing the saved tested identity snapshot, the partial backend milestone and PR protection. No new frontend implementation occurred.

- Baseline CI passed: https://github.com/loktrishal-05/legal-compliance-regulatory-workbench/actions/runs/37491748786
- Part 1 ticket: https://github.com/loktrishal-05/legal-compliance-regulatory-workbench/issues/1
- Part 2 ticket: https://github.com/loktrishal-05/legal-compliance-regulatory-workbench/issues/3
- Part 3 ticket: https://github.com/loktrishal-05/legal-compliance-regulatory-workbench/issues/2

Tickets assign work to the three owner slots; GitHub assignees remain unset until the user supplies their actual handles. Verified remote team baseline is `496f903`; all three assigned team branches exist at that commit. Latest baseline CI passed: https://github.com/loktrishal-05/legal-compliance-regulatory-workbench/actions/runs/37492025870 . Both main and the shared development base are protected: required `legal-core`, up-to-date branch, one independent/latest-push approval, stale review dismissal, resolved conversations and admin enforcement; force pushes/deletions disabled. Main remains `d95dfc3`. Baseline CI success does not complete D or accept future teammate features.

## Shared baseline and branches

- Repository: `https://github.com/loktrishal-05/legal-compliance-regulatory-workbench.git` only.
- Shared development base: `feat/legal-regulatory-platform-migration`. Clone that branch rather than `main` for this build.
- GitHub default branch is `main`. As of this handoff it has **no merge base** with the local migration history. Do not force-push, overwrite `main`, or merge unrelated histories automatically. A reviewed reconciliation plan and owner approval are required before promotion to `main`.
- Names are not supplied yet: **Team member 1**, **Team member 2**, **Team member 3** are assignment slots. Replace them with GitHub handles when the owner supplies them; do not guess contributors or grant repository access.
- Use separate feature branches. Open PRs against the shared development base. No direct team pushes to `main` or the shared base.

```powershell
git clone --branch feat/legal-regulatory-platform-migration https://github.com/loktrishal-05/legal-compliance-regulatory-workbench.git
```

Inside each teammate's own clone, create their assigned branch:

| Slot | Branch | Primary work |
|---|---|---|
| Team member 1 | `team/1-documents-contracts` | Remaining D foundation, E secure intake/source lineage, F contracts/grounded summaries/search |
| Team member 2 | `team/2-regulatory-compliance` | G regulation/source/version changes, H requirements/controls/evidence/assessment |
| Team member 3 | `team/3-workflows-assurance` | I obligations/timers, J review/remediation/audit, cross-team L security and M acceptance/recovery |

The integrating assistant reviews incoming PRs, runs relevant checks, fixes reviewed defects on explicit contributor/integration branches, updates consolidated evidence, and merges accepted work into the development base. Promotion to `main` waits for history reconciliation and the complete acceptance report. Review is active during an assistant session; GitHub Actions checks run automatically between sessions. No unattended AI approval or continuous assistant monitoring is claimed.

## Mandatory reading and common rules

Read `AGENTS.md`, `SESSION_RESUME.md`, `LEGAL_DOMAIN_MIGRATION_PLAN.md`, `MIGRATION_PROGRESS.md`, `VALIDATION_REPORT.md`, `LEGAL_DOMAIN_BUILD_CONTRACTS.md`, `LEGAL_REQUIREMENT_TRACEABILITY.md` and relevant master-report pages before each phase. Inspect existing callers before changing a shared component. The living guide's dependencies and exit checks still apply.

Use public/synthetic fixtures only. No private `.env`, source documents, secrets, model weights, customer data, nested tool repositories, historical worktrees, benchmark evidence edits, or deployment artifacts in commits. Current industrial terms/consents and old immutable/audit hashes remain intact. No live inference/deployment/private-DB migration without separate permission. Frontend acceptance remains pending with the owner.

Each PR includes: phase/FR IDs, exact paths, requirement basis, tests and commands/results, fixture provenance, migration baseline/head, actual limitations, demonstration evidence, and the next step. Update the living guide/progress/validation in the same change; coordinate edits to their phase rows rather than overwrite another team's evidence. No phase/FR is complete merely because code or a PR exists.

## Part 1 — documents, legal core, contracts and grounded answers

**Owner:** Team member 1. **Phases:** remaining D, E, F; document/retrieval portion of L. **Requirements:** FR-001..025, FR-048..053, provider/data-policy implementation in FR-065. Enterprise SSO/MFA/re-auth, actual legal terms and validated legal packs remain approval/pilot gates, not skipped requirements.

### Ordered tasks

1. Finish D: audited independent membership/reviewer provisioning, explicit legacy ownership/quarantine, workspace-scoped duplicate/version strategy, tenant-qualified legal/source relationships and compatibility guards on old content APIs. Existing `authorize_workspace`/`authorize_document` are prerequisites, not final review/release authority.
2. Prepare additive migration 0021 for agreed source/version changes; preserve earlier migrations/IDs/immutability/hash chains. No guessed private ownership. Existing global `DocumentVersion.source_sha256` uniqueness and global industrial retrieval must be addressed coherently before legal intake is enabled.
3. E: secure PDF/DOCX/TXT/image/approved-format intake, preserved originals and storage references, size/type/archive limits, malware/quarantine/parser isolation, deterministic lifecycle/retries/idempotency, OCR quality and correction revisions.
4. Store exact source spans with immutable version/hash/page/section/offset/box lineage. DOCX gets paragraph/section locators; no invented page numbers. Deliver version/span APIs and a source resolver for Parts 2/3.
5. Apply authorization before dense/sparse retrieval, reranking, source reads, summaries, memory and exports. Keep indexes as rebuildable projections; no global retrieve-then-hide shortcut.
6. F: contracts/versions/parties/clauses, governed playbooks, source-linked facts/duties/triggers/dates, missing/deviating clauses, basic conflict checks and exact/semantic version differences. Outputs remain proposals.
7. Executive/detailed/clause/risk/obligation/action/change summaries with material-statement citations, coverage and uncertainty; approved export contract. Integrate private gateway through pinned task/schema/prompt policies. No fabricated jurisdiction or AI confidence-as-authority.
8. Development identity remains local-session only until enterprise identity is implemented/accepted. Preserve active terms and session/origin/no-store behavior; never add trusted user/role headers.

**Owned paths:** new document/contract/source model, schema, service, route and fixture/test modules under existing `backend/`; supporting source/retrieval adapters after caller review. No frontend edits. Coordinate shared registration/auth/gateway changes with the integrator.

**Required checks:** malformed/oversized/archive/path/quarantine files; real synthetic PDF/DOCX/scans; hash/version/locator integrity; same bytes in different workspaces; correction/retry/duplicate behavior; cross-tenant reads/search/reranker/export denial; golden extraction/summary coverage/refusal; independent-review integration. Demonstrate source -> clause -> cited proposal/summary, including one extraction failure.

**Handoff to Parts 2/3:** exact version/span resolver, current authorized document eligibility/query contract, proposal schema, stable source-version references and draft obligation/finding payloads. Parts 2/3 can develop against labelled synthetic fixtures before integration, but cannot mark dependent phases complete before D/E checks pass.

## Part 2 — regulatory intelligence and compliance assurance

**Owner:** Team member 2. **Phases:** G/H and regulatory connector scope of FR-061. **Requirements:** FR-026..040; regulatory taxonomy/playbook configuration interface in FR-064. No live regulatory authority connector is claimed by manual import.

### Ordered tasks

1. Agree version/span/permission contracts with Part 1; build independent deterministic fixtures/rules while D/E integration is pending.
2. Approved source registry: authority/trust state, jurisdiction, fixture/public provenance, named approval and manual import. Separate public acquisition from confidential user/model context.
3. Regulatory document/version records with publication/effective half-open periods, imported/check times, amendments/supersession and immutable source hashes. Unknown dates stay unknown/needs verification.
4. Exact/structural differences plus grounded semantic change proposals; authorized human applicability/materiality decisions. Keep old versions and historical as-of behavior.
5. Separate Requirement/Policy/Control/Evidence/Assessment/Finding identities/revisions and tenant-qualified mappings; never reuse industrial environmental scores as legal compliance results.
6. Deterministic evaluations and grounded provisional interpretation with all six states, evidence sufficiency and explicit reasons. Missing evidence is not satisfaction or automatically a proved violation.
7. Expiry/replacement/source/control drift invalidates current projections and adds reasons/re-evaluation work; historical assessments remain unchanged.
8. Relational change blast radius and explainable component status; no invented opaque AI risk weights. Feed accepted changes/findings/evidence requests into Part 3's durable events/workflow contract.

**Owned paths:** new regulatory/compliance model/schema/service/route modules, deterministic fixtures and tests. Coordinate shared source and proposal schemas; do not copy Part 1's extraction/storage code or Part 3's scheduler/review ledger.

**Required checks:** authority/effectivity/version selection, unknown/amended dates, exact diff, freshness failure, human applicability, forbidden cross-workspace mappings, six-state reasons, absent/stale/conflicting evidence, historical preservation and blast radius. Demonstrate regulation version change and evidence expiry -> explainable pending finding/re-evaluation.

**Handoff to Part 3:** revision-bound finding/evaluation proposals, accepted applicability decisions, obligation/requirement references and source/evidence change events with workspace/actor/idempotency keys. No model may accept state or assign binding review authority.

## Part 3 — durable workflows, review, security and acceptance

**Owner:** Team member 3. **Phases:** I/J plus consolidated L/M. **Requirements:** FR-041..047, FR-054..063 (regulatory acquisition belongs to Part 2), administration/configuration integration for FR-064..066. Coordinate FR-019 accepted obligation promotion with Part 1. Every teammate owns security tests for their own feature; Part 3 owns cross-team assurance.

### Ordered tasks

1. Define durable workflow/event/idempotency contracts with Parts 1/2 and reuse current revision/approval/audit/checkpoint patterns. Before their APIs exist, implement restart/clock/failure checks against labelled synthetic input.
2. Exact-revision independent legal/compliance approve/reject/request-changes/escalation; preserve existing reviewer eligibility and add scoped grants/assignment. No self-approval, silent revision edits or model-controlled acceptance.
3. Accepted obligations with duty/owner/source/trigger/conditions, approved timezone/date/calendar/recurrence, durable occurrences/outbox/receipts and in-app notifications. Ambiguous dates stay reviewable; external delivery remains unconfigured until an adapter is accepted.
4. Tasks/dependencies/evidence requests/remediation submission/closure/retest/reopening; expiry-bound exceptions/risk acceptance and bulk triage remain explicit Should requirements, not silently dropped.
5. Expanded legal audit vocabulary/context, exact source/evidence/analysis/model/prompt/rule/decision binding, append-only comments/decisions, scoped snapshot/replay/basic exports. Preserve old hash envelopes and deny legacy audit/review back doors to legal content.
6. Governed service identities/API scopes, signed webhook/replay boundaries, connector retries/dead letters and admin configuration contracts. Coordinate real adapters with Part 2; do not claim unconfigured integrations work.
7. L: cross-role/tenant tests across resources/retrieval/export/audit/workers, revoked-membership resume/release denial, prompt injection/tool misuse/source poisoning, log/checkpoint privacy, dependency/security review and legal golden evaluations. Live inference still needs separate permission.
8. M: integrated synthetic/public backend journeys, migration/current-to-head preservation, worker/timer kill/restart/retry, backup/restore/reindex/config/key recovery rehearsal, measured approved performance/recovery targets and complete FR/evidence reconciliation.
9. Prepare final acceptance report with unfinished items, deployment/SSO/MFA/legal-pack/retention gates and frontend-owner checks visible. User-owned frontend does not waive its final end-to-end/usability acceptance.

**Owned paths:** workflow/review/obligation/task/notification/audit services/models/routes/tests and cross-team acceptance/recovery scripts/docs. Shared CI edits require integrator review. Preserve frozen industrial corpus; report its existing mismatch separately.

**Required checks:** real session/terms gates, independent reviewers, concurrent revoke/approve/release, exact revision/hash binding, no lost/duplicate timers across crashes, stale-source promotion denial, closure/retest enforcement, tenant-safe audit/export, restore hash parity and full three-pillar acceptance. No binding promotion before Parts 1/2's relevant gates pass.

## Shared-file and migration coordination

| Shared concern | Owner / rule |
|---|---|
| `app/api/router.py`, `app/db/models/__init__.py`, `main.py`, central auth/policy | Integrator reviews each additive change; teams propose small separate PRs |
| Source/span/AI proposal contracts | Part 1 authors; Parts 2/3 acknowledge before consumers land |
| Findings/event/review binding | Part 2 proposals + Part 3 authority; Part 1 integrates contract findings |
| Migration chain | Current head `0020_legal_policy_audit`. Part 1 proposes 0021, Part 2 0022, Part 3 0023, **only after predecessor schema is agreed/merged**. Later revisions are allocated centrally; never create competing heads or use a speculative missing predecessor |
| Early parallel model/rule development | Allowed with synthetic fixtures; dependent migrations/persistent APIs wait for actual predecessor. No fake phase completion |
| Living guide/progress/validation/FR registry | Teams update affected sections in PRs; integrator resolves overlap and preserves actual evidence |
| Docker/runtime/dependency configuration | Dedicated disposable targets only; no private resource probing; additions bounded and pinned |

## Review and merge procedure

1. Teammate pushes their branch and opens a PR to `feat/legal-regulatory-platform-migration` with this handoff's evidence.
2. `Legal backend checks / legal-core` runs the current scope/API/migration regression on GitHub-hosted disposable resources. It is a **baseline check**, not acceptance for future features. Each team adds its actual unit/integration/security/fixture checks; AI accuracy is not inferred from scope tests.
3. The integrator reviews **all commits and the full base-to-head diff**, changed callers, schema/FKs/ACLs, source/evidence/review/state boundaries, tests, provenance, secrets and the FR map. Green CI alone does not authorize merge.
4. Reproduce failures, patch on the contributor branch only with explicit edit permission or on a separate integrator fix branch, rerun affected checks, and document fixes. No force pushes or rewritten contributor history.
5. Merge reviewed PRs to the development base in dependency order. Revalidate combined migrations and cross-team contracts after each relevant integration.
6. `main` promotion requires the approved unrelated-history reconciliation, applicable complete acceptance evidence, the full validation report and owner authorization. Use a normal PR/merge that preserves existing `main` history; never overwrite it to resolve conflicts.

## Completion tracking

All 66 FRs remain in `LEGAL_REQUIREMENT_TRACEABILITY.md`; these assignments specify ownership rather than completion. Parts 1/2/3 own all backend phases and extended/pilot requirements. The owner owns frontend/K and frontend acceptance. The integrator owns reconciliation/review/publication and reports skipped/pending checks explicitly. No half-hour deadline overrides a requirement or verification gate.
