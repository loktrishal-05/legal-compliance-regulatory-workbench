# Validation report — discovery, A/B, Phase C identity and backend build

Date: 2026-10-06. Overall: **C backend identity verified; frontend acceptance deferred to user; D backend work in progress; legal workflows/full runtime validation NOT COMPLETE**.

## Current full migration status for team publication

### E2a start / RED — 2026-10-07

Owner requested continuous verified commits/pushes and an advanced README refresh. Reverified authorized root/origin/common metadata/no config overrides, active branch `integration/backend-continuation-20261007` at `0aef554`, PR #13 OPEN with passing baseline CI; development `b3dcf4f`, migration head 0023. Approved Docker context `desktop-linux`, test Compose render PASS. New synthetic E2a test target executed in the approved Linux image and failed intentionally at the missing `app.db.models.legal_extraction` module. This is a missing-feature RED checkpoint, not test acceptance. Next add scoped immutable extraction/spans, bounded parser and source APIs; only then build the lock-aligned PyMuPDF test dependency and run actual tests. No live inference, scanner release or private runtime.

### E2a native extraction / immutable provenance — GREEN, 2026-10-07

Post-checkpoint integration review found a lifecycle response bug: repeating intake after successful extraction returned stored `ready`, but `IntakeResponse.status` still accepted only `received`/`quarantined`. Added the actual HTTP replay journey; API target ran 6 tests with 1 intended Pydantic literal-validation error. Fix the shared response contract to include current legal processing states, preserving the existing immutable result rather than resetting its lifecycle. Earlier 126-check results predate this additional journey; reconfirm affected checks before next push.

| Guarantee | Actual verification |
|---|---|
| Native TXT Unicode/CRLF quotes, DOCX paragraphs/table cells without invented pages, actual synthetic PDF headings/page boxes, blank-page uncertainty | `docker compose -f infra/docker-compose.legal-core-test.yml run --rm tests python -B -m unittest discover -s tests -p test_legal_scope_extraction.py -v`; final focused target **32/32 PASS** |
| No quarantine parsing/read-only processing, cross-workspace/unknown-source denial, success/failure revocation, hash recheck on retries, audit atomicity | Same target on SQLite and disposable PostgreSQL; current grants checked before source read and after expensive work; root industrial audit excludes new events |
| Bounded child environment/JSON/offsets/output; no silent truncation or private environment inheritance | Actual Linux child execution plus timeout/invalid/oversize-output unit checks; pure worker corpus and XML-declaration rejection |
| Scoped/session/origin/no-store source HTTP endpoints; real uploads remain quarantined | Alembic-head PostgreSQL bounded API test; 201 extraction/source quote, uniform 404 after grant revocation/unknown span, 409 quarantine, 403 bad origin |
| Complete current legal-core regression | `docker compose -f infra/docker-compose.legal-core-test.yml run --rm tests`: **126/126 PASS**, no skips |
| Coverage | Focused `python -B -m trace --count --missing --summary --ignore-dir /usr/local/lib/python3.11 --coverdir /tmp/legal-extraction-coverage --module unittest discover -s tests -p test_legal_scope_extraction.py`: service **90%**, worker **84%** line coverage. Parent/direct-unit trace only; child execution tested separately, no branch/whole-app coverage claim |
| Migration correctness/history | `... run --rm tests python -B -m scripts.validate_legal_migrations`: fresh and 0018 -> **0024_legal_extraction PASS**, metadata parity, repeat upgrades, exact old trigger/hash/ID preservation, new UPDATE/DELETE/TRUNCATE trigger message, populated-history downgrade rejection |

Review evidence: additional reproducer run had 2 intended assertion failures and 2 wrong-exception errors for replay tampering and failed-parser revocation; shared service corrected, final focused and broad checks pass. Stricter trigger assertion initially failed because standalone parent TRUNCATE was blocked by its FK before the immutable trigger; validator now attempts schema-local synthetic TRUNCATE CASCADE, verifying the intended trigger message. No expectation weakened.

Added PyMuPDF 1.28.2 to the bounded image, matching the existing Linux lock; no model artifacts/dependencies or private services added. Runtime is Linux-only/fails closed elsewhere, synchronous and bounded (10-second wall deadline, 5-second child CPU, 512 MiB address space, 8 MiB output file, 2 MiB extracted characters, 2,000 spans, at most 100 PDF pages). Resource limits are **not** a deployment-grade kernel filesystem/network sandbox. PDF/DOCX native structure stays `needs_verification`; blank/scanned content never gets fabricated text. OCR execution, validated correction workflow, durable dispatch/restart, deployment-grade sandbox/quotas and legal index integration remain open E2/E3 gates. No live scanner is configured; HTTP uploads stay quarantined. Citation reads resolve immutable extraction text/locators, not a fresh integrity check of the original on-disk file; later release/viewer integrity policy must cover that distinction. Historical full industrial runtime regression, real legal corpora, SSO/MFA, legal policy packs and recovery/pilot acceptance remain pending. Existing Starlette/SQLite/duplicate-ZIP fixture warnings unchanged.

### 2026-10-07 E1 hardening — RED evidence

Verified authorized root/origin/common metadata/sample-only hooks and Docker Desktop Linux context. Development is `b3dcf4f`, source migration head `0023_legal_intake_audit`; main is `a85494d`. Earlier status tables remain historical. PRs #4-#12 are merged; no open PRs. GitHub currently requires zero approvals but root AGENTS independent-review/no-bypass constraints are retained.

`docker compose -f infra/docker-compose.legal-core-test.yml config --quiet` passed. Dedicated synthetic PostgreSQL only, internal network/no published ports/no private mounts/model and vector loopback port 9.

RED command: `docker compose -f infra/docker-compose.legal-core-test.yml run --rm tests python -B -m unittest discover -s tests -p test_legal_scope_intake.py -v`. After correcting two test subtest-context reporting errors, 28 tests ran with **17 intentional assertion failures, zero errors**: XML relationship quote/whitespace/character-reference/UTF-16 bypasses; malformed/DTD XML; duplicate/case-colliding ZIP members; unsupported compression; wrong source hash, duplicate tampering and publication overwrite race. Existing intake checks passed. This checkpoint is reproducer evidence, not E1 acceptance. Next: fix the shared service, rerun the target and broader scoped/migration checks.

### 2026-10-07 E1 hardening — GREEN and scope

| Check | Actual result |
|---|---|
| Same reproducer target after shared service fix | 28/28 PASS; all previously failing assertions now pass |
| Additional XML size/macro, missing-original and symlink boundaries | Final focused intake target 33/33 PASS, including SQLite and PostgreSQL |
| Line coverage | `... run --rm tests python -B -m trace --count --missing --summary --ignore-dir /usr/local/lib/python3.11 --coverdir /tmp/legal-intake-coverage --module unittest discover -s tests -p test_legal_scope_intake.py`: intake service **96%** (253 executable lines). Line coverage only; no whole-app/branch/E2E coverage claim. An earlier trace run omitted `--missing` and printed misleading 100% summaries; those percentages are discarded. |
| Final scope/API/provisioning/isolation/migration regression | `docker compose -f infra/docker-compose.legal-core-test.yml run --rm tests`: **93/93 PASS**, zero skipped tests |
| Actual disposable PostgreSQL upgrades | `... run --rm tests python -B -m scripts.validate_legal_migrations`: fresh and 0018 -> actual head **0023** PASS, ORM parity and repeat upgrade, old evidence/audit/immutability preservation checks PASS |
| Source/security review | Reviewed shared intake callers (versioned route + tests), authorization before duplicate original reads, stable rejection codes/audit without source text, no original replacement or missing-file repair, no new dependencies/migrations |

Warnings: intentional duplicate-ZIP synthetic fixture warning; inherited Starlette httpx deprecation and SQLite expression-index reflection limitation. Checks run in the approved bounded Linux image, not full app startup or native Windows original-storage acceptance. Filesystem write-once assumes service-owned directories and hard-link support; protection against a malicious local administrator and filesystem crash-durability/restore remain L/M acceptance work. Simultaneous same-workspace DB duplicate insertion recovery, real malware scanner integration, real-world document corpora, sandboxed parsing/OCR, spans/corrections/retrieval and full legal journeys remain unfinished. HTTP intake still uses `scanner=None`, so real uploads remain quarantined.

Current full status: A/B source/design complete; C backend identity verified, frontend owner-managed; D development exit recorded with historical industrial-regression gap; E1 partial/hardened, E2/E3 pending; F pending; G/H deterministic core only, registry/domain persistence pending; I/J and L/M pending; K owner-managed. Enterprise identity/MFA/re-auth, legal packs/terms/retention/hold, model/private-resource/deployment and recovery/SLO approvals remain open. This is a verified partial backend checkpoint, not operational-pilot or all-66-FR acceptance. Publication requires the report shown to the user and explicit authorization; independent review remains a repository instruction even though GitHub's approval count is zero.

Publication evidence: full status/report shown and explicit owner **Push and open PR** authorization received. Reverified exact root/origin/common metadata/no hook or URL overrides, intended all-commit diff/log and unchanged development base `b3dcf4f`; pushed `9327f9b` + `9e9e01e` normally to the authorized continuation branch and opened PR #13. `docker compose -f infra/docker-compose.legal-core-test.yml down --volumes` removed only the dedicated synthetic test container/network. No merge/main change/approval or private service operation. Remote CI is separate from these local results; verify the newest PR HEAD after this documentation-only evidence update.

| Phase / area | Acceptance state |
|---|---|
| A/B | Source custody/configuration and approved development architecture complete; private deployment acceptance pending |
| C | Backend identity verified; saved frontend identity checks green; frontend/design acceptance owner-managed |
| D | Initial scoped models/policy/metadata APIs and migrations verified; provisioning/legacy-path isolation/tenant dedupe pending |
| E/F | Secure intake/OCR/provenance, contract intelligence and cited summaries planned |
| G/H | Regulatory versions/changes/applicability and compliance/evidence evaluations planned |
| I/J | Durable obligations/timers, legal review/remediation/audit planned; old primitives do not complete these |
| K | Owner-managed frontend; real legal journeys/usability acceptance remains required |
| L/M | Cross-system security/legal evaluation, full runtime/recovery/restore and final FR reconciliation pending |
| Pilot gates | Enterprise identity/MFA/re-auth, validated legal packs/terms/retention/hold, private resource ownership and recovery/SLO acceptance pending |
| Publication | Base 496f903 published/protected; PR #4 handoff/CI updates await independent approval; main reconciliation separate |

All 66 FRs remain tracked. Three workstreams assign all backend work; none is dropped or accepted merely by publication. This is not a completed application or compliance claim.

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

Phase A checkpoint `dfea5db`: 29 explicit paths covering custody/config/tests/guides/master PDF/provenance. Before staging, custody suite revalidated 6/6 and PDF hash unchanged; cached whitespace check passed with CRLF recognition. Post-commit status confirmed unrelated frontend, benchmark, nested tooling and private/runtime work was not included. This does not certify a clean or complete whole working tree.

## Phase B document acceptance — 2026-10-06

| Check | Evidence / result |
|---|---|
| Explicit development baseline approval | User selected approved baseline; enterprise/legal/retention/recovery policies remain operational-pilot gates |
| Mature component compatibility | Read session/deps, immutable revision model, Document/DocumentVersion, Query and S1-S7 output contracts before defining additive legal contracts |
| Complete catalogue mapping | Dedicated content search `^\| FR-[0-9]{3} \|` in `LEGAL_REQUIREMENT_TRACEABILITY.md` returned **66** rows; inspected sequential 001-066, no duplicate/missing rows; Must 001-045 / Should 046-066 preserved |
| Source/authority/time invariants | Reviewed exact immutable version/span binding, unknown-date handling, historical/effective time, authorized retrieval and insufficient-evidence release boundary |
| Governance/isolation invariants | Reviewed scoped role/ACL matrix, no default admin content-read, independent reviewer, six assessment states, immutable successor revisions and deterministic timers |
| Scope honesty | All legal FR rows planned; local auth explicitly development-only; no configured regulator, validated jurisdiction pack, legal accuracy or SLO attainment claimed |
| Documentation whitespace/diff | New contract/registry no-index checks and focused tracked-document `git diff --check` passed with CRLF recognition; reviewed intended document diff |

Phase B is documentation/architecture acceptance only. No new business logic, migration or backend domain test was executed; reversible documentation changes do not need a mirrored implementation test. Implementation phases must add real components/tests/demo evidence before any FR status changes. No services/models/DB, deployment, push or unrelated Git operations were invoked.

## Phase C start / RED — 2026-10-06

User approved neutral development branding with existing styles and exact legacy-terms preservation/labeling. Frontend preservation snapshot `1968d2e` contains 29 approved paths; 39/39 existing frontend tests passed and unrelated diff comparison passed before Phase C edits.

- `python -B -m unittest discover -s backend/tests -p test_product_identity.py -v`: two intended identity assertion failures before implementation.
- `node --test src/productIdentity.test.js src/services/api.test.js` from frontend: five intended identity/copy/health failures and nine existing passes before implementation.
- Native venv inspection: prefix is inside current application; FastAPI import fails because `ujson` DLL is blocked by Application Control. No app services imported, no model/DB execution and no security policy changed. AST-isolated health/title contract checks avoid that dependency; no full HTTP acceptance claimed.

## Phase C GREEN and pause evidence — 2026-10-06

| Check | Actual command / result |
|---|---|
| Focused identity/API | `node --test src/productIdentity.test.js src/services/api.test.js` from frontend: **14/14 pass** after implementation |
| Complete frontend | `npm.cmd --prefix frontend test`: **44/44 pass**; existing Vite test WebSocket 24678 collision warnings |
| Frontend lint | `npm.cmd --prefix frontend run lint`: 0 errors, 2 existing fast-refresh warnings in `session.jsx` |
| Frontend build | `npm.cmd --prefix frontend run build`: pass, Vite 7.3.6, 159 modules; ignored build output, no deployment |
| Backend pure identity | `python -B -m unittest discover -s backend/tests -p test_product_identity.py -v`: **2/2 pass**, no private Settings or native/server import |
| Custody | `python -B -m unittest discover -s backend/tests -p test_legal_repository_custody.py -v`, `PYTHONPATH=backend`: **6/6 pass** |
| Master PDF / legacy consent | SHA-256 unchanged: master `69ef7ab3f5299a765d641e1f55853dbb6d21cb0ff0610c6e6ff7846ec3b5f102`; terms DOCX `feef43e2378f40e48cd9cd5449d121c56fb2f9bd4dc47e860c87a8db2735bc6f`; exact-document frontend test passes |
| Browser / final mechanical scan | **Not executed**: user paused before browser verification; do not claim responsive/visual/interaction acceptance |
| Preview cleanup | Temporary frontend process 35516 and its children stopped successfully; no unrelated process or DB/model service stopped |

Phase C pause checkpoint is a tested partial implementation, not completion. Native full backend/HTTP/migration/model acceptance remains unverified due blocked `ujson`; no OS policy changes or dependencies installed. Existing frozen benchmark mismatch remains unchanged. Resume steps/approvals/current hazards are durable in `SESSION_RESUME.md`.

## Resume verification and user scope change — 2026-10-06

Exact root/origin, migration branch at `770c834`, local common metadata and sample-only hooks verified. Historical worktrees remain untouched. Reviewed backend identity patch and frontend coupled health contract; no storage/schema rename introduced.

Isolated frontend preview PID 14916 used proxy `http://127.0.0.1:9` and intercepted `/api/**` responses. Landing desktop 1440/mobile 390: assets loaded, no horizontal overflow, reduced-motion fallback and keyboard skip-link observed. Login desktop/mobile: assets loaded, no video, no overflow; unavailable/process-online labels matched mocks. Terms desktop/mobile: legacy v1.0 notice and original text present, acceptance disabled before acknowledgement. Help shell desktop/mobile: notices/legacy resource labels and assets present; stable layout has no overflow (immediate resize measurement caught a transient transition). DOM spot checks: no missing image alt attributes, unlabelled login inputs or unnamed visible help-shell buttons. No bundled mechanical detector was available. These are bounded observations, not a WCAG conformance audit or real backend/session acceptance.

One unintended authenticated redirect reached the legacy dashboard with a generic `{}` mock and caused a rendering error; probe timeouts and this mock-shape failure are not passes. Dashboard is outside this bounded identity check and no frontend repair was made. User subsequently deferred frontend/landing/design acceptance and K to their own work; backend D may proceed. Existing frontend files remain preserved outside the backend checkpoint. No broad unchanged suites repeated; earlier results remain dated evidence.

## E1 secure intake — 2026-10-06

`docker compose ... run --rm tests`: 76/76 OK (adds 8 SQLite + 8 PostgreSQL intake tests and the real upload-route API test on an Alembic-head schema). Validator PASS fresh and 0018 -> 0023. Covered: 11 rejection codes audited with nothing stored, 6 quarantine reasons, write-once read-only originals and tamper detection, idempotent same-workspace dedupe, conflict without leaking another member's document, independent copies across tenants, viewer/clearance/non-member/matter denials, audit-failure rollback, 413/422/403/404 HTTP mapping. Not covered: real malware engine (none configured), real-world PDF/DOCX corpora, extraction.

## D audited provisioning — 2026-10-06

Branch `team/1-documents-contracts` (integrator; all three teammates unavailable). Disposable legal-core Compose project only; network removed after each run.

| Command | Result |
|---|---|
| `python -B -m unittest tests.test_legal_scope_provisioning` (Windows venv, SQLite) | 7 OK, 7 PostgreSQL skipped |
| `docker compose ... run --rm tests` (all `test_legal_scope*`) | 41/41 OK (27 prior + 7 SQLite + 7 PostgreSQL provisioning) |
| `docker compose ... run --rm tests python -B -m scripts.validate_legal_migrations` | PASS fresh and 0018 -> 0021: parity, idempotent, reversible without history, provisioning event accepted, unknown event rejected, lossy downgrade refused |
| CLI `--help` / invalid UUID | parses; rejects before settings/DB import |

Not covered by the first slice: dedupe/isolation (added below); HTTP provisioning UI (intentionally none).

D dedupe/isolation follow-up (same branch): 0022 plus guards. `docker compose ... run --rm tests` 57/57 OK; validator PASS fresh and 0018 -> 0022 incl. `alembic check` parity, reversibility without scoped rows, per-namespace duplicate rejection and lossy-downgrade refusal. Mutation (drop document-ownership half of the guard) is caught by `test_owned_document_hides_unstamped_legacy_namespace_version`. Industrial regression: 24 affected modules run on baseline and branch; identical results — runnable modules pass the same (agents_knowledge 25, knowledge 11, release_retrieval 7 OK; model_routing 4 pre-existing errors); the other 20 cannot import in either runtime (bounded image lacks qdrant_client/langgraph; Windows Application Control blocks psycopg/ujson). This is a recorded gap, not a pass.

## Part 2 deterministic G/H core — 2026-10-06

Branch `team/2-regulatory-compliance` (owner reassigned Part 2 to the integrator). Pure stdlib modules; no DB/settings/network/model access, so no test container dependency beyond Python.

| Command | Result |
|---|---|
| `python -B -m unittest tests.test_legal_regulatory_core -v` (backend venv, Windows) | 14/14 OK |
| Same module in approved `legal-core-test` image, `--no-deps`, no network | 14/14 OK (Python 3.11 image; network removed after run) |
| Mutation: inclusive `effective_until`; removed partial state; allowed cross-workspace link | each FAILED as expected (1, 2, 2 failures) |

Not covered: persistence/migration 0022, tenant FK enforcement in PostgreSQL, APIs, authorized human applicability, semantic change proposals, review binding. Not FR acceptance.

## Initial D verification — 2026-10-06

- RED: native isolated target fails because the new scope module is intentionally absent. Initial in-memory policy/migration checks subsequently passed 12/12.
- Approved dedicated legal-core Compose project: internal network, no host ports/persistent volumes, selected backend read-only mounts, no private `.env`/data/models. Bounded Linux Python 3.11 core dependency test image; no OCR/AI weights, not a release image.
- First migration attempt failed before connection because Settings requires MODEL_NAME; explicit fixture tag supplied, model/vector URLs remain unused loopback port 9. No inference/private DB access.
- `docker compose -f infra/docker-compose.legal-core-test.yml run --rm tests`: **27/27 passed** (10 SQLite policy, 10 PostgreSQL policy, 4 bounded API, 3 migration/target checks).
- `... run --rm tests python -B -m scripts.validate_legal_migrations`: fresh -> 0020 and 0018 -> 0020 PASS; Alembic parity/repeat upgrade PASS; legacy source/version hashes and audit hash/chain preserved; existing trigger definitions unchanged; zero automatic ownership mappings.
- Actual scoped router + real session/terms dependencies on PostgreSQL; actual main middleware AST-loaded into a bounded app. No full industrial/AI root-router startup acceptance claim. Unknown/denied/cross-workspace IDs match; header spoof/revoked sessions/old terms deny; no source paths/body/hash response; denial audit contains requested IDs only.
- Warnings: Starlette httpx TestClient deprecation; inherited SQLite expression-index reflection limitation. Duplicate-ownership ORM warning eliminated with Core insert; no dependency churn for the TestClient warning.
- Final review adds cache/referrer headers to early origin denials; confirming suite required before checkpoint. Remaining D provision/legacy/retrieval/audit/dedupe gates and complete record-level governance preservation proof remain explicit.
- Full backend/legal/model/recovery suite remains incomplete; native ujson limitation and unrelated frozen-readiness mismatch unchanged. New PR CI is baseline regression, not an autonomous reviewer or future-feature acceptance.

Final checkpoint confirmation: after the header and negative-insert edits, 27/27 scoped checks and both fresh/0018-to-head migration paths passed again. Focused frontend paired identity/API 14/14, backend pure identity 2/2 and custody 6/6 passed. No unchanged full frontend suite/lint/build repeated; earlier 44/44/lint/build results remain historical evidence. User saw the current complete status report and explicitly approved development-base publication, the existing tested identity snapshot and PR protection on main/development. Main remains unchanged pending unrelated-history reconciliation; no deployment/live inference authorization.

Publication evidence: checkpoint `87cd2bd` pushed normally to the authorized development branch. GitHub Actions `Legal backend checks` run `37491748786` completed SUCCESS, including the `legal-core` scope/API/migration baseline. Issues #1 (Part 1), #3 (Part 2), #2 (Part 3) created. These are assigned work slots, not guessed GitHub identities. Master PDF Git blob equality passed, staged whitespace check passed, sampled high-confidence credential/private-key scan found no matching indexed paths, and historical tracked blobs over 50 MiB were absent; no comprehensive historical secret certification is claimed. Only the approved disposable PostgreSQL project was removed. Main at d95dfc3 remains unmodified.

Final remote checks: shared base 496f903 and CI run 37492025870 SUCCESS; three team branches match the base. Main/development protection read-back confirms strict legal-core, independent approval (including last-push requirement), stale-review dismissal, conversation resolution/admin enforcement, force pushes/deletions disabled. Main remains d95dfc3. No teammate PRs at final polling; GitHub issue assignees intentionally pending actual handles. Further evidence edits go through a normal PR; no protection bypass or automatic merge.

Handoff PR #4 baseline run 37492479516 passed all scope/API/migration steps, but checkout-action post-cleanup warned because the inherited claudex-loop gitlink has no .gitmodules URL; this is not a feature test failure. Nested metadata remains untouched. The new baseline workflow is being corrected to fetch the authorized public source explicitly with no credentials and no recursive submodule operations; confirming remote run required. No root Git configuration changes or nested-tool repairs.

Correction confirmed at 9cd84af: push 37492888207 and PR 37492895455 SUCCESS with credential-free/non-recursive source checkout, scoped tests and both migration paths. Results also recorded in PR #4; independent approval still required. No nested/main modification.

Claude handoff is documentation only. Reverified Git/remote branches/issues/protection flags/PR head/checks; consolidated reading/approval/state/team/commit-review instructions and archived old resume notes. Referenced document targets exist; focused whitespace check passed and master PDF Git blob equals HEAD. No new application/legal/model test claim or local whole-app rerun. Commit only intended documentation to the existing review branch; required GitHub baseline CI runs normally after push, with results recorded in PR #4.
