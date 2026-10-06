# Validation report — discovery and Phase A

Date: 2026-10-06. Overall: **Phase A source custody/configuration verified; legal migration and full runtime validation NOT COMPLETE**.

## Discovery checks (historical baseline; Phase A supersedes custody/config state)

| Check | Result | Evidence / scope |
|---|---|---|
| Root | PASS | `git rev-parse --show-toplevel` resolves the exact authorized legal workspace |
| Origin/config | PASS (root only) | Exact authorized `.git` URL, fetch/push; no returned pushurl/URL rewrite/include/hooksPath override |
| SHA/branch/status | RECORDED / BLOCKED | HEAD `831c14909afc4ed1d2b778359df07f9e6b21b5cc`, master, cherry-pick 11fdd1c, 17 staged paths, 19 unstaged status entries, pre-existing untracked work |
| Conflicts | No unmerged paths | Empty `git diff --name-only --diff-filter=U`; does not mean cherry-pick completed |
| Migration branch | PASS (reference only) | `show-ref --verify` confirms requested branch at same HEAD; no checkout |
| Worktree custody | FAIL isolation | Fifteen registrations including historical external paths; nested pointer risks preserved, not repaired |
| Eleven siblings | HISTORICAL LINKED WORKTREE — LEAVE UNCHANGED | Read .git pointer files; all requested read-only Git lookups fail stale resolution |
| PDF copy | PASS | Source and destination SHA-256 `69ef7ab3f5299a765d641e1f55853dbb6d21cb0ff0610c6e6ff7846ec3b5f102`; no PDF edits |
| Full PDF review | COMPLETE | 80/80 parsed pages, diagrams and appendices A-J; specification gaps recorded in target architecture |
| Private file exclusion sample | PASS for sampled paths only | `.env`, `data/phase-f-local-admin.json`, `.dump`, `.bundle`, sampled models ignored; `ls-files` does not list sampled private files |
| Architecture/reference discovery | COMPLETE at architecture level | Source plus hidden config/metadata and ignored source/report families inspected; not forensic binary/private-content certification |
| Frozen integrity | **FAIL, pre-existing** | `python -B backend/scripts/frozen_integrity.py` exits 1: mismatch `benchmark/reports/final_model_runtime_readiness.json`; no benchmark/model execution |
| Broader shell count | UNAVAILABLE | `rg` command not installed/on PATH; dedicated content search fallback used |
| Final preservation check | PASS | HEAD/active branch unchanged; index SHA-256 still `522ae5affb5c58cea5347da7746752a5740100c2ad5624bf7b3ca2c29eb7761f`; tracked staged/unstaged diff summaries match discovery baseline |
| Intended-text whitespace | PASS | `git diff --no-index --check -- NUL <path>` for AGENTS and all seven new markdown files emitted no findings |

## Discovery checks not executed (see later Phase A results)

- Backend unit/integration/PostgreSQL/security suites.
- Frontend tests/lint/build or live accessibility/browser journeys.
- Fresh/existing schema migrations, migration stamping or DB smoke.
- Live Qdrant retrieval/OCR/model inference, regulatory feed polling or performance benchmarks.
- Backup/restore, deployment or SLO acceptance.
- Dependency/SBOM/container/secret forensic scans of private/binary runtime contents.

Reason: pre-approval scope is discovery/documents and custody; actual service defaults can reach shared historical resources. Product code unchanged. Only isolated, approved runtime testing is acceptable. Historical test counts in PRODUCT/handoff/phase reports are not results of this session.

## Full migration release gates (pending)

1. Current workspace Git/config custody accepted and migration branch active without losing user work.
2. Real document/contract/review/obligation/summary journey with exact source provenance.
3. Requirement/control/evidence evaluation, expiry/version change, finding/remediation/retest and explainable status.
4. Regulatory authority/import/version/diff/applicability/change impact, freshness honestly displayed.
5. Tenant/matter/document authorization across APIs/search/chunks/models/reviews/audit/exports; prompt injection and malicious upload controls.
6. Durable async work/timers/retry/restart without duplicate authoritative records or lost alerts.
7. Fresh-to-head and current-to-head migrations with old immutable/audit data preserved in disposable DB.
8. Applicable backend/frontend/lint/build/API/retrieval/security/E2E/accessibility checks; legal fixture evaluation separate from frozen industrial corpus.
9. Tested restore/reindex/key/config recovery and selected pilot performance/availability gates.
10. Known failures, mocks, unconfigured integrations, unimplemented FRs and jurisdiction validation remaining explicitly listed before user is shown the full validation report.

No push is authorized by this document.

## Living-guide follow-up — 2026-10-06

Documentation-only verification: confirmed the authorized root/origin and local common Git directory; reviewed the existing guide/progress/instructions; expanded the A-M execution checklist and mandatory synchronization workflow. No implementation phase started.

Whitespace checks for `AGENTS.md`, `LEGAL_DOMAIN_MIGRATION_PLAN.md` and `MIGRATION_PROGRESS.md` emitted no findings. The initial wrapper incorrectly treated no-index's expected difference exit code 1 as a failure; rerunning with the correct exit-code handling passed. Index SHA-256 remains `522ae5affb5c58cea5347da7746752a5740100c2ad5624bf7b3ca2c29eb7761f`. No staging, commit, push or runtime testing occurred; existing blockers remain open.

## Phase A verification — 2026-10-06

Approved behavior: preserve user work while activating the legal branch; prevent source-default service collisions/foreign backup targets/old CI runner execution. Source plan: `LEGAL_DOMAIN_MIGRATION_PLAN.md`, A and C's moved configuration prerequisite. No commit checkpoints: the user has not authorized commits.

| Guarantee / check | Command / target | Result |
|---|---|---|
| Branch activation preserves user diffs | Captured `git diff --cached --binary` and `git diff --binary --ignore-submodules` before/after approved quit/switch | PASS: exact comparison; original HEAD retained; branch `feat/legal-regulatory-platform-migration` |
| RED before implementation | `python -B -m unittest discover -s backend/tests -p test_legal_repository_custody.py -v`, `PYTHONPATH=backend` | Expected RED: 4 unsafe-default/CI assertions fail; new backup guard absent. No unrelated dependency failures in this target |
| Isolated Compose projects/ports; native defaults/template consistency; explicit model endpoint; exact CI boundary; foreign DB/Qdrant backup rejection | Same custody target, final six tests | **6/6 PASS**. Backup failure tests assert no network/subprocess call; configuration checks do not import private Settings |
| Base Compose schema | `docker compose --env-file .env.example -f infra/docker-compose.yml config --quiet` | PASS; no containers started |
| Backend overlay schema | Same base + `-f infra/docker-compose.backend.yml`, synthetic `BACKEND_MODEL_BASE_URL=http://host.docker.internal:21434` and allowed host | PASS; quiet output; no live connection or credential dump |
| Disposable overlays | `docker compose --env-file .env.example -f infra/docker-compose.auth-test.yml config --quiet` and UI-test equivalent | Both PASS; no containers started |
| Missing model endpoint blocked | Backend overlay render with empty required model variables | Expected nonzero interpolation failure before startup; PASS negative check |
| Vite syntax/config | `node --check frontend/vite.config.js`; imported config asserts server/preview 15173, strict binding and proxy 18000 | PASS; no frontend dev server launched by these checks |
| Frontend regression | `npm.cmd --prefix frontend test` | **39/39 PASS**; inherited WebSocket port 24678 collision warnings |
| Frontend lint | `npm.cmd --prefix frontend run lint` | PASS: 0 errors, 2 existing context/fast-refresh warnings in `session.jsx` |
| Frontend build | `npm.cmd --prefix frontend run build` | PASS; Vite 7.3.6 installed runtime, 158 modules; ignored dist artifacts only; no deployment |
| Supplemental benchmark unit collection | `python -B -m unittest discover -s benchmark -p test_stage2.py -v` | NOT RUN successfully: collection fails `ModuleNotFoundError: pydantic` in selected system Python; no benchmark/model execution |
| Diff review/whitespace | Focused Phase A `git -c core.whitespace=cr-at-eol diff --check -- <changed paths>` | PASS; broad check reports inherited CRLF/whitespace. User files were not normalized; Git config unchanged |

Coverage scope: these checks protect source configuration and backup-target rejection, not full app/runtime coverage. No claim of 80% whole-application coverage, successful full backend suite, migration, DB/Qdrant/Ollama readiness, backup/restore, legal accuracy or live deployment.

Private `.env`/process overrides can supersede safe defaults; their resource ownership is an explicit prerequisite to every future live operation. Historical nested metadata remains quarantined, unchanged; it is not repaired or certified. The frozen benchmark readiness mismatch remains a release issue, not a green result.

Final custody verification: branch `feat/legal-regulatory-platform-migration`, authorized origin, HEAD `831c14909afc4ed1d2b778359df07f9e6b21b5cc`, and no remaining `CHERRY_PICK_HEAD`. Original PDF SHA-256 rechecked `69ef7ab3f5299a765d641e1f55853dbb6d21cb0ff0610c6e6ff7846ec3b5f102`. New test/runtime guide and living-document whitespace checks passed. Existing 17 staged user paths remain; Phase A implementation is unstaged. No commit/push or unrelated repository operation occurred.

## Commit custody follow-up — 2026-10-06

The user authorized regular local checkpoint commits and separately approved preserving the inherited staged terms/auth work as a commit. `34dc7af` contains exactly the original 17 staged paths; no new files were added to its index. Reviewed staged patch; no private keys/real credentials identified (password strings are existing synthetic fixtures). Exact unstaged binary diffs matched before/after. No new backend, PostgreSQL or model acceptance is claimed for this preservation snapshot. Push remains gated by the full migration/validation report and explicit authorization.
