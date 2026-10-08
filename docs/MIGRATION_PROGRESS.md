# Migration progress

Date: 2026-10-06. **Backend build resumed; user owns frontend/landing. D in progress. Handoff: `SESSION_RESUME.md`.**

## Current state

### PAUSE checkpoint — bounded OCR and transcription correction review, 2026-10-08

Owner is stopping for the night and requests commit/publish/main. No further feature implementation is authorized during the pause. RED OCR `dd81e9f`, correction `ca76ab5`; GREEN checkpoint follows with this report. Implemented opt-in English PDF OCR under separate `legal-ocr-v1`, native text preserved in mixed PDFs, exact page/region/method/offset spans, language-data SHA-256 in extractor lineage, and persistent immutable proposals/independent approve/reject decisions. Corrections preserve original quotes/artifacts; successor proposals retain prior decisions. Approval confirms transcription only and never marks an OCR document legally approved/ready. Migration head 0025; role + read/review ACL + platform reviewer eligibility + different requester/reviewer enforced, including database self-review constraint.

Files: parser worker/extraction service/schema/API, optional setting/template, public language-data test image, correction model/schema/service, model/audit/policy registration, additive 0025, migration validator/head tests, synthetic OCR/correction tests; guide/progress/validation/FR/architecture/reuse/runtime/handoff/resume updated. Final **168/168 scoped tests**, **38/38 extraction/OCR checks**, fresh/0018-to-0025 parity/history/immutable UPDATE/DELETE/TRUNCATE/lossy-downgrade and DB independent-review checks pass. Correction service 96%, worker 81% line coverage; no full-app/branch claim. Test-only validator indentation, membership flush ordering and oversized six-page fixture failures corrected without weakening guards; see validation.

Current stage E remains partial. English OCR is capped at 5 image-bearing pages, 200 dpi, 8M page/source-image pixels, 20 child CPU/30 wall seconds/768 MiB; output caps unchanged. No confidence probability invented; all OCR needs human verification. Empty/unrecognized regions cannot yet be manually transcribed without a stored text span; broad legal golden quality/multilingual/handwriting/table acceptance and frontend source correction journeys remain open. Next resumed build: durable jobs, restart/retry, production parser isolation, then authorized retrieval; F contract/summaries, G/H persistence, I/J monitoring/remediation, K owner-managed frontend and L/M security/recovery/pilot gates remain. Private application scanner/OCR configuration unchanged, real uploads still default quarantine.

GitHub verified: PR #13 OPEN at remote 9763a81, no reviews; main requires strict legal-core (configured approval count zero, repository independent-review rule still binding). Publish checked continuation checkpoint, not direct main push or self-merge; normal reviewed dev -> main promotion awaits integration. Preserve all benchmark/nested/private/untracked artifacts. Resume through SESSION_RESUME only when owner asks. No overnight assistant process/model/scanner is left running; synthetic test runtime cleanup follows.

### E2 OCR / corrections start — 2026-10-08

Owner requested the next milestone. Verified root/origin/common metadata, local 89c45fe and preserved unrelated work. Traced native worker/service/schema/model/API, PDF inspection and existing Paddle service. Reuse PyMuPDF and bounded subprocess; avoid private model paths/industrial OCR normalization. Tests first for actual synthetic scanned/mixed PDFs and source coordinates, then immutable correction/independent decision/FK/audit/API tests. Planned migration 0025 follows actual 0024; no private DB/model/frontend/push execution. Next add opt-in English OCR and correction review, run dedicated synthetic validation and record actual limits.

### Isolated real scanner validation start — 2026-10-08

Owner requested proceeding one by one. Reverified local c5dd8b9, authorized root/remote/common metadata/no hook override, preserved unrelated work and desktop-linux context (8.16 GB Docker memory). Official latest release reports clamav-1.5.4; pulled official preloaded image and recorded digest `sha256:ebec5bc138401b36ae987caa1a3fa3c3b2a21ed3d51f0bfa5852825e663e67b0`. Image identity checks: clamav UID 100/GID 101; ClamAV 1.5.4, bundled daily signature 28136 dated 2026-09-27. Signature freshness is a current blocker; build the isolated updater/engine/test profile and update before acceptance. No private configuration/application services or frontend enabled.

### Isolated real scanner / freshness checkpoint — 2026-10-08

RED `99eea33` records real engine detection/HTTP checks with intentionally stale bundled signatures. Dedicated FreshClam updater downloaded/verified daily 28147, signed 2026-10-08 06:24:12 UTC, retaining main 63 and bytecode 339. Seven real-engine checks pass (clean TXT/PDF/DOCX, plain/compressed/nested EICAR, encrypted PDF, recursion/stream limits, actual HTTP clean extraction vs quarantined detection/replay); stopped-engine HTTP upload quarantines (1/1); restart/revalidation passed. Docker inspect confirms user 100:101, network none, read-only root/signatures, dropped ALL capabilities, no-new-privileges, 4 GiB cap and only reviewed config/signature/socket mounts.

Follow-up RED `f4616b8` reproduced missing per-request freshness validation. Adapter policy `clamd-instream-v2` now checks bounded VERSION before scans by default, rejects stale/future/invalid/unavailable signature metadata before document transmission, and shares the same total deadline with INSTREAM. `WORKBENCH_LEGAL_SIGNATURE_MAX_AGE_HOURS` defaults provisionally to 72 (bounded 1–168); deployment policy approval remains required. Explicit `max_signature_age_hours=None` is reserved for raw protocol fixtures; HTTP uses the checked factory. Final 142/142 scoped checks and 9/9 protocol checks pass, 97% adapter line coverage. Existing migration 0024 unchanged; current migration-source/parity checks included in scoped suite; fresh/0018 preservation evidence from prior milestone still applies, not newly rerun here. Validation records tmpfs YAML, one-off shell quoting and fresh VERSION fixture-format errors and their corrections.

Files: scanner adapter/settings/template; new `infra/clamav` configs and scanner test overlay; real engine/outage/protocol tests; guide/progress/validation/runtime/FR/architecture/reuse/handoff/resume. Development engine milestone verified, E still incomplete. No private app/.env enablement, broad malware-corpus certification, source storage/model/frontend/deployment/main integration or push. Operational freshness threshold/monitoring/update schedule, exact per-upload engine/signature lineage and historical quarantine rescan/release remain; next build is OCR/corrections/durable jobs/parser isolation then E3. Dedicated runtime cleanup and local GREEN checkpoint follow; preserve public signature cache for efficient reruns.

Completion evidence: direct scanner default also checks freshness; final 7 engine/1 real outage/142 scoped/9 protocol checks pass, coverage stays 97%. Combined Compose down removed only dedicated scanner/PostgreSQL containers and networks. Owned public signature/socket volumes retained; no unattended scanner/updater. Intended whitespace passes, unrelated benchmark/nested/private/untracked work remains excluded. Local verified GREEN checkpoint follows; no push requested.

### Phase E scanner integration start — 2026-10-08

Owner requested building the remaining work. Root/origin/common metadata/sample-only hooks and user artifacts verified; continuation HEAD 9763a81 matches open PR #13, legal-core SUCCESS (run 37662308360). Docker context desktop-linux; disposable test targets inspected. First increment is configured local scanning through the existing intake callback, fail-closed outages/protocol handling and post-scan authorization recheck. Tests first; no real engine/private runtime/frontend/main integration enabled. Next: validate scanner adapter and HTTP intake, then remaining E2 gates.

### Phase E scanner adapter verified checkpoint — 2026-10-08

RED checkpoint `991437c` preserves the missing adapter and intake revocation/outage reproducers. Delivered `backend/app/services/legal_malware.py`, settings in `core/config.py`/`.env.example`, upload-route wiring and intake v3 handling with scan outcome/policy metadata in the existing version/audit transaction. Standard-library socket/struct/time only; no new dependency or migration. Tests verify chunked exact bytes, fragmented clean replies, detection redaction, malformed/truncated/oversized/ambiguous replies, missing socket/timeout/total deadline, optional local-path configuration, HTTP clean/detected/outage/duplicate states, non-boolean callback rejection and revocation committed by another DB session before original publication. Earlier archive/hash/source tests remain green.

Actual checks: adapter 6/6; API 7/7; intermediate intake 37/37, final expanded intake included in **139/139 legal-core tests**, no skips. Scanner adapter **98% line coverage** by stdlib trace (not whole-app/branch coverage). Fresh and 0018 -> 0024 migrations, parity/idempotency/immutable spans/history pass. Same-session source/security review completed; independent human review remains open. Runtime guide §8 describes operator configuration and real-engine/signature/limit acceptance; default is still unconfigured, all current real HTTP uploads still quarantine. No live scanner/model/private runtime/deployment/frontend/main operation. Remaining E2 OCR/corrections/durable jobs/kernel sandbox and E3 retrieval precede F; other backend/acceptance phases remain as previously recorded. Updated plan/validation/FR/architecture/reuse/handoff/resume with this partial evidence. Local checkpoint only; no push requested in this session.

Final custody checks: bounded image lacks PyYAML for custody suite; native initial command lacked PYTHONPATH. Correct documented native command passes 6/6; errors recorded in validation. Intended whitespace passes. Dedicated disposable PostgreSQL container/network removed; Docker Desktop remains running. Benchmark/nested/private/untracked artifacts preserved and excluded.

### Owner-requested README promotion to main — 2026-10-07

Owner reported the advanced README was absent from main and asked for the authorized repository to be fixed. Built a README-only branch from current main a85494d in the authorized root, preserving benchmark/nested/untracked bytes. Commits e89f662/fc34ea0 provide architecture, source ER, system design, intake/extraction/target flows, API/status/verification and references with explicit main/development/#13 availability. GitHub preview exposed a semicolon parse error in the sequence diagram; corrected it and reverified five SVG diagrams/ten tables with no errors.

Reviewed all commits/full diff (only README), required legal-core run 37661284977 SUCCESS, current protection has zero approvals/strict check/admin enforcement/no force/delete; used a normal merge of PR #14 after the explicit owner main-fix instruction. Main is now **04d719f**; actual diff from a85494d is README only. No self-approval, protection change or backend/main-feature acceptance. Repository homepage confirms advanced README rendering. Backend PR #13 remains OPEN (e3f677d check run 37659371892 SUCCESS), with remaining E2/E3/F/G-H persistence/I-J/L-M gates unchanged. Returned to root continuation branch. Final evidence-only update/push follows; no new runtime services/models.

### E2a start — 2026-10-07

Owner authorized continuing E2 with ongoing verified commits/pushes and a professional README including architecture, system design and workflow diagrams. Root/origin/status reverified; PR #13 open/passing at `0aef554`; development `b3dcf4f`, main `a85494d`, no new workstream-3 remote commits. Continue on the authorized root branch. Current scope: tests-first native extraction, immutable scoped artifact/spans and source API through additive 0024. Existing scanner quarantine stays intact. README will clearly label implemented vs planned systems. Preserved unrelated user artifacts; no external worktree or private runtime execution.

### E2a verified native-provenance checkpoint — 2026-10-07

RED `20833ab` references the intentionally missing model. Delivered two immutable source tables through additive 0024, qualified version/hash/tenant foreign keys, ORM/PostgreSQL history protection, two versioned endpoints, typed bounded parser IPC, native TXT/DOCX/PDF worker and exact quote resolver. Reused native PyMuPDF inspection with opt-in heading retention and deferred Docling settings import; legacy default heading behavior retained. Test image adds already-locked PyMuPDF 1.28.2 only. Original bytes/hash and old migrations/envelopes unchanged.

Review found and reproduced two retry/revocation gaps (2 assertion failures + 2 wrong-exception errors); fixed at the shared service: reverify original bytes even on replay, and recheck authorization before recording parser failure. Final 126 scoped tests and 32 focused checks pass; extraction service 90%, worker 84% line coverage. Migration validator passes fresh/0018-to-0024 and enforces actual trigger messages; initial strict truncate proof exposed PostgreSQL FK blocking before trigger, corrected to schema-local synthetic TRUNCATE CASCADE, then trigger rejection verified.

Files: legal_extraction model/schema/service, parser worker, 0024 migration, shared source/version/audit/model registration/native inspection, legal_scope routes, validator, extraction/API/migration tests and bounded Dockerfile; living guide/FR/architecture/reuse/handoff/evidence synchronized. E2 remains partial: native DOCX/PDF layout requires verification; no OCR/correction/async queue/kernel sandbox/scanner release/index cutover. Next build finishes those E2 gates before E3/F integration. README refresh is the next documentation checkpoint. Full runtime/legal/FR/pilot acceptance and independent review remain open.

### Active continuation — 2026-10-07

Published E2a GREEN as `35f9e1b` with RED predecessor `20833ab` under the owner's ongoing continuation authorization. Review then reproduced processed-upload replay failing the old status response contract; RED `2e033ba`, minimal shared-schema fix and **6/6 API checks PASS**. Processed duplicates preserve existing state and provenance.

README refreshed with a restrained technical presentation, delivered-vs-planned architecture diagram, implemented source ER diagram, request/authority/failure design table, intake sequence, extraction flowchart, target compliance lifecycle, API catalogue, verification evidence and developer/acceptance references. No new product/frontend implementation. Next: finish remaining E2 gates (OCR/corrections/durable dispatch/approved sandbox) before E3/F; current real uploads still quarantine.

README/replay GREEN published as `54b1149`; GitHub PR #13 legal-core run `37645213603` SUCCESS. Live GitHub preview shows five Mermaid SVG diagrams, 11 structured tables, expected headings/anchors and no Mermaid syntax/error display. Browser inspection is documentation rendering only, not application frontend acceptance. Dedicated synthetic test container/network removed. Final documentation evidence committed/pushed under standing continuation authorization; reverify latest PR HEAD/checks before integration.

Verified current GitHub development `b3dcf4f`, main `a85494d`; PRs #4-#12 merged, no open PRs at entry. Started `integration/backend-continuation-20261007` in the authorized root; preserved benchmark/nested/untracked user work. Merged D development exit and E1 intake are present; G/H has deterministic logic only. The local handoff branch was stale. No new frontend, private runtime, model execution or historical worktree operation.

Delivered E1 corrections in `backend/app/services/legal_intake.py`, with reproducers and boundary checks in `backend/tests/test_legal_scope_intake.py`: decoded XML external-link checks, bounded XML/DTD/entity/macro guards, unambiguous ZIP member/compression checks, matching content address before storage, duplicate original integrity/lineage checks and create-only original publication with temporary-file cleanup. New records use `legal-intake-v2`; historical metadata/hashes stay untouched. RED checkpoint `9327f9b`: 17 intended assertions failed; final GREEN: 33 focused tests, 93 scoped tests, 96% intake service line coverage; fresh/0018-to-0023 validation passed. Existing warnings remain documented. Guide/validation/FR/architecture/reuse/handoff/resume synchronized; no phase/FR declared fully accepted.

Next: E2 sandboxed extraction/source spans and correction revisions, E3 scoped retrieval, F contract analysis and cited summaries, G/H persistence, I/J workflow authority/timers/audit, L/M integrated security/recovery/acceptance. Real upload extraction remains gated by an approved configured malware scanner; none is currently configured. No push performed at this checkpoint: full status/report must be shown and explicit publication authorization obtained under AGENTS.

Publication follow-up: after the full status/validation report was shown, owner explicitly authorized **Push and open PR**. Commits `9327f9b` and `9e9e01e` pushed normally to the authorized continuation branch; PR #13 targets development. No merge/main promotion/self-approval. Test container/network cleanup passed; unrelated working-tree artifacts remain excluded. Latest remote CI/review must be checked on the evidence follow-up HEAD.

| Checkpoint | Status |
|---|---|
| A custody/report/discovery | Complete: preserved branch activation, isolated defaults/CI/runbooks, offline regression/frontend checks |
| B architecture/reuse | Complete: approved development baseline; domain/permission/state/provenance contracts and all 66 FR acceptance mappings |
| C identity | Backend verified; frontend/design acceptance deferred to user |
| D implementation | In progress: backend legal core and authorization |
| E-M implementation/validation | Not started; frontend K deferred to user |

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

## Phase C implementation / user-requested pause — 2026-10-06

RED checkpoint `770c834` is committed. Implementation now uses the PDF product name and legal backend service identity, paired strict frontend health validation, shared identity constants, neutral SVG assets, active metadata/package/manifest/title updates and honest landing/auth/shell/help copy. Existing industrial screens are labelled legacy; terms DOCX/version/text/acknowledgements and receipts remain unchanged. README/PRODUCT/DESIGN/surface brief updated; original assets and motion/media infrastructure preserved.

Files: backend main/init/health and foundation expectation; frontend identity module, three neutral branding SVGs, index/package/locks/manifest, UI logo/status titles, shell/routes/navigation/page descriptions, auth layout, landing model/page/CSS, resources/help/terms notices, root/backend README, PRODUCT/DESIGN and approved surface brief. No domain model/migration/authorization rewrite or existing storage rename.

Latest GREEN evidence: backend identity 2/2; custody 6/6; focused frontend identity/API 14/14; full frontend 44/44; lint 0 errors/2 existing warnings; build passed (159 modules). Master PDF and terms hashes unchanged. Native backend import remains blocked by Application Control on `ujson`, explicitly not worked around.

The user stopped the session immediately after frontend preview startup, before any browser inspection. Only temporary preview PID 35516 and its children were stopped successfully. No DB/model service started; no unrelated process stopped. **Phase C is not complete.** Remaining browser/detector/final diff checks and D-M build work are recorded in `SESSION_RESUME.md`. Save current green implementation as an honest partial pause checkpoint; do not amend history, push, or advance the phase on pause.

## Phase C resumed — 2026-10-06

User requested continuation while pause-checkpoint preparation was ongoing. Read the saved handoff and verified root/origin/branch/common Git metadata/status/guide. Latest committed HEAD is `770c834`; no pause commit exists, and current green implementation remains uncommitted. Original temporary preview is stopped. Resume only browser/final checks with mocked API; do not rerun unchanged broad suites or start live backend/DB/model services. A coherent completion commit will include the handoff and accurate pause/resume history.

## Backend-only scope and Phase D start — 2026-10-06

User explicitly requested no further frontend/landing work and will handle it later. Existing frontend changes remain preserved and outside the backend checkpoint. C backend identity reviewed; frontend C/K acceptance is deferred, not declared complete. D entry now proceeds under that explicit scope change.

Bounded mocked browser observations before steering: landing/login/terms/help shell loaded at desktop/mobile sizes, neutral images loaded, reduced-motion landing fallback and skip-link worked; stable layouts had no horizontal overflow. Mock-only probes are not real authentication/backend acceptance. A generic `{}` dashboard mock produced a legacy dashboard rendering error during an unintended authenticated redirect; no dashboard acceptance claimed and no frontend fix attempted. No bundled mechanical detector found; bounded DOM checks found no missing image alts/unlabelled login inputs/unnamed help-shell buttons. Existing frontend automated evidence is retained without rerunning unchanged suites.

D current scope: reuse existing UUID/auth/audit conventions for organization/workspace/membership/matter/document policy, additive migration after actual head, backend scoped authorization and runnable isolation checks. First inspect model registration, auth callers, migrations and disposable validation; no private DB/model access.

User explicitly approved isolated tests: a dedicated disposable PostgreSQL container and bounded backend test runtime, synthetic data only. New legal-core test Compose project uses no host ports/persistent volumes, an internal network, scoped read-only source mounts (no private `.env`/data/models), and model/vector targets at unused loopback port 9. This approval does not authorize touching private resources, model execution, deployment or push.

## Initial Phase D milestone and three-team handoff — 2026-10-06

Delivered seven scope tables, centralized DB-derived role/clearance/matter/document-grant policy, two session/terms-protected `/v1/workspaces` metadata APIs, denied-access audit vocabulary and migrations 0019/0020. Existing UUID/auth/terms/audit envelopes reused. Legacy unmapped records have no legal API access; no intake/provisioning/release endpoint is enabled. Reviewer permission checks are prerequisites, not final release authority. Review corrected no-store/referrer headers on early origin denials.

Files: new `app/db/models/legal_scope.py`, `app/services/legal_policy.py`, `app/schemas/legal_scope.py`, `app/api/routes/legal_scope.py`; model/router registration, audit vocabulary, main middleware/foundation expectations; migrations 0019/0020; `scripts/validate_legal_migrations.py`; four `test_legal_scope*` modules; dedicated legal-core Dockerfile/Compose; team allocation and PR baseline workflow. Full D remains open for audited provisioning, explicit legacy ownership/quarantine, tenant dedupe and legacy content/retrieval/review/audit isolation.

Actual verification: 27/27 scoped tests (SQLite/PostgreSQL policy, bounded real-session API, migration/target guard); fresh and 0018-to-head upgrades, Alembic parity/idempotency, synthetic legacy source/version hashes, audit hash/chain and existing trigger definitions preserved. Initial Settings failure for absent MODEL_NAME fixed with explicit fixture tag; model/vector endpoints stay loopback port 9 and no inference occurs. Confirming checks are required after the final header/negative-insert review edits.

User requests three human teammate workstreams without skipped requirements. `TEAM_WORK_ALLOCATION.md`: Part 1 remaining D/E/F/documents/contracts/search; Part 2 G/H/regulatory/compliance; Part 3 I/J/L/M/workflows/security/recovery. Frontend/K owner-managed; final frontend acceptance remains required. GitHub handles not supplied.

Authorized GitHub repository: PUBLIC, viewer ADMIN, default main at d95dfc3, unprotected, zero open PRs at inspection. Authorized fetch found no merge base with migration history; no unrelated-history merge/reset/force push/main overwrite attempted. Publish the reviewed development base after current report/confirmation; main promotion requires reconciliation. New read-only GitHub-hosted baseline PR checks are automated; assistant review remains session-bound.

Confirmed publication approval after report: user chose publishing the partial team base, including already-tested identity files and enabling main/development PR protection. No new frontend work. Final checks passed: 27 scoped tests, fresh/0018 migrations, focused frontend identity/API 14, backend identity 2, custody 6. Next: stage intended checkpoint paths only, preserve unrelated work, commit/push normal development branch, verify CI and create three work issues/branches. No main promotion yet.

Published checkpoint `87cd2bd` (`Add scoped legal backend and three-team build handoff`) contains 57 intended paths; unrelated benchmark/nested/private/local artifacts stayed excluded. Normal push created the development base; main unchanged. GitHub baseline CI run `37491748786` completed successfully (`legal-core`). Team tickets: Part 1 #1, Part 2 #3, Part 3 #2; usernames not supplied, assignment slots explicit. Dedicated disposable PostgreSQL container/network removed successfully after checks; no private/shared service stopped. Final handoff evidence commit and team branch/protection verification follow; no unrelated-history merge or completed D claim.

Remote handoff verified: evidence commit `496f903` pushed; CI run `37492025870` SUCCESS. All three team branches created at 496f903. Main/development PR protection enabled and read back: strict legal-core check, one approval/last-push independence, stale dismissal, resolved conversations, admins enforced, no force pushes/deletions. Main code still d95dfc3. No teammate PRs yet. Remaining integration starts with receiving contributor handles/PRs and reviewing full diffs; no unattended AI monitoring. This final settings-evidence change is documentation only and must use a review PR now that the integration branch is protected.

Opened protected handoff-evidence PR #4 from team/handoff-review-evidence. Baseline CI passed on push/PR; it correctly remains review-required. Inspection found checkout post-cleanup warning on the inherited quarantined gitlink. Minimal workflow correction replaces checkout-action recursion/credential cleanup with explicit authorized public fetch/checkout, non-recursive and credential-free. Nested repository bytes/metadata are unchanged; remote confirmation follows. Shared base stays 496f903 until independently reviewed integration.

## Consolidated Claude continuation — 2026-10-06

User requested one reference file covering conversation/build/state/team/repository/commits/PR review and a Claude prompt. Added CLAUDE_HANDOFF with reading index, actual approvals/state/evidence/paths, remaining phases, human assignments, commit/fetch/review/fix/merge procedure and next actions. Replaced accumulating SESSION_RESUME with a current pointer; preserved old content in SESSION_RESUME_HISTORY_2026-10-06. AGENTS links the consolidation. Synchronized actual head 0020, automatic baseline/manual full CI, published/protected branches and user-owned frontend. No product code/PDF/terms changes.

Before writing: local review branch 9cd84af, shared base 496f903, protected main d95dfc3 unchanged, team branches at base; PR #4 OPEN/REVIEW_REQUIRED with both corrected push/PR CI SUCCESS (37492888207/37492895455). Issues #1/#3/#2 await actual handles. No teammate implementation PRs yet. Update only existing handoff PR; no new phase, main promotion, bypass or unattended monitor. Document diff/link/whitespace checks and newest commit/CI are recorded in the PR; preserve unrelated user artifacts.

## Team assignment and main-flow request — 2026-10-06

Owner delegated slot choice to the integrator and asked that accepted teammate work regularly reach `main` under central integrator review. Mapped by invitation order: Part 1 #1 Harsha-code-per, Part 2 #3 Sanjjith27, Part 3 #2 Cholan-kinnera. All three write invitations are pending; GitHub returns 404 for assigning pending invitees, so assignment comments were posted (issue comments 6020833889/6020834374/6020834824) and assignees follow acceptance. Cholan-kinnera asked to review PR #4. Verified before change: HEAD fc09fc5 = PR #4 head, both CI runs SUCCESS, no reviews; dev 496f903, main d95dfc3, team branches at 496f903, no teammate commits. `main` is a 2-commit snapshot with no merge base (84 main-only paths incl. vendored claudex-loop and data/.phase_e_* staging); a reconciliation plan was presented for owner approval. No merge/promotion performed. Docs only.

Owner selected the one-time join. Built merge `b451860` with `git commit-tree` (no checkout; user working tree untouched): parents main `d95dfc3` + dev `496f903`, tree identical to `496f903`, 70 commits, main verified ancestor. Pushed `reconcile/main-join`; opened PR #5 into main. Requires legal-core + independent teammate approval; no bypass. After merge, regular reviewed dev→main promotion PRs per integrated checkpoint. Not a phase/FR acceptance.

Owner reported Sanjjith27 unavailable and assigned Part 2 to the integrator with overall repository management. Issue #3 assigned to the owner account. Built the deterministic G/H core in a separate temp worktree on `team/2-regulatory-compliance` (user working tree untouched): `regulatory_versions.py`, `compliance_assessment.py`, 14 synthetic tests, CI step; commit `e670f65`, PR #6 to development. 14/14 local and in the legal-core image; three mutations caught. No migration (0022 waits for 0021). PR #6 needs approval from Harsha-code-per or Cholan-kinnera; invitations still pending.

## All workstreams to integrator — 2026-10-06

Owner reported all three teammates unavailable and asked the integrator to complete the remaining backend work and commit. Owner authorized setting required approvals to 0 on main/development (CI legal-core, strict, conversations, admin enforcement, no force/delete kept); applied and read back. Merged #4 and #6 into development (32c3670) and #5 join into main (a85494d). Creating the dev->main promotion PR was blocked by the session permission classifier; left for the owner. D provisioning slice: migration 0021, legal_provisioning service, operator CLI, 14 tests; 41/41 scoped + migration validator pass on disposable PostgreSQL. Next D: workspace-scoped dedupe and legacy route isolation.

D completed for development exit checks: PR #7 merged (provisioning, 0021). Follow-up 0022 workspace-scoped dedupe, legacy guards on ten industrial sites, mapped-version stamping and root-audit exclusion; 57/57 scoped tests and validator pass; a surviving mutation exposed a missing case, test added. Industrial suites not executable in available runtimes (recorded). Next: Phase E secure intake on scoped versions.

## Parts 1/2 to integrator, Part 3 with Cholan-kinnera — 2026-10-06

Owner screenshot: integrator does Part 1 (#1) and Part 2 (#3); Cholan-kinnera (invitation accepted) owns Part 3 (#2) and asked to merge development into team/3 before work. Issues assigned. Development -> main promotion attempt denied again by the session permission classifier; owner action required. E1 secure intake built (0023); 76/76 scoped tests and validator pass. Migration allocation: integrator took 0023; Part 3 must request the next revision in its PR.

Part 3 reassigned to an owner-run Codex agent (Cholan-kinnera unavailable). team/3 fast-forwarded to development 1e51029; isolated worktree prepared for the agent; issue #2 reassigned. E1 merged as PR #10. Migration rule: agents set down_revision to the current development head when adding a revision; the integrator re-chains at merge if both sides added one.
