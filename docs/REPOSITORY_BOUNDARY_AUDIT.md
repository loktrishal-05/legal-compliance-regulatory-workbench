# Repository boundary audit

Date: 2026-10-06. Discovery baseline below is preserved; Phase A source custody/configuration remediation is recorded at the end. Private runtime ownership/provisioning is **not yet accepted**.

## Verified custody

| Item | Observed value |
|---|---|
| Only application root | `C:\Users\Lohith k\Desktop\OLD hard work\legal-compliance-regulatory-workbench` |
| Active branch | `master` |
| HEAD | `831c14909afc4ed1d2b778359df07f9e6b21b5cc` |
| Origin, fetch and push | `https://github.com/loktrishal-05/legal-compliance-regulatory-workbench.git` |
| Origin safety | Exact authorized URL; no correction needed |
| Root `.git` | Directory; `--git-dir` and `--git-common-dir` both `.git` |
| Git operation | Unfinished cherry-pick of `11fdd1c`; no unmerged paths |
| Cached tracking state | `master` is 43 commits behind cached `origin/master`; not fetched/pulled/merged |
| Migration branch | Created `feat/legal-regulatory-platform-migration` at the same HEAD; **not checked out** because the cherry-pick remains active |
| Index SHA-256 before planning edits | `522ae5affb5c58cea5347da7746752a5740100c2ad5624bf7b3ca2c29eb7761f` |

Commands inspected: `git rev-parse --show-toplevel`, `git status`, `git branch --show-current`, `git rev-parse HEAD`, `git remote -v`, `git remote get-url origin`, `git worktree list`, `git config --show-origin --get-regexp "^remote\..*\.url$"`, common-dir resolution, remote/pushurl/URL rewrite/include/hooksPath configuration query, staged/unstaged diff summaries, unmerged paths, and porcelain status. No additional configured pushurl/rewrite/include/hooksPath was returned. Root hooks contain only the fourteen Git sample hooks; these are not active hooks.

This is a state record and branch reference, **not a full backup of uncommitted files**. No backup/archive, stash, commit, history deletion, reset, cherry-pick continuation/abort, worktree repair/prune, deployment or push was performed.

## Existing user work preserved

Seventeen staged paths:

```text
.env.example
backend/alembic/versions/0018_terms_acceptance.py
backend/app/api/deps.py
backend/app/api/routes/auth.py
backend/app/core/config.py
backend/app/db/models/audit_event.py
backend/app/db/models/user.py
backend/app/schemas/auth.py
backend/app/services/terms.py
backend/tests/test_phase5b.py
backend/tests/test_phase5c.py
backend/tests/test_phase5d.py
backend/tests/test_phase5f_security.py
backend/tests/test_phase_f_auth.py
backend/tests/test_phase_f_postgres.py
backend/tests/test_terms_acceptance.py
docs/terms_acceptance.md
```

Nineteen unstaged status entries (including nested gitlink content):

```text
README.md
benchmark/reports/final_model_runtime_readiness.json
claudex-loop
frontend/src/WorkspacePages.jsx
frontend/src/app/AppPages.jsx
frontend/src/app/AppShell.jsx
frontend/src/app/navigation.js
frontend/src/app/routes.jsx
frontend/src/components/ui.jsx
frontend/src/features/approvals/ReviewDesk.jsx
frontend/src/features/dashboard/DashboardView.jsx
frontend/src/features/insights/insightsModel.js
frontend/src/features/insights/insightsModel.test.js
frontend/src/features/maintenance/MaintenanceView.jsx
frontend/src/hooks/useApi.js
frontend/src/services/api.js
frontend/src/services/api.test.js
frontend/src/styles/base.css
frontend/src/styles/workbench.css
```

Pre-existing untracked files/directories: `.gitattributes`, `.impeccable/review/`, `AGENTS.md`, `PROJECT_HANDOFF.md`, `SOURCE_AUDIT.md`, `docs/.phase11_advisory_details.json`, `docs/.phase11_baseline.json`, `docs/.phase11_npm_audit.json`, `docs/.phase11_python_advisories.json`, `docs/.phase11_python_advisories_after.json`, `docs/.phase11_secret_scan.json`, `docs/.phase11_secret_scan_revalidated.json`, `docs/.phase11_test_runtime/`, `docs/help_resources.md`, `frontend/public/resources/`, and `frontend/src/features/{executions,knowledge,pid,resources}/`. The copied PDF and migration documents are new discovery outputs, not part of that original baseline.

## Registered worktrees (observed; no repair)

Paths below are reproduced as Git registered them, not instructions to use them. Desktop prefix is `C:/Users/Lohith k/Desktop/`.

| Registered path relative to Desktop | HEAD | State |
|---|---|---|
| `OLD hard work/legal-compliance-regulatory-workbench` | `831c149` | `master`, active root |
| `OLD hard work/legal-compliance-regulatory-workbench/.kilo/worktrees/pine-passionfruit` | `d95dfc3` | Detached; linked to current root |
| `OLD hard work/sovereign-agentic-workbench/.kilo/worktrees/quixotic-dibble` | `94b27c5` | Detached; prunable |
| `sovereign-agent-audit` | `11960bc` | `audit/agent-runtime-20260927`, prunable |
| `sovereign-agentic-workbench/.kilo/worktrees/branch-mandrill` | `656f5d0` | Detached; prunable |
| `sovereign-deployment` | `f76913b` | `feat/offline-deployment`, prunable |
| `sovereign-durable-graph` | `ad81b36` | `feat/durable-langgraph`, prunable |
| `sovereign-enterprise-knowledge` | `e737e5d` | `feat/enterprise-knowledge`, prunable |
| `sovereign-local-voice` | `49702df` | `feat/local-voice`, prunable |
| `sovereign-maintenance-intel` | `b47fd7e` | `feat/maintenance-sensor-intelligence`, prunable |
| `sovereign-model-routing` | `82c64bb` | `feat/risk-aware-model-routing`, prunable |
| `sovereign-multimodal-pid` | `5d8adf7` | `feat/multimodal-pid`, prunable |
| `sovereign-phase-f-auth` | `1e90122` | `feat/phase-f-auth`, prunable |
| `sovereign-phase-f-ui-api` | `11fdd1c` | `feat/phase-f-ui-api`, prunable |
| `sovereign-vercel-demo` | `831c149` | Detached; prunable |

## Siblings physically inspected read-only

The parent has the active project plus the following eleven folders. Each `.git` is a **file**, containing `gitdir: C:/Users/Lohith k/Desktop/sovereign-agentic-workbench/.git/worktrees/<folder>`. Each of the requested `rev-parse --git-dir`, `rev-parse --show-toplevel`, `remote -v` and `worktree list` commands was attempted with `--no-optional-locks` and failed with `fatal: not a git repository: (NULL)`. The target is stale; their current remotes cannot be confirmed through normal Git resolution. Do not infer that the root's newly corrected origin is their independently verified origin.

| Folder | Classification | Decision |
|---|---|---|
| sovereign-agent-audit | C/D: historical linked pointer/shared-metadata risk | HISTORICAL LINKED WORKTREE — LEAVE UNCHANGED |
| sovereign-deployment | C/D | HISTORICAL LINKED WORKTREE — LEAVE UNCHANGED |
| sovereign-durable-graph | C/D | HISTORICAL LINKED WORKTREE — LEAVE UNCHANGED |
| sovereign-enterprise-knowledge | C/D | HISTORICAL LINKED WORKTREE — LEAVE UNCHANGED |
| sovereign-local-voice | C/D | HISTORICAL LINKED WORKTREE — LEAVE UNCHANGED |
| sovereign-maintenance-intel | C/D | HISTORICAL LINKED WORKTREE — LEAVE UNCHANGED |
| sovereign-model-routing | C/D | HISTORICAL LINKED WORKTREE — LEAVE UNCHANGED |
| sovereign-multimodal-pid | C/D | HISTORICAL LINKED WORKTREE — LEAVE UNCHANGED |
| sovereign-phase-f-auth | C/D | HISTORICAL LINKED WORKTREE — LEAVE UNCHANGED |
| sovereign-phase-f-ui-api | C/D | HISTORICAL LINKED WORKTREE — LEAVE UNCHANGED |
| sovereign-vercel-demo | C/D | HISTORICAL LINKED WORKTREE — LEAVE UNCHANGED |

No independent sibling is verified safe to rename. `sovereign-agentic-workbench` is absent from the listed parent; its names survive in pointers/provenance. Application source searches found exact sibling names in historical documentation, not a verified requirement to load application code from those physical sibling paths. Historical commands using a sibling interpreter are unsafe to execute. No sibling source was merged or renamed.

## Nested repository custody

- `claudex-loop` is an indexed gitlink, mode `160000`, recorded commit `8cf5e2c1771c5151d90c12642391d0ba8fa71b0e`; it has `.git/` with origin `https://github.com/chaseai-yt/claudex-loop.git`.
- `claudex-loop/claudex-loop` also has `.git/` with that unrelated origin. Stop nested Git/tool operations. Do not retarget a third-party tool repository to the application's remote. An approved plan must decide how to preserve its provenance and isolate/remove operational nested metadata without losing user content/history.
- `.kilo/worktrees/pine-passionfruit/.git` points to the current root's `.git/worktrees/pine-passionfruit`; leave it untouched.
- Physical `.kilo/worktrees/{branch-mandrill,quixotic-dibble}/.git` point to historical Sovereign paths. Stop operations there; leave unchanged.
- Root `.git/worktrees/*/gitdir` has historical external registrations. No pruning/repair is authorized by this discovery phase. Root refs/reflogs contain historical Sovereign names; history is preserved.

## Reference classification ledger

Class codes: **1** operational/dangerous; **2** historical provenance; **3** documentation; **4** branding; **5** domain terminology; **6** test fixture; **7** deployment config; **8** agent config. Multiple codes are intentional. Source locations refer to the pre-planning working tree.

| Match locations / family | Class | Proposed handling |
|---|---|---|
| Root `.git/config:9`, README repository link | Authorized identity | Keep exact legal repository; no root remote edit |
| `AGENTS.md:5` forbidden eRTMAC URL | 8, prohibition | Keep prohibition; strengthen historical/nested boundaries |
| `SOURCE_AUDIT.md:5,9,21-32` source root, old URL, sibling table | 2 | Preserve truthful provenance; current audit supersedes assertions about isolation |
| `PROJECT_HANDOFF.md:21` old source root | 2 | Preserve historical source; document contradictions separately |
| Handoff current root/setup/isolation claims at lines 13,25,29,87,93,101-150 | 3/1/7 | Do not execute; reconcile active instructions after approval; do not falsify the historical report |
| `.git/worktrees/*/gitdir`, physical `.kilo` pointers | 1/8 | Leave untouched; block worktree operations pending custody decision |
| `.git/packed-refs` archive name and historical reflog descriptions | 2 | Preserve history; not an application deployment target |
| Both nested `claudex-loop/.git/config:9` origins | 1/8 for application use; third-party attribution is 2 | Quarantine operational use; preserve third-party provenance; no nested remote change |
| `.github/workflows/regression.yml:3-5,70-71` auto triggers, old runner/environment | 1/7 | No push/dispatch; retire old live linkage in an approved custody patch |
| `.codex/hooks.json:9-10,22-23`, `.claude/settings.local.json:64,76` | 8 | Machine skill executable paths, not another app root; portability review; not invoked |
| `.impeccable/design.json:649,820`, landing surface notes:9,14; DESIGN/PRODUCT | 4/5/8 | Adapt design guidance and active product wording after approval |
| `backend/app/api/routes/health.py:12`, `frontend/src/services/api.js:71` | 4, protocol coupling | Change together with compatible health handling, not a blind replacement |
| `backend/tests/test_foundation.py:64` | 6 | Update identity expectation alongside health change; preserve regression semantics |
| Root `package-lock.json:2`, frontend package/lock names:2,8 | 4 | Safe identity patch with synchronized lock metadata |
| `README.md:68`, `backend/README.md:56`, docs/n8n and incoming n8n README:73 | 3/4 | Active docs update; incoming copy stays archive-only |
| `infra/docker-compose.ui-api-test.yml:15` old image | 1/7 | Use only a separately built legal image in a dedicated disposable project |
| Compose base/backend/auth overlay, config defaults, env template, Vite proxy, launcher | 1/7/4 | Shared service collision risk; isolate names/ports/volumes before any runtime command |
| `_incoming_phase10_bundle/.../COPY_INSTRUCTIONS.md:1,3` old copy destination | 2/3/1 if executed | Archive/reference only; never overlay into either repository |
| `benchmark/reports/final_model_runtime_readiness.md:100` and JSON:669-671 | 2/3/1 if executed | Preserve frozen history; prohibit historical commands; legal benchmark separate |
| `docs/final_security_sovereignty_audit.md:3` | 2 | Historical audit, not new legal certification |
| `docs/risk_aware_model_routing.md:107,112-113` | 2/3/1 if executed | Preserve reported history; replace active setup references later |
| `docs/local_voice_and_language_resources.md:220,250,268` | 3/1 | Old cwd commands; not approved setup |
| `docs/maintenance_sensor_intelligence.md:150,157` | 2/3/1 | Historical interpreter/import paths; not used |
| `docs/multimodal_pid_intelligence.md:147-148,164-165` | 2/3/1 | Historical validation/commands; not used |
| `docs/phase_f_authentication.md:154` | 2/7 | Historical image build claim, preserve history |
| `docs/phase5f-results/{adversarial-postgres*,frontend-*}.txt` old stack paths/package banners | 2/6 | All such matches are historical captured output, not active paths |
| `docs/offline_deployment_and_release.md:17-22` variable clone URL/old destination | 3/1/7 | Require exact authorized URL and isolated setup in current runbook; historical commands blocked |
| `docs/phase4-autonomous-continuation.md` push prohibition | 2/3 | Preserve prohibition |
| `data/.phase_e_stage/docs/offline_deployment_and_release.md:18` | 2/3/1 | Staging archive, not setup instructions |
| `data/prefrontend-frozen-readiness.json:580-582` | 2/1 if executed | Historical executable command strings; never run |
| `data/processed/phase9-live*.json` service values | 2/6 | Historical runtime evidence, not current acceptance |
| Industrial route/prompt/schema/UI/corpus strings | 5/4/6 | Adapt or retire by subsystem; keep history/tests until replacements protect shared behavior |
| Third-party dependency/tool links and licenses | 2 | Attribution, not authorization to operate those repositories |

Search covered the main source/documentation tree and separately inspected hidden agent/config/Git metadata plus ignored data source/report families. Narrow main-tree search returned 90 old-name matches before new audit documents. There is no identified executable application push URL to eRTMAC or Sovereign in the inspected runtime source. **This is not a claim of zero old references**: stale metadata, commands, branding and deployment linkage remain. A broader shell count scan could not run because `rg` is unavailable; dedicated content search was used instead. Binary archives/model weights/private credentials were not opened for a forensic scan. Historical logs and generated caches are not freshly certified. Re-scan at release after approved repairs.

## Immediate blockers requiring approval

1. Decide the unfinished cherry-pick and ownership of existing changes before checking out the migration branch. Do not pull the cached branch merely to resolve the 43-commit gap.
2. Approve a current-workspace custody/config patch for CI, runbooks and isolated service endpoints; these exceed the pre-approval change whitelist.
3. Decide nested tool/gitlink isolation without touching external repositories or deleting history.
4. Require explicit disposable database/service identities before tests; `.env`, private account JSON, backups and models are present locally, contrary to older isolation claims. Git confirms the sampled private paths are ignored/untracked; no credentials were opened or printed.

## Phase A remediation — supersedes discovery's current-state assertions

The user approved `git cherry-pick --quit` followed by switching to `feat/legal-regulatory-platform-migration`. Original HEAD is unchanged. Exact captured staged/unstaged binary diffs matched across activation; no cherry-pick commit/abort/reset or history deletion occurred. Branch activation refreshed index metadata, so the discovery index-file hash is historical, not the new byte-level acceptance oracle; semantic preservation was checked using the diffs.

CI now dispatches manually only in the exact authorized repository, uses hosted runners and has no live-inference execution/self-hosted environment linkage. Main and disposable Compose projects, service ports, image tags, DB/collection/default endpoint, Vite/CORS and launcher have been isolated. Current setup is `LEGAL_RUNTIME_SETUP.md`; historical commands are labelled superseded. Six offline custody tests and Compose/frontend checks pass; see validation report for warnings and test-environment limitations.

Custody decision for all historical/nested worktrees and both third-party `claudex-loop` repositories: **preserve in place, quarantine from application operations/build/deployment, do not repair/retarget/delete/execute**. Root Docker context already excludes this tooling. No sibling, nested metadata, historical registration or private `.env` was changed. Existing staged user terms/auth work remains; new Phase A work is unstaged. No new commit/push occurred.

The approved Phase A exit is source-level custody/configuration, not commissioning: private configuration/process overrides, live service ownership, dedicated model provision and disposable DB acceptance must still be verified before runtime operations. The frozen benchmark mismatch remains untouched.
