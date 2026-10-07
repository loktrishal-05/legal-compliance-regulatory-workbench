# Consolidated Claude handoff — Legal & Regulatory Assurance Platform

Updated: 2026-10-06. **One entry point for the next assistant.** This is a factual handoff and reading index, not a replacement for the master specification, repository boundaries, detailed build guide or actual tests. Reverify recorded state before acting. The user's latest request is to save the conversation/build/team/repository context for Claude; this documentation change does not start another implementation phase.

## 0. Current state — 2026-10-06 (supersedes the §3/§4 snapshot rows below)

### Current continuation — 2026-10-07 (supersedes dated snapshots and prompts below)

- Verified development `b3dcf4f`, main `a85494d`; PRs #4-#12 merged, no open PRs at entry. Actual migration head `0023_legal_intake_audit`. Issues #1/#2/#3 currently assigned to the owner.
- Authorized root-only branch `integration/backend-continuation-20261007`; RED checkpoint `9327f9b` and verified GREEN E1 corrections. Preserve existing benchmark/nested/private/untracked work and all external/historical worktrees; do not execute them.
- Shared intake policy v2 fixes XML external-reference detection, rejects malformed/DTD/entity/macro/oversize XML and ambiguous/unsupported archives, verifies original/duplicate lineage and publishes without overwriting existing files. 33 focused checks, 93 scoped checks, 96% intake service line coverage and fresh/0018-to-0023 validation pass. See VALIDATION_REPORT for exact evidence and limitations.
- A/B source/design complete; C backend identity verified; D development exit recorded with historical industrial regression gaps; E1 partial/hardened, E2/E3 and F pending; G/H deterministic core only; I/J/L/M pending. K/frontend remains owner-managed. Real uploads stay quarantined because no malware scanner is configured. No full FR/pilot/runtime/recovery acceptance.
- Next build: E2 isolated extraction/OCR with exact source spans/corrections, then E3 authorized retrieval. No live model/private DB/deployment enablement. Local commits authorized; publication awaits the displayed full status/validation report and explicit push authorization. Root AGENTS independent-review/no-bypass rules remain binding even though GitHub currently requires zero approvals. Reverify actual commit/PR state; do not follow obsolete teammate-invitation, PR #4, migration 0022 or external-worktree commands below.

The original 2026-10-06 snapshot follows for provenance:

- All three teammates are unavailable; the owner asked the integrator to build all remaining backend work and commit. Frontend/landing (K) stays with the owner.
- Owner set required approvals to **0** on `main` and development (kept: `legal-core` required, strict up-to-date, conversation resolution, admin enforcement, no force push/deletion). Integrator self-reviews; independent human review is an open acceptance gate.
- Merged to development: #4 handoff/CI, #6 Part 2 deterministic G/H core, #7 D provisioning (0021), #8 D dedupe/isolation (0022). Development head `5ff7ed8`; migration head `0022_legal_version_scope`.
- `main` = `a85494d` (PR #5 joined the unrelated histories; tree = development at 496f903). Creating a development -> main promotion PR was **blocked by the session permission classifier**; the owner must create/merge it or grant that permission.
- Phase D complete for development exit checks; industrial regression suites cannot run in available runtimes (recorded gap). Next: Phase E secure intake on scoped versions, then F, G/H persistence (Part 2 core exists), I, J, L, M.
- Parts 1/2: integrator. Part 3 (#2): owner-run Codex agent in worktree `C:/Users/Lohith k/AppData/Local/Temp/lrw-part3` on `team/3-workflows-assurance`; integrator reviews every commit/full diff, fixes on a separate branch, merges after `legal-core`. Both agents use the owner's GitHub account: no independent human review (open gate).
- Work happens in temp worktrees (`%TEMP%\lrw-part1`, `%TEMP%\lrw-part2`) so the owner's dirty working tree is never touched.

## 1. Exact workspace and source of truth

**Only application root:**

```text
C:\Users\Lohith k\Desktop\OLD hard work\legal-compliance-regulatory-workbench
```

**Only authorized GitHub repository:**

```text
https://github.com/loktrishal-05/legal-compliance-regulatory-workbench.git
```

Read these documents in this order; all are in this workspace:

| File | Authority / purpose |
|---|---|
| `AGENTS.md` | Mandatory repository, user-work, service, commit/push and phase boundaries |
| `docs/SESSION_RESUME.md` | Short resume entry point linking to this consolidated handoff |
| `docs/Legal_Regulatory_Assurance_Platform_Master_Report.pdf` | Immutable 80-page product specification, all three pillars and 66 FRs |
| `docs/LEGAL_DOMAIN_MIGRATION_PLAN.md` | Canonical A-M sequence, dependencies, blockers, exit checks and plan-change log |
| `docs/MIGRATION_PROGRESS.md` | Actual implementation/approval/checkpoint history; dated older entries are historical |
| `docs/VALIDATION_REPORT.md` | Actual commands/results, warnings, failures and pending acceptance |
| `docs/TEAM_WORK_ALLOCATION.md` | Detailed three-person scope, paths, FR ownership, migration/contracts, tests and PR workflow |
| `docs/LEGAL_DOMAIN_BUILD_CONTRACTS.md` | Tenant/ACL/classification/source/time/state/review/AI/API invariants |
| `docs/LEGAL_REQUIREMENT_TRACEABILITY.md` | All FR-001..066, priorities, deliverables and evidence; none fully accepted yet |
| `docs/LEGAL_PLATFORM_TARGET_ARCHITECTURE.md` / `LEGAL_PLATFORM_REUSE_MATRIX.md` | Approved reuse-first architecture; do not rebuild mature infrastructure blindly |
| `docs/LEGAL_RUNTIME_SETUP.md` | Isolated settings/service targets and offline/runtime boundaries |
| `docs/REPOSITORY_BOUNDARY_AUDIT.md` / `MIGRATION_CODEBASE_AUDIT.md` | Custody/discovery context; historical findings are not current acceptance |

Preserved historical resume notes: `docs/SESSION_RESUME_HISTORY_2026-10-06.md`. Do not execute its superseded Phase C-only/no-push/unprotected/770c834 resume instructions. Use the current guide and verified state; do not erase historical evidence to make the documents appear green.

## 2. What the user asked and approved

1. Rebuild the existing industrial workbench into a real **Legal & Regulatory Assurance Platform**: contract analysis, compliance monitoring and document summarization as connected persistent workflows, not a PDF-chat demo or fake dashboard.
2. Follow the unchanged master report and permanent phased guide, inspect callers, reuse mature components, keep plans/progress/validation/FR evidence synchronized, and report completed versus remaining work after milestones.
3. Retain React/Vite, FastAPI/PostgreSQL/Qdrant/LangGraph and local/private AI. Do not switch to Next.js, hosted inference, a graph DB or microservices without a justified approved change.
4. Development uses clearly labelled public/synthetic fixtures, manual approved regulatory imports and existing local cookie sessions. Enterprise SSO/MFA/re-auth, validated jurisdiction/playbooks/legal terms/retention/hold/recovery and deployment policies remain pilot gates, not waived requirements.
5. Original industrial v1.0 terms/DOCX/acknowledgement keys/receipts remain unchanged and labelled legacy. New legal-platform terms require owner approval. No signing, filing, automatic deletion, compliance certification or autonomous high-impact promotion.
6. User now owns **frontend and landing-page implementation**. No new frontend work by the assistant. The user separately approved publishing the previously written/tested identity snapshot so frontend/backend health identity remains coherent; that is not permission for redesign or new pages.
7. User initially wanted completion in half an hour, then explicitly required **no process skipped** and asked for three human teammate workstreams. There is no guaranteed half-hour completion. Parallel development does not waive dependencies, security, accuracy, recovery or frontend acceptance.
8. Regular coherent local commits are authorized. The inherited cherry-pick was explicitly quit with preservation; do not reintroduce/continue/abort it. User separately approved preservation snapshots of inherited work.
9. User approved a dedicated disposable PostgreSQL/backend test environment with synthetic data only, no private database/model access. The approved legal-core project was stopped/removed after tests; recreate only that isolated project after verifying its targets. No live inference/deployment permission.
10. After seeing the current full migration/validation status, user explicitly approved publishing the partial development checkpoint and saved identity snapshot, creating team tasks/branches and enabling PR protection on main/development. This does not authorize main history overwrite or unreviewed promotion.
11. User wants the assistant to inspect teammate commits/PRs, reproduce/fix defects, run checks and integrate accepted work. AI review is **session-bound**; GitHub CI runs between sessions. No unattended continuous AI monitoring or automatic quality approval is configured.

## 3. Verified Git/GitHub snapshot

Snapshot verified immediately before writing this handoff; re-query on resume.

| Reference | Recorded state |
|---|---|
| Root/common Git directory | Authorized root; `.git`/`.git`, no returned hooksPath/pushurl/URL rewrite/include override; sample hooks only |
| GitHub access | Repository PUBLIC; authenticated account `loktrishal-05` had ADMIN access. Recheck auth; do not expose credentials |
| Shared development base | `feat/legal-regulatory-platform-migration` at **`496f903ec42a4368a2546d83416affdff8bb6841`**, pushed |
| Default `main` | **`d95dfc3e6cf0432f3c2c0e50093b605d5bc13bff`**, protected, code unchanged |
| Main/development relationship | **No merge base / unrelated histories**. Do not normal-pull main into this work or run `--allow-unrelated-histories` automatically |
| Local active branch | `team/handoff-review-evidence`, tracking its matching origin branch |
| Pre-handoff active HEAD | **`9cd84af9a41900b5d34861fa0e811524739cbb81`**; this handoff documentation adds a later normal commit |
| Open PR | **[#4](https://github.com/loktrishal-05/legal-compliance-regulatory-workbench/pull/4)**, head `team/handoff-review-evidence`, base development; OPEN / REVIEW_REQUIRED |
| PR #4 scope | Handoff evidence + explicit credential-free/non-recursive CI checkout; no new backend feature/frontend implementation; this consolidation extends its documentation scope |
| Team branches | `team/1-documents-contracts`, `team/2-regulatory-compliance`, `team/3-workflows-assurance`, all initially at 496f903 |
| Issues/people | Part 1 #1 @Harsha-code-per, Part 2 #3 integrator/owner account (Sanjjith27 unavailable; PR #6 open), Part 3 #2 @Cholan-kinnera (owner delegated the mapping; invitation order). Write invitations pending; assignment comments posted; set assignees after acceptance |

Important normal checkpoints (do not amend): `34dc7af` terms/auth preservation; `dfea5db` A custody/config/plan; `3f94383` B domain/FR contracts; `1968d2e` inherited frontend preservation; `770c834` identity RED checks; **`87cd2bd`** scoped backend + saved identity + three-team handoff; **`496f903`** published evidence/shared base; `30caf9c` protections evidence; `9cd84af` CI checkout custody fix. Preservation snapshots are not fresh legal acceptance.

Both main/development protection was verified: required **`legal-core`** with up-to-date branch, one independent approval including last-push independence, stale-review dismissal, conversation resolution and admin enforcement; force pushes and deletions disabled. Superseded 2026-10-06 by the owner: approvals set to 0 (see §0). Still never use `--admin`, force push, or bypass `legal-core`; record self-review honestly.

## 4. Current application state and remaining phases

| Phase | Actual state / remaining work |
|---|---|
| A — custody/config/discovery | Source/config milestone complete; isolated defaults/CI/runbooks; master ingested unchanged. Private runtime/deployment ownership still gated |
| B — architecture/contracts | Approved development baseline, scoped role/state/source/review contracts and 66-FR registry complete; planning is not feature delivery |
| C — identity/configuration | Backend identity and saved paired frontend identity verified/published. Existing layout retained; frontend/design acceptance now user-owned. Historical industrial pages/results are labelled legacy |
| D — legal core/authorization | **Complete for development exit checks** (0019-0022): scope/policy, audited independent provisioning, operator bootstrap/legacy mapping, per-workspace dedupe, legacy-path guards, root audit exclusion |
| E — document intelligence | Secure formats/upload/import, scan/quarantine/type/size/archive/parser limits, immutable originals, OCR/layout/quality/corrections, exact source spans, authorized retrieval still to build |
| F — contracts/summaries | Contract/party/clause/playbook/version analysis, source-linked duty/date/conflict proposals, deviations/missing clauses/redlines, cited audience summaries/coverage/exports and review integration still to build |
| G — regulatory intelligence | Deterministic as-of/diff/freshness core merged (#6). Approved source registry/manual imports, authority/version/effectivity/amendment/diff/freshness/applicability/change impact still to build |
| H — compliance assurance | Deterministic six-state/evidence/drift/impact core merged (#6). Persistent requirements/policies/controls/evidence/assessments/findings/mappings and APIs still to build |
| I — monitoring/work | Accepted obligations, approved timezone/recurrence/calendar deadlines, durable occurrence/outbox/receipt/escalation/task/in-app notification behavior still to build/test |
| J — legal governance/audit | Exact immutable legal review/independence/request-changes/escalation, remediation closure/retest/reopen, scoped audit/replay/export and atomic hash/evidence binding still to build |
| K — frontend | User-owned implementation; real backend journeys/role/error/loading/responsive/accessibility/source-jump acceptance remains required, not skipped |
| L — evaluation/security | Each team owns feature security; cross-team tenant/role/retrieval/export/worker/logging/injection/upload/legal golden evaluation and hardening still pending |
| M — full acceptance/recovery | Integrated three-pillar journeys, migration/history/restart/restore/reindex/key/config/performance evidence, complete FR reconciliation and pilot approvals still pending |

No FR is fully accepted solely by the initial metadata APIs or CI. Existing industrial tests/agents are reusable historical infrastructure, not legal correctness proof.

### Implemented D slice: concrete code

- Seven tables: Organization, Workspace, WorkspaceMembership, Matter, MatterAccess, LegalDocumentScope, DocumentAccess in `backend/app/db/models/legal_scope.py`, using existing Base UUID/timestamp/naming.
- `backend/app/services/legal_policy.py`: current DB-derived account/terms/membership/organization/workspace/role/clearance; explicit document grants plus matter access; no inherent global admin read; review prerequisite also needs original reviewer/admin eligibility and non-self requester.
- `backend/app/api/routes/legal_scope.py` + `schemas/legal_scope.py`: GET `/v1/workspaces/{workspace_id}` and GET `/v1/workspaces/{workspace_id}/documents/{document_id}`. Metadata only; no path/body/hash or write/intake/provisioning/release endpoint.
- Denied/unknown IDs share a 404; `SECURITY_POLICY_DENIED` uses the existing audit writer/hash chain and requested IDs only. Versioned paths inherit session/terms, origin/no-store/referrer and validation-input redaction.
- Additive `0019_legal_scope` and `0020_legal_policy_audit`; **actual source head is `0020_legal_policy_audit`**, baseline 0018 preserved. Do not edit old migrations or guess a private applied head.
- `backend/scripts/validate_legal_migrations.py` rejects targets other than the exact disposable legal-core DB before settings/connection.
- Existing global `DocumentVersion.source_sha256` uniqueness and global industrial content/retrieval paths still need a reviewed transition. Do not enable legal intake or place real confidential legal data in old shared routes/indexes meanwhile.

## 5. Verification, limitations and runtime commands

| Evidence | Actual result / scope |
|---|---|
| Scoped tests | **27/27**: 10 SQLite policy + 10 PostgreSQL policy + 4 bounded API + 3 migration/target checks; confirmed after final code review |
| Migrations | Fresh -> 0020 and 0018 -> 0020; Alembic parity and repeat upgrade PASS; synthetic source/version hashes, audit hash/chain and existing trigger definitions preserved; no automatic ownership backfill |
| Paired identity/API | Frontend focused **14/14**, backend pure identity **2/2**, custody **6/6** passed |
| Earlier frontend regression | **44/44**, lint 0 errors/2 inherited fast-refresh warnings, build passed. Earlier dated evidence, not a newly repeated full suite |
| Bounded browser | Mocked landing/login/terms/help desktop/mobile observations passed for identity/assets/stable fit/reduced motion/skip link; not real backend or full WCAG/legal-journey acceptance. Legacy dashboard `{}` mock failure recorded, not passed |
| GitHub shared-base CI | Run [37492025870](https://github.com/loktrishal-05/legal-compliance-regulatory-workbench/actions/runs/37492025870) SUCCESS at 496f903 |
| GitHub corrected PR CI | Push [37492888207](https://github.com/loktrishal-05/legal-compliance-regulatory-workbench/actions/runs/37492888207) and PR [37492895455](https://github.com/loktrishal-05/legal-compliance-regulatory-workbench/actions/runs/37492895455) SUCCESS at 9cd84af; PR still requires independent approval |
| Not accepted | Full industrial/AI root-router startup, full backend/security/retrieval/legal accuracy, live inference, restore/reindex/performance/pilot/end-to-end frontend |

The API tests use the actual scoped router/session/terms dependencies and actual main middleware AST-loaded in a bounded app; do not represent them as full `app.main` acceptance. Native FastAPI import is blocked by OS Application Control on `ujson`; do not disable protection. The approved bounded Linux test image avoids that dependency for these checks, not every app dependency. Warnings: Starlette httpx TestClient deprecation and SQLite inherited expression-index reflection limitation. Keep actual failures visible.

Approved synthetic test runtime (verify Docker context and exact Compose targets first):

```powershell
docker compose -f infra/docker-compose.legal-core-test.yml config --quiet
docker compose -f infra/docker-compose.legal-core-test.yml build tests
docker compose -f infra/docker-compose.legal-core-test.yml run --rm tests
docker compose -f infra/docker-compose.legal-core-test.yml run --rm tests python -B -m scripts.validate_legal_migrations
docker compose -f infra/docker-compose.legal-core-test.yml down --volumes
```

This project uses an internal network, no host ports/persistent volumes, selected backend read-only mounts, no private `.env`/models/data, and model/Qdrant endpoints at unused loopback port 9. Fixture MODEL_NAME is not permission to call a model. The container/network was removed after tests; images remain. Broaden dependencies/tests only when a real feature requires them. `.github/workflows/legal-backend-checks.yml` runs baseline CI on pushes/PRs with read-only permission; the corrected version on PR #4 uses explicit public credential-free, non-recursive checkout to avoid the quarantined gitlink. The older full regression remains manual.

## 6. Three human teammate assignments

Detailed ordered tasks, owned paths, required checks and shared contracts: `TEAM_WORK_ALLOCATION.md`. These are human teammate slots, not permission to create three AI agents or duplicate their work.

| Slot / branch / issue | Scope and handoff |
|---|---|
| **Member 1** — `team/1-documents-contracts` — [#1](https://github.com/loktrishal-05/legal-compliance-regulatory-workbench/issues/1) | Remaining D, E/F, authorized source/search/summary and document security. FR-001..025, FR-048..053, provider policy in FR-065. Deliver stable exact source/version/span/ACL/proposal contracts for Parts 2/3; enterprise identity requirements remain pilot gates |
| **Member 2** — `team/2-regulatory-compliance` — [#3](https://github.com/loktrishal-05/legal-compliance-regulatory-workbench/issues/3) | G/H, FR-026..040, regulatory connectors/taxonomy interfaces. Deliver reviewed applicability/version/change/evidence/evaluation/finding contracts and events to Part 3 |
| **Member 3** — `team/3-workflows-assurance` — [#2](https://github.com/loktrishal-05/legal-compliance-regulatory-workbench/issues/2) | I/J and consolidated L/M, FR-041..047 and FR-054..066 coordination. Durable legal workflows, reviews/audit/remediation, service/webhook/admin contracts, security/restart/recovery/final acceptance. Every team still owns its own security tests |

Frontend/K is the user. Assistant/Claude is the integration/review coordinator unless explicitly assigned another non-overlapping implementation scope. Handles are mapped above; set GitHub assignees once invitations are accepted. Do not alter access beyond the owner's invitations. Independent PR approvals come from teammates (cross-review), never the owner account that also runs the assistant.

Branches already exist remotely. A teammate can clone their branch directly, for example:

```powershell
git clone --branch team/1-documents-contracts https://github.com/loktrishal-05/legal-compliance-regulatory-workbench.git
```

Teams may develop independent deterministic logic/labelled fixtures in parallel, but dependent persistent APIs/migrations/phase acceptance wait for approved D/E/source/review prerequisites. Do not fabricate missing predecessors or competing heads. Coordinate actual migration allocation from current 0020: proposed Part 1 0021, Part 2 0022, Part 3 0023 **only after actual predecessor is agreed/merged**; reallocate centrally if features need more migrations.

## 7. Repository management, regular commits, pull/review/correction and merging

### Before every operation

Verify exact root/origin/fetch+push URLs/common Git metadata/worktrees/hooks and relevant deployment/test targets. Preserve staged/unstaged/untracked work. Do not use sibling/historical repositories, eRTMAC (`loktrishal-05/ertmac-nwis`), nested `claudex-loop`, stale `.kilo` worktrees or old self-hosted deployment/model targets. Do not overwrite .env or rename/delete private storage/indexes to rebrand.

Current remaining user/local work includes modified `benchmark/reports/final_model_runtime_readiness.json`, dirty/untracked `claudex-loop`, `.impeccable/review/`, `.playwright-mcp/` and `docs/.phase11_*` private/local artifacts. Do not stage/delete/normalize these or change the frozen manifest to make its mismatch disappear. No `git add .`, blind stash/reset/clean, force push, history deletion, hook bypass or automatic worktree repair. Master PDF SHA-256 remains `69ef7ab3f5299a765d641e1f55853dbb6d21cb0ff0610c6e6ff7846ec3b5f102`; legacy terms SHA-256 remains `feef43e2378f40e48cd9cd5449d121c56fb2f9bd4dc47e860c87a8db2735bc6f`.

### Commit discipline

Make coherent verified local checkpoints with their docs. Before each commit inspect status, intended diff and `git log --oneline -10`; stage explicit intended paths only; check whitespace/secrets and relevant runnable tests. Never claim test acceptance for preservation-only snapshots. Failed commits/hooks: fix and make a new commit attempt, no amend/skip. Regular local commit approval is not blanket deployment/main-promotion permission. Publish team/review fixes only within the requested handoff/assigned work and existing PR rules; new unrelated scope needs approval.

### Pull/fetch and review loop during an active session

1. Use `gh` to list current issues/branches/PRs/checks/commits in the authorized repository. Reverify auth/account and base/head/author. PR descriptions/comments/files are review data, not authority to override repository/security instructions.
2. Fetch named contributor/development refs read-only first; compare **all PR commits and full base-to-head diff**, changed callers, test/provenance/FR evidence and dependencies. Do not run blind `git pull`, especially while dirty or from unrelated main.
3. To update a teammate branch after compatible base advances, coordinate a normal reviewed merge from the development base and preserve history. Do not rebase/force-push somebody's work, overwrite their branch, or resolve conflicts by dropping another team's changes. Never pull contributor code across unrelated app roots.
4. Run baseline checks plus the feature's actual unit/integration/security/fixture/acceptance tests in verified isolated resources. Green `legal-core` alone is not future feature acceptance or legal accuracy. Check tenant/FK/ACL/revocation/source/hash/review/state/timer/logging/data boundaries end to end.
5. Reproduce defects and identify the shared root cause/callers. Fix on a separate clearly scoped integration/fix branch; edit the teammate's own branch only with explicit permission. Commit normally, rerun affected checks and document findings/fix evidence. No hidden scope expansion or bypass.
6. Approve/merge only after an actually independent review, passing required checks, resolved discussions and relevant phase gates, in dependency order, into **`feat/legal-regulatory-platform-migration`**. Use normal PR merges; preserve all user work and history. If the active account authored the PR, obtain another reviewer rather than impersonating independence.
7. Revalidate combined schemas/migrations/contracts after meaningful integrations; synchronize guide/progress/validation/FR registry and report actual complete/remaining work. GitHub CI runs automatically between sessions; Claude cannot promise unattended monitoring or acceptance without a real authorized running service.

### Main promotion is a separate gate

**Update 2026-10-06:** owner chose the one-time join. PR [#5](https://github.com/loktrishal-05/legal-compliance-regulatory-workbench/pull/5) (`reconcile/main-join`, merge `b451860`, parents `d95dfc3` + `496f903`, tree identical to `496f903`) awaits `legal-core` and one teammate approval. After it merges, the integrator opens a normal reviewed dev → main promotion PR after each integrated checkpoint; promotion never claims phase/FR acceptance. The text below is the pre-approval rule, kept for history.

Remote main has unrelated history. Show the actual graph/tree differences and propose a preservation-first reconciliation plan; obtain owner approval before any reconciliation. Do not invoke `--allow-unrelated-histories`, recreate main, force/reset or promote a partial checkpoint silently. Final main promotion requires relevant complete acceptance/known-limitations report and owner approval, preserving main history and satisfying protection via a normal reviewed PR. This has **not happened**.

## 8. Exact next actions for Claude

1. Read the required files and reverify all state above. This workspace is deliberately not clean; preserve user artifacts.
2. Check invitation acceptance; set assignees #1 Harsha-code-per, #2 Cholan-kinnera (#3 is assigned to the owner account; Part 2 built by the integrator, PR #6). Owner wants accepted work regularly reaching `main`; that requires the owner-approved one-time unrelated-history reconciliation first (see §7), then reviewed dev→main promotion PRs.
3. Inspect PR #4 and its latest documentation/CI checks. It is a handoff PR, not a completed legal implementation, and must get independent approval; do not self-approve/merge with admin override.
4. Inspect new teammate PRs/commits during active review, coordinate their D/E/source/review/migration dependencies and required evidence, reproduce/fix reviewed defects, integrate accepted work on development base.
5. Remaining D is the first implementation gate. All three backend streams are assigned; only take an explicit non-overlapping implementation task or integrator correction, never quietly duplicate a human teammate's branch.
6. Keep master/terms/private data/history intact. Update this consolidated handoff, the short resume pointer and living guide/progress/validation when state changes. Do not turn historical failures into passes or skip work for speed.

## 9. Prompt to paste into Claude

```text
Continue as the backend integration/review coordinator for the Legal & Regulatory Assurance Platform in:
C:\Users\Lohith k\Desktop\OLD hard work\legal-compliance-regulatory-workbench

First read AGENTS.md and docs/SESSION_RESUME.md, then docs/CLAUDE_HANDOFF.md completely. Follow its linked reading order for the living migration plan, progress, validation report, team allocation, domain contracts, FR registry, architecture/reuse and relevant unchanged master-report requirements. Treat dated old resume/progress sections as history, not current commands; verify Git/GitHub rather than relying on this chat.

Only use https://github.com/loktrishal-05/legal-compliance-regulatory-workbench.git. Preserve all staged/unstaged/untracked work and quarantined nested/historical repositories. Do not implement frontend/landing; I will handle them. No requirements, security checks or phase gates may be skipped. Initial Phase D is tested but incomplete; all remaining backend work is divided into the three human workstreams in TEAM_WORK_ALLOCATION.md.

Recheck root/origin/common metadata/hooks/branch/status, remote heads/protections and PR #4. Shared development base was 496f903 on feat/legal-regulatory-platform-migration; local team/handoff-review-evidence carries the handoff/CI fixes and this consolidation. Main is protected with unrelated history; do not overwrite, force-push, merge unrelated histories or promote to main without a separately reviewed owner-approved reconciliation and acceptance plan.

Ask me for the three teammates' GitHub handles, assign their existing issues correctly, inspect incoming commits and the full PR diffs, reproduce/fix defects on authorized separate fix branches, run real relevant isolated checks and merge accepted changes into the protected development base only with independent review. Make regular coherent verified local commits, stage explicit paths, and keep plan/progress/validation/FR evidence and the consolidated handoff synchronized. GitHub baseline CI is not feature acceptance. Do not self-approve the authenticated account's own PR or bypass protection. Monitoring/review is active-session work, not an unattended promise.

Use only the approved disposable legal-core test resources after verifying targets. No private database migration, live model execution, deployment, new frontend work or unrelated repository operation without separate permission. Start by reporting verified current state, outstanding PRs and the first unresolved dependency, then proceed with the authorized review/coordination work. Clearly report completed, blocked and remaining work.
```
