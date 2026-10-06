# Source audit and repository isolation

## Canonical old source

Actual root: `C:\Users\Lohith k\Desktop\OLD hard work\sovereign-agentic-workbench`.

Branch: `master`; HEAD: `831c14909afc4ed1d2b778359df07f9e6b21b5cc`.

Original origin: `https://github.com/loktrishal-05/sovereign-agentic-workbench.git` (fetch and push). This is historical provenance only, not an allowed remote for this project.

`.git` is a directory; this is the main repository/common metadata owner. All eleven listed siblings have `.git` pointer files targeting that repository at its former Desktop location. They share branches, objects and remotes; none should be treated as a disposable independent repository.

Original status: behind cached `origin/master` by 43 commits, unfinished cherry-pick of `11fdd1c`, staged terms-acceptance changes, uncommitted frontend/report changes and new frontend resources/views. All were left untouched. Cached remote HEAD `94b27c5603b29746aa9f419dde0f92c3b783b6f8` contains newer NWIS work and was deliberately not used as this application's source.

## Sibling worktree inventory

All folders below are under `C:\Users\Lohith k\Desktop\OLD hard work`. Branch/HEAD were read through their preserved relocated worktree metadata because ordinary `git -C <folder>` cannot resolve the stale pointers. All inherit the canonical remote shown above.

| Folder | Type | Branch | HEAD (short) | Indexed files | Unique useful content / source decision | Required separately? | Safe to ignore for copy? |
|---|---|---|---|---:|---|---|---|
| sovereign-agentic-workbench | Main repo, `.git` directory | master | 831c149 | 802 | Integrated application plus staged/untracked work; selected source | Yes | No |
| sovereign-agent-audit | Linked worktree, stale pointer | audit/agent-runtime-20260927 | 11960bc | 608 | Agent-runtime audit baseline, already evolved in main | No | Yes; preserve original |
| sovereign-deployment | Linked worktree, stale pointer | feat/offline-deployment | f76913b | 708 | Offline deployment/release capabilities present in main | No | Yes; preserve original |
| sovereign-durable-graph | Linked worktree, stale pointer | feat/durable-langgraph | ad81b36 | 675 | Durable graph/checkpoint capabilities present in main | No | Yes; preserve original |
| sovereign-enterprise-knowledge | Linked worktree, stale pointer | feat/enterprise-knowledge | e737e5d | 687 | Knowledge packs/enterprise workflows present in main | No | Yes; preserve original |
| sovereign-local-voice | Linked worktree, stale pointer | feat/local-voice | 49702df | 690 | Local voice/language resources present in main | No | Yes; preserve original |
| sovereign-maintenance-intel | Linked worktree, stale pointer | feat/maintenance-sensor-intelligence | b47fd7e | 673 | Maintenance/sensor intelligence present in main | No | Yes; preserve original |
| sovereign-model-routing | Linked worktree, stale pointer | feat/risk-aware-model-routing | 82c64bb | 668 | Risk-aware routing present in main | No | Yes; preserve original |
| sovereign-multimodal-pid | Linked worktree, stale pointer | feat/multimodal-pid | 5d8adf7 | 672 | Multimodal/P&ID capabilities present in main | No | Yes; preserve original |
| sovereign-phase-f-auth | Linked worktree, stale pointer | feat/phase-f-auth | 1e90122 | 723 | Auth integrated via cherry-picked history; main adds terms | No | Yes; preserve original |
| sovereign-phase-f-ui-api | Linked worktree, stale pointer | feat/phase-f-ui-api | 11fdd1c | 728 | UI-read API integrated; main has newer frontend and terms | No | Yes; preserve original |
| sovereign-vercel-demo | Linked worktree, stale pointer | detached | 831c149 | 798 | Untracked `DEPLOYMENT-VERCEL.md`, frontend ignore files and `vercel.json`; deployment-only material not imported | No | Yes; preserve original |

The first ten feature worktrees have only two tracked paths absent from main: legacy `frontend/src/App.jsx` and `frontend/src/styles.css`. These are superseded frontend entry/layout files, not missing main application files. All feature worktrees except the separately cherry-picked Phase F branches have HEADs ancestral to canonical HEAD. None of the feature worktrees has unstaged tracked modifications. Only the Vercel demo has additional untracked content; it is deployment material listed above.

Additional registered nested worktrees: `.kilo/worktrees/quixotic-dibble` at `94b27c5` (detached; newer NWIS history), and former `.kilo/worktrees/branch-mandrill` at `656f5d0` (detached; stale/prunable registration). Nested tool worktrees were not imported. No worktree pruning or repair occurred.

No root or nested `.vercel` content was found in the audited Sovereign tree. `.github` exists in main, deployment, Phase F auth, Phase F UI/API and Vercel demo. Main contains reusable Compose/Docker/n8n infra and one regression workflow; the Vercel-specific extra configurations were confined to the demo worktree.

## Missing/skipped-file checks

- Zero absent indexed paths across all 12 folders, using each folder's own Git index.
- All 168 paths referenced by `infra/frozen_benchmark_sha256.json` exist.
- Backend application Python modules parsed successfully; checked absolute `app.*` imports resolve locally.
- Checked relative frontend imports resolve locally.
- Static frontend asset references resolve; dynamic auth asset names are generated from the retained auth-media asset set.
- Required untracked main frontend views and resources, help docs and staged terms files were included.
- The Windows skipped-file dialog/log and original pre-extraction filesystem were not available. The exact historical skipped-file list cannot be reconstructed from current Git metadata alone. The checks establish completeness against the retained indexes, imports and benchmark manifest, not proof about unknown never-tracked files.
- Auxiliary `claudex-loop` tooling is a nested repository/gitlink without a usable root `.gitmodules` mapping. Its on-disk source was preserved as ordinary files, with no inherited nested Git metadata; it is not an application runtime dependency.

One existing benchmark hash mismatch remains: `benchmark/reports/final_model_runtime_readiness.json`. It is present, not a skipped file. The original integration documentation explicitly records the pre-existing report edit. It was retained unchanged.

## Copy integrity before Git removal

**PASS: 948 / 948 selected files matched SHA-256, byte-for-byte.**

| Source area | Copied files |
|---|---:|
| backend | 276 |
| backend/alembic/versions | 18 |
| backend/app/agents | 35 |
| backend/app/agents/prompts | 7 |
| backend/tests | 48 |
| frontend | 98 |
| frontend/public | 37 |
| docs | 109 |
| infra | 16 |
| benchmark | 168 |
| data | 96 |

Nested categories overlap; they must not be summed. Historical incoming extraction inputs and auxiliary tools were also retained. Package files and Linux dependency lock were included.

Excluded content: installed Python/Node dependencies, build outputs, Python/tool caches, logs, nested agent-tool worktrees, downloaded model artifacts, private `.env` files, real local-admin/account fixtures, database backups/bundles, operational extraction/index caches and generated runtime reports. Source scripts found within ignored `data/` staging/recovery areas were conservatively preserved, along with raw input examples. Some raw/runtime examples remain Git-ignored as in the source; source definitions and benchmarks are committed.

## Old identity classification and neutralization

| Class | Finding | Action |
|---|---|---|
| A — executable identity | Inherited root Git metadata with old origin/worktrees/cherry-pick state | Removed from verified new copy only; fresh repository required |
| A — operational target | Active regression workflow's `sovereign-regression` self-hosted runner and inherited environment | Disabled live job, removed old runner/environment target; workflow now manual-only |
| A — operational target | Default Compose project would be `infra`, shared with original; original ports/image tag | Explicit new project name, new host ports and new backend image tag |
| A — operational target | Frontend default proxy/port and `.env.example` endpoints could reach original local services | New proxy/backend/frontend/database/Qdrant ports; template CORS updated |
| B — historical reference | `docs/phase4-autonomous-continuation.md:83` mentions `git push` only to prohibit it | Retained; it is not a push script |
| B — historical material | Archived data staging files and historical setup docs mention original resources | Retained as historical/recovery source; do not execute as new-project setup |
| B — upstream attribution | Third-party GitHub links, licenses, dependency funding links and auxiliary tool repositories | Retained; they are not Sovereign/eRTMAC deployment targets |
| C — source/domain wording | Sovereign service names, industrial schemas/prompts/UI/corpora and terms | Retained pending separately authorized legal-domain migration |

Before adding these provenance documents, the selected application files had zero old Sovereign/eRTMAC GitHub URLs, zero Vercel project/org IDs, zero Cloudflare tunnel URLs and zero executable `git push` scripts. The only narrow identity-pattern text hit was the historical push prohibition above. The old origin appears in this document solely to explain provenance.

No deployment credentials or hosting metadata were imported. Ignoring `.vercel`, Cloudflare local state, private certificate/container backup formats and machine-local agent settings helps prevent accidental future commits.

## Secrets scan

The copy excludes real environment files, private local-admin JSON, database dumps, backups, repository bundles and downloaded runtime state. Scanning checks credential-like filenames, private-key markers, common provider token patterns, literal sensitive assignments and password-bearing connection URLs; text inside preserved ZIP/DOCX containers is included in final pre-commit checks.

Candidate matches in retained source are disposable test fixtures, public development/CI database defaults, password-validation/mock expressions, and UI labels/getpass usage. These are not copied private account or provider credentials. No actual private-key/provider-token finding is accepted. Machine-specific agent permission/hook files are not committed.

This is a repository-content secret scan, not a new runtime security certification. Never deploy example passwords or seed accounts; generate new private configuration in the isolated environment.

## Verification boundary

Isolation verifies source/file completeness, copy hashes, fresh Git history/remotes, secret exclusion and deployment-target neutralization. It does not certify live model inference, OCR provisioning, database migrations or end-to-end application behavior. Existing historical test reports are retained as provenance, not represented as newly executed backend tests. No domain development or deployment occurred.

New verification: all 900 staged file blobs matched their corresponding on-disk bytes; all 168 benchmark-manifest paths were staged. `.gitattributes` preserves snapshot bytes and marks binary assets explicitly, avoiding Windows line-ending damage to PDFs or frozen snapshots. Original folders and Git metadata, including eRTMAC-NWIS, matched a 13,439-file read-only baseline after copying and checks.

Frontend dependencies were installed only in the new copy using the lockfile and with install scripts disabled. The frontend suite passed **39/39 tests** and Vite configuration syntax passed. The test transformation harness reported inherited WebSocket port `24678` collision warnings; no existing process was stopped or reconfigured. Backend/live/database tests were not run against existing services. Inherited whitespace in historical files was preserved; changed isolation configuration and new documents passed focused whitespace checks with CRLF recognition.
