# Legal & Regulatory Assurance Platform

## Application explanation, existing-codebase assessment, and complete build plan

**Assessment date:** 9 October 2026

**Document type:** owner-facing technical explanation and delivery roadmap

**Current stage:** partial Phase E document intelligence; foundation established; business workflows and operational-pilot acceptance remain unfinished

**Local checkpoint:** b3b6a71; migration source head 0025

**Authority:** the unchanged Legal_Regulatory_Assurance_Platform_Master_Report.pdf, approved domain contracts, and living migration guide

This report explains what we are building, why we are adapting a prebuilt application, what actually exists now, what remains, and how to finish it without dropping requirements. It is a dated assessment and proposed delivery schedule. It does not replace the master specification, authorize implementation/deployment/publication, or declare planned work delivered.

## 1. Executive answer: what is this application?

We are building a new **Legal & Regulatory Assurance Platform** by adapting an existing private/local-AI industrial workbench in this authorized repository. The new product is for legal teams, compliance teams, business owners, and auditors. It connects contract analysis, document summarization, and compliance monitoring into one persistent, evidence-backed workflow.

The application should help answer: What does this contract or regulation require? Which exact source supports that statement? Does it apply to our business? Which control addresses it? What evidence supports the assessment? Who must act and by when? What changed? Who reviewed the interpretation? Can we reconstruct the decision later?

A completed journey is: import a permitted document; preserve its original/version/hash; parse and verify its text; propose clauses, findings, summaries, and obligations; obtain an independent human decision; persist accepted obligations or requirements; connect controls and evidence; monitor expiry, deadlines, and source changes; create tasks and remediation; reconstruct the outcome through audit history.

**We are not starting from an empty codebase.** We are retaining mature platform infrastructure and adding/replacing domain-specific layers. The existing workbench's industrial workflows do not, by themselves, satisfy legal-domain requirements. Rebranding an industrial dashboard or routing a PDF to an LLM is not the completed new product.

Current conclusion: architecture/contracts and substantial access/source foundations exist. The latest local implementation reaches secure intake, native extraction, bounded English OCR, and transcription correction review. Contract intelligence, grounded summaries, persistent regulatory/compliance workflows, legal obligations/timers, remediation, integrated frontend journeys, and final recovery/security/quality acceptance remain.

## 2. Why build this new application?

### 2.1 The problem being solved

Legal/compliance work is often spread across PDFs, contracts, policies, spreadsheets, email, evidence folders, and ticketing systems. A document can be available but its duties can still be missed. A compliance conclusion can appear current even after evidence expires or a regulation changes. An AI summary can sound credible while omitting a material condition or citing the wrong version.

The product therefore treats a document as an immutable evidence source and a workflow starting point. The valuable output is not only text: it is a reviewed, source-linked obligation, requirement, assessment, finding, task, or decision with an accountable owner and persistent history.

### 2.2 The three mandatory pillars

| Pillar | What the completed application must do | Observable proof |
|---|---|---|
| Contract analysis | Identify clauses, parties, terms, rights/duties/prohibitions, dates, renewals/notices, deviations, missing clauses, conflicts, and version changes | Reviewer opens the exact source, accepts a finding, and creates an owned obligation |
| Document summarization | Produce audience/profile-specific summaries and cross-document synthesis without inventing or omitting material meaning | Every substantive claim cites authorized spans; coverage and uncertainty are visible; approved output exports |
| Compliance monitoring | Connect approved requirements to policies, controls, evidence, findings, owners, and time | Evidence expiry or source/control change invalidates current status and produces explainable follow-up work |

### 2.3 Intended users

- Legal counsel/contract reviewers: review clauses, compare playbooks, approve interpretations/findings, and inspect source versions.
- Compliance officers: govern regulatory imports/applicability, map controls, accept evidence, review assessments, and approve remediation.
- Business owners: own obligations/tasks, supply evidence, and submit completion; they do not independently approve material legal interpretation or remediation closure.
- Auditors: inspect granted sources, timelines, snapshots, and evidence packs with read-only authority; separate observations do not rewrite decisions.
- Workspace administrators: provision users and configuration without inherent access to all confidential documents or self-granted material review authority.
- Risk/security/executive users: scoped risk acceptance, security operations, and permitted aggregate views as the operating model expands.

### 2.4 The compliance digital twin

The digital twin is a persistent relationship model, initially implemented with PostgreSQL relations rather than a new graph database. A regulation version links to requirement versions; requirements link to controls/policies/evidence; assessments link to findings and decisions. Contract versions link to clauses, accepted obligations, deadlines, and owners. Changes traverse those relationships and mark dependent current conclusions stale or awaiting review.

Historical decisions remain intact. A changed source does not rewrite the earlier legal basis. This gives the product temporal reasoning, change impact, evidence freshness, and audit replay rather than a static compliance percentage.

## 3. The prebuilt application we are reusing

### 3.1 What the original application was

The inherited application is an industrial/operational private-AI workbench, historically branded as a Sovereign workbench. Its domains include maintenance, equipment/sensors, safety, process optimization, P&ID intelligence, shift handover, operator notes, and environmental operations. It also contains generic AI query, controlled knowledge, review, execution, audit, authentication, and integration infrastructure.

Those historical names identify the origin of the code; they do not authorize operations in old repositories or worktrees. All application work belongs to this repository: https://github.com/loktrishal-05/legal-compliance-regulatory-workbench.git.

### 3.2 Why reuse it instead of rebuilding everything?

The prebuilt system already contains useful, nontrivial infrastructure: cookie sessions and recovery; typed FastAPI APIs; PostgreSQL migrations; document versions; local model gateway; hybrid retrieval; checkpoint/execution primitives; independent review/release patterns; append-only audit chains; evidence manifests; frontend shell/session/state components; and operational scripts/tests.

Reusing these components reduces the need to write a second authentication system, second audit chain, second model client, second UI shell, or second basic retrieval implementation. The migration must still inspect callers and assumptions because industrial source types, global access patterns, specialist prompts, and industrial evidence sufficiency are not automatically correct for legal work.

### 3.3 Transformation map

| Existing component/domain | New application use | Required adaptation |
|---|---|---|
| Industrial query/router/specialist agents | Legal source-grounded analysis and synthesis | Legal schemas, task profiles, scoped tools, evidence policy, uncertainty, and evaluation |
| Maintenance/safety/optimization outputs | Contract findings and compliance proposals | New domain entities; do not relabel industrial answers |
| PDF/P&ID extraction and source inspectors | Contract/regulation/evidence parsing and viewers | Exact legal structure, DOCX/images/email formats, OCR corrections, quality, authorization |
| Global knowledge retrieval | Authorized legal hybrid search | Workspace/matter/document ACLs, classification, authority, version/effectivity, revocation |
| Generic immutable revision/review/release | Legal finding/obligation/applicability/evidence decisions | Exact legal target binding, independent authority, request-changes/escalation, concurrent revoke/release |
| Existing audit chain and manifests | Scoped legal audit/replay/export | Legal vocabulary, source/model/rule lineage, sufficient citations, point-in-time evidence |
| Checkpoints/durable executions/receipts | Document jobs and legal workflow recovery | Actual async dispatch, worker leases, restart/retry, durable timers/outbox |
| Existing shell/dashboard/review/knowledge/admin | Evidence-first legal frontend | Real legal APIs, legal navigation, source jumps, permitted aggregates, accessible journeys |
| Industrial operational compliance | Requirement-control-evidence assurance | Separate legal model, six explainable states, freshness/drift, remediation |

### 3.4 What is preserved and what is replaced?

Preserve generic IDs, applied migrations, historical source hashes, audit envelopes, immutable decisions, authentication history, terms receipts, reusable security checks, UI shell patterns, and historical benchmark evidence. Add legal schemas/migrations forward rather than destructively replacing old tables.

Replace active industrial routing/prompts/navigation only after tracing callers, separating generic utilities, validating legal replacements, and reviewing the transition. Old data and industrial tests remain historical/reference material. Never alter frozen expected answers to make legal functionality appear accepted.

No approved first-slice need exists for a Next.js rewrite, microservice split, graph database, Kubernetes deployment, or hosted-AI switch. The approved development stack remains React/Vite, FastAPI, PostgreSQL, Qdrant, LangGraph, and private/local AI. Existing durability primitives should be evaluated before introducing another workflow engine; required durability itself cannot be omitted.

## 4. What is inside the codebase right now?

### 4.1 Repository inventory

| Location | Present purpose | Status interpretation |
|---|---|---|
| backend/app/main.py and api/ | FastAPI startup/middleware, auth dependencies, legacy and legal routes | API registration exists; full startup acceptance is still a separate test |
| backend/app/db/models/ | Identity, documents, agents/executions, immutable review/audit/evidence, knowledge, industrial records, new legal scope/extraction/correction | Existing ORM infrastructure plus additive legal models; major legal business entities remain absent |
| backend/app/schemas/ | Pydantic input/output contracts | Legal scope, extraction, and correction schemas exist; future domain contracts require implementation |
| backend/app/services/ | Auth, extraction/retrieval, gateway, governance, audit, executions, industrial services, legal services | Mixed reusable/legacy/new application source |
| backend/app/agents/, nodes/, prompts/, tools/ | Orchestration, specialist routing, state/tool/evidence machinery | Predominantly inherited industrial reasoning; legal routing/profile migration remains |
| backend/alembic/versions/ | Forward schema/history evolution | Local source chain contains 0001 through new 0025; not evidence of a private database's applied head |
| backend/tests/ and scripts/ | Unit/integration/security/fixture checks, provisioning, migration validation, backup and evaluation utilities | Scoped legal acceptance exists; full product suite and recovery remain |
| frontend/src/app/ | Routes, AppShell, session, navigation | Existing shell is retained; legal workflow frontend is not accepted |
| frontend/src/features/, components/, services/ | Auth/landing/resources/features, reusable UI, API clients | Existing UI and legacy operational surfaces, with product identity changes |
| infra/ | Compose profiles, Dockerfiles, scanner config, offline/test/runtime launch support | Isolated configuration/test resources; production deployment not accepted |
| benchmark/ | Industrial cases/corpus/harness/results | Historical evidence; not a legal benchmark |
| data/ and models/ | Local/private artifacts, raw/processed data, indexes/logs, model resources | Presence does not prove ownership, permission, health, or current execution |
| docs/ | Master specification, living plan, contracts, FR registry, handoff, validation, audits/runbooks | Mix of current checkpoint evidence and explicitly historical snapshots |
| claudex-loop/, historical worktrees, incoming archives | Auxiliary tooling and historical/reference material | Not application implementation targets; preserve boundaries |

This is an architectural/source inventory, not certification of every private file, binary, archived report, or external service. Private resources were not probed for this report.

### 4.2 Legacy API and frontend surfaces that still exist

backend/app/api/router.py continues to register health, query, agents, approvals, auth, documents, audit, sovereignty, knowledge, P&ID, maintenance, sensors, models, verified knowledge, knowledge packs, operational, product, and executions routers. It also registers the new legal_scope router. Thus the repository still contains an industrial application backbone alongside incremental legal additions.

frontend/src/app/routes.jsx still defines dashboard, AI workspace, voice, agents, P&ID, maintenance/sensors, operations, knowledge/gaps, approvals, executions, audit, private-runtime/sovereignty, resources/help, admin, and profile routes. Authentication/recovery and terms gates remain. Those routes are not a finished contracts/regulatory/compliance/obligations frontend.

### 4.3 Existing platform behavior worth reusing

- Authentication: Argon2 password hashing, server-side opaque sessions, HttpOnly cookies, account/session revocation, signup/recovery/verification, terms checks, and optional identity/email adapters. These do not satisfy complete enterprise SSO/MFA/step-up requirements by themselves.
- Retrieval: dense/sparse vectors, reciprocal-rank fusion, BGE embeddings/reranking, indexed-version filtering, and stored citation metadata. Industrial payloads and global eligibility must become legal-scope-aware before use with a legal corpus.
- Gateway: private/local endpoint policy, structured output, bounded schema repair, allowlisted tools, profiles, and health/status interfaces. Existing source implements Ollama integration; historical vLLM adapter is a placeholder, not a delivered alternative.
- Governance: immutable revisions, hashes, decisions, self-approval denial, release policy/evidence rechecks, and transactional audit. Legal target/state expansion remains.
- Audit: hash-linked append/verification, chain-head locking, immutable history, and manifests. Local hash chains are tamper-evident controls, not a claim of tamper-proof independent archiving.
- Durability: persisted execution/checkpoint/operation receipts. Existing synchronous start/resume is not proof of a general document queue or durable legal calendar.
- Frontend: lazy routes, server-derived session principal, terms/role gates, reusable loading/error/empty states, source/review patterns, and responsive shell.

## 5. What has actually been built for the new application?

### 5.1 A/B/C: safe foundation and identity

Source custody and isolated defaults/CI/runbooks were established. The master specification was preserved unchanged. Architecture/reuse/domain contracts and all 66 functional requirements were mapped. Product/backend health identity and paired saved frontend identity were tested. Frontend design/browser/product acceptance remains owner-managed.

Legal configuration defaults distinguish candidate DB/vector/backend/frontend/model resources from inherited industrial resources. Documented candidate ports include DB 55432, Qdrant 16333/16334, backend 18000, frontend 15173, and a dedicated model candidate 21434. These are configuration intent, not proof that private/live instances are provisioned or accepted.

### 5.2 D: scope, permission, and compatibility foundation

New legal_scope models represent Organization, Workspace, WorkspaceMembership, Matter, MatterAccess, LegalDocumentScope, and DocumentAccess. legal_policy.py resolves active server-owned identity/terms/membership/role/clearance and document/matter grants. Workspace administration is not inherent confidential-content access.

legal_provisioning.py and the operator CLI support audited independent provisioning and explicit legacy mapping. Workspace-scoped deduplication and legal-version guards isolate inherited industrial read/index/reuse paths. Root audit exclusion helps prevent scoped legal events becoming visible through a global legacy view.

Migrations 0019-0022 add scope/policy/audit/tenant-version changes. D is recorded complete for its development exit checks. Full historical industrial regression could not run in available runtimes; that gap remains visible.

### 5.3 E1: secure intake and scanner increments

legal_intake.py accepts bounded authorized PDF/DOCX/TXT bytes. It checks format, empty/oversize input, dangerous/malformed XML, archive ambiguity/compression/size, macros, active/external PDF/DOCX content, and source lineage. Rejections are audited without storing rejected bytes. Unsafe or unscanned input quarantines. Original storage is content-addressed per workspace and published create-only; existing originals are reverified rather than overwritten.

legal_malware.py implements optional local Unix-socket ClamAV INSTREAM scanning with bounded responses/deadline and exact clean-result handling. Scanner errors/detection/freshness failure quarantine. Current policy is rechecked after scanning before publication. An isolated digest-pinned ClamAV 1.5.4 profile and separate public-signature updater were tested; scanner has no network and the updater receives no confidential source content.

Remaining: approved real-application provisioning/update policy, exact per-upload loaded engine/signature snapshot, historical quarantine rescan/release, broader operational acceptance, quotas, concurrency recovery, parser isolation, and full format coverage. The real application's private scanner configuration is unchanged; uploads still default quarantine.

### 5.4 E2a: native extraction and exact sources

legal_extraction model/schema/service and legal_parser_worker.py provide bounded TXT/DOCX/PDF extraction. Immutable legal_extractions and legal_source_spans bind organization/workspace/document/version/source hash. Source APIs resolve exact quotes with Unicode offsets and reliable PDF page/region or DOCX part/paragraph locators. They do not invent DOCX page numbers.

Extraction checks permissions before source access and after expensive processing, verifies original bytes/hash on retry, and records failure state with audit. DOCX/PDF native layout remains needs_verification where appropriate. Migration 0024 introduces extraction/source storage and history protections.

Processing is still synchronous and resource-bounded. CPU/memory/output/deadline limits are development containment, not deployment-grade filesystem/network sandboxing or durable dispatch.

### 5.5 Bounded English OCR and correction decisions

The latest local checkpoint adds opt-in English PDF OCR using existing PyMuPDF and packaged public Tesseract data. Mixed-document native text is retained; source regions, method, offsets, and language-data digest remain bound to immutable lineage. Policy legal-ocr-v1 is separate from native extraction.

Current recorded OCR bounds: five image-bearing pages, 200 dpi, 8 million page/source-image pixels, 20 child CPU seconds, 30 wall seconds, and 768 MiB address-space limit. These are current development limits, not final product throughput/quality acceptance.

legal_correction model/schema/service/API and migration 0025 add immutable span-bound proposals, successor linkage, idempotency/conflict checks, and independent approve/reject decisions. The reviewer must have current scoped read/review permission plus required platform eligibility and cannot be the requester. Approval confirms transcription only: it does not approve legal meaning, rewrite original text, or silently clear OCR quality warnings.

Blank/unrecognized regions lacking a stored nonempty span cannot yet be manually transcribed through this workflow. Broader language/table/handwriting quality, larger documents, current corrected-text projection, original viewer integrity, frontend verification journeys, and async/sandbox acceptance remain.

### 5.6 G/H: deterministic logic, not persistent business modules

regulatory_versions.py provides effective-date selection, exact structural/text differences, and source freshness. Unknown/overlapping dates require verification; failed source checks are unavailable rather than no-change.

compliance_assessment.py provides versioned declarative rule checks, evidence currency, six explainable states, immutable result inputs, drift reasons, and workspace-bounded dependency traversal. Visible component counts exist; no invented scoring weights.

These functions operate over supplied inputs. Persistent source registry, regulatory versions/decisions, requirement/policy/control/evidence/finding models, domain APIs, review binding, scheduling, and UI remain unbuilt. They are useful starting points, not delivered continuous monitoring.

## 6. Current APIs, migrations, and delivery state

### 6.1 Legal routes present locally

All routes below begin with /v1/workspaces/{workspace_id}. They inherit server-side session/terms and object policy; client-supplied identity/role is not authoritative.

| Method | Relative path | Implemented purpose |
|---|---|---|
| GET | / | Workspace metadata; actual route is the workspace path without trailing suffix |
| GET | /documents/{document_id} | Authorized document metadata |
| POST | /documents | Raw-body bounded secure intake |
| POST | /documents/{document_id}/versions/{version_id}/extractions | Native extraction or configured opt-in OCR |
| GET | /documents/{document_id}/versions/{version_id}/spans/{span_id} | Authorized exact source span |
| POST | /documents/{document_id}/versions/{version_id}/spans/{span_id}/corrections | Immutable transcription proposal |
| POST | /documents/{document_id}/versions/{version_id}/corrections/{correction_id}/decisions | Independent transcription decision |
| GET | /documents/{document_id}/versions/{version_id}/corrections/{correction_id} | Authorized proposal/decision read |

Complete legal contract/regulatory/compliance/obligation/remediation/search/audit domain APIs remain to be built. Scope metadata/individual source reads also do not constitute complete list/search/source-download/admin UI APIs.

### 6.2 Additive legal migration chain

- 0019_legal_scope: organization/workspace/matter/document scope.
- 0020_legal_policy_audit: legal policy denial audit vocabulary.
- 0021_legal_provisioning_audit: audited provisioning vocabulary.
- 0022_legal_version_scope: workspace-qualified version/deduplication compatibility.
- 0023_legal_intake_audit: intake audit vocabulary.
- 0024_legal_extraction: immutable extraction/source spans.
- 0025_legal_corrections: immutable transcription proposals/independent decisions.

Future migrations must append after the actual agreed predecessor. Do not reuse proposed historical revision numbers or edit already-applied migrations. The local source head says nothing about a private database's applied state.

### 6.3 Verified branch/PR snapshot: 9 October 2026

| Reference | Verified head/status | What it means |
|---|---|---|
| Local integration/backend-continuation-20261007 | b3b6a71 | Latest scanner/OCR/correction checkpoint; source migration head 0025 |
| Remote continuation and PR #13 | 9763a81; OPEN; no reviews | Older native-source/documentation checkpoint; legal-core SUCCESS on this older head |
| Remote feat/legal-regulatory-platform-migration | b3dcf4f | Earlier accepted development integration; 0023 intake migration present |
| Remote main | 04d719f | Earlier application baseline plus README-only promotion; newer continuation backend is not integrated |

There are eight local commits after remote continuation 9763a81. The latest scanner/OCR/correction work is committed locally but unpublished. Do not interpret the earlier remote green CI as verification of those unpublished commits. main's advanced README is documentation visibility, not evidence that the corresponding later backend features are on main.

Unrelated benchmark modification, nested tooling changes, local review/browser artifacts, and private phase11 artifacts exist and must be preserved. This report performs no publication/integration or user-work cleanup.

## 7. Current evidence and what it does not prove

### 7.1 Recorded checkpoint evidence

| Evidence | Recorded result | Boundary |
|---|---|---|
| Latest scoped legal suite | 168/168 PASS, no skips | Bounded legal scope/auth/intake/source/OCR/correction/protocol/migration checks |
| Focused extraction/OCR suite | 38/38 PASS | Synthetic/public fixture checks and bounded child execution |
| Fresh and historical migrations | Fresh and 0018 to 0025 PASS | Disposable PostgreSQL only; parity/idempotency/history/immutability/self-review protection |
| Correction service coverage | 96% line coverage | Not branch or whole-application coverage |
| Parser worker coverage | 81% line coverage | Parent/direct-unit tracing; actual child also exercised separately |
| Isolated real scanner milestone | Seven engine checks plus one actual outage check PASS | Synthetic/harmless EICAR, clean formats, limits, and fail-closed HTTP behavior; not broad malware certification |
| Earlier frontend identity | 44 tests, lint/build recorded passing | Earlier saved identity/frontend evidence; not current legal E2E/WCAG acceptance |
| Remote PR legal-core | SUCCESS at 9763a81 | Older remote source, not local b3b6a71 |

Results above are taken from the dated validation report and checked against current source/Git references. This assessment did not rerun application tests, enable services/models, or reproduce private deployment behavior.

### 7.2 Remaining verification gaps

Full application/root-router runtime acceptance remains distinct from bounded-router tests. Native Windows imports encountered OS Application Control blocks on dependencies; some industrial suites lacked needed dependencies in the bounded Linux image. The remedy is an approved supported test environment, not disabling protection or disguising collection errors as passes.

No complete FR is accepted merely because a metadata API exists or baseline CI is green. The traceability registry still says no legal FR is fully accepted. There is no verified all-three-pillar journey, complete legal accuracy benchmark, operational enterprise identity, live private-model acceptance, complete frontend acceptance, recovery rehearsal, or achieved deployment SLO.

The inherited frozen benchmark readiness report mismatch remains an owner-reviewed issue; preserve historical benchmark integrity. Warnings/failures/mocks and unconfigured integrations must stay visible in final acceptance evidence.

## 8. Non-negotiable application contracts

### 8.1 Tenant and confidentiality contract

Resolve active account/session/terms, membership, workspace/matter/object ACL, classification, and operation permission on the server. Relationships need workspace-qualified foreign keys as well as service checks. Membership/admin status alone does not reveal all documents. Unknown/denied objects use consistent unavailable responses; counts, search, audit, exports, and model context cannot leak existence/content.

Workers carry originating actor/scope and reauthorize on execution/resume/release. Service accounts require explicit scopes. Public regulatory acquisition must not receive confidential user/model context. Logs, prompts/traces/checkpoints, memory, indexes, exports, and backups are all secondary-copy boundaries.

### 8.2 Evidence and authority contract

Original bytes and historic artifacts remain immutable. A replacement creates a new version. Citations bind document/version/hash/span/quote/locator/extraction quality; regulatory citations additionally identify authority and effective period. Validate stored evidence rather than trusting model-generated IDs.

Separate source facts/observations, interpretations, and recommendations. Schema validity or model confidence does not establish legal truth. Human review controls material conclusions, applicability, evidence acceptance, risk acceptance, and remediation closure. Correction approval is transcription-only.

### 8.3 Time, state, and reliability contract

Keep published/imported/effective/observed/decided times distinct. Unknown dates remain unknown. Deadline timezone/calendar/trigger/recurrence is human-confirmed; no guessed legal business-day convention. Jobs/timers/notifications use durable identities, leases/receipts, bounded retry, and dead-letter states.

Do not conflate received/processed/indexed source state with accepted legal meaning. Evidence/source/control change invalidates current projections with reasons and schedules review/re-evaluation; it preserves past decisions. Deterministic workflows and stored approved data must remain usable during model outage.

### 8.4 Six assessment states

- satisfied: all required components supported by accepted current sufficient evidence and approved applicable rules.
- partially_satisfied: some known components supported, others incomplete; gaps are explicit.
- unsatisfied: evidence demonstrates failure of an applicable approved rule; missing evidence alone is not violation.
- insufficient_evidence: required proof is missing, expired, invalid, or unavailable.
- not_applicable: authorized applicability decision exists with exact source/version/effectivity context.
- needs_review: ambiguity, conflict, material interpretation, or source-change impact awaits authorized decision.

Freshness and review dimensions remain visible alongside these states. No opaque AI-only score or fabricated green status.

## 9. Complete remaining build plan: sequence and method

This plan follows A-M and preserves all FR-001 through FR-066. Tasks below describe proposed delivery, not new approvals. Backend is integrator-owned under current recorded scope; frontend/landing is owner-managed. Independent human review remains an acceptance need even though GitHub configured required approvals are zero.

The estimates are person-days, including design/caller inspection, implementation, scoped tests, migration checks, review fixes, and synchronized evidence. A person-day is approximately eight working hours. Waiting for approval, hardware, licensed feeds, external reviewers, or provisioning is additional. See section 23 for totals and staffing scenarios.

Recommended dependency chain: existing checkpoint reconciliation -> remaining document processing/isolation -> authorized retrieval/source APIs -> contracts/summaries with minimum legal review -> persistent regulatory/compliance model -> obligations/timers/remediation/audit -> complete frontend journeys -> consolidated quality/security/pilot/recovery acceptance. Frontend, security fixtures, and pilot decisions can overlap once their contracts/predecessors are stable.

At each milestone: inspect implementation/callers; define failing or meaningful acceptance checks; make the smallest compatible implementation; validate fresh/history migrations if changed; review security/source/time/authority invariants; record actual evidence/blockers; checkpoint intended paths; publish/integrate only within explicit repository/PR authorization. A pause or plan change is not phase completion.

## 10. Step 0: reconcile, review, and integrate the local checkpoint

**Estimate:** 1-2 person-days. **Requirements:** publication/traceability process supporting all FRs. **Entry:** current authorized root and eight unpublished commits.

1. Compare all eight commits/full diff against remote continuation 9763a81 and verify dependency/migration history.
2. Reconcile stale top-level summaries with current A/B/C/D/E/G/H facts; preserve dated historic results.
3. Verify actual test/coverage/migration scope at b3b6a71 and reproduce any unresolved review findings in the isolated runtime.
4. Preserve unrelated benchmark/nested/private/untracked work; stage explicit intended paths only.
5. Show current validation/limitations and obtain publication authority where required.
6. Publish through PR #13, run CI on the actual latest head, obtain independent review, and resolve discussions.
7. Integrate accepted work into development and promote through normal reviewed development-to-main PRs; reconcile README branch availability wording.

**Exit evidence:** actual source, reports, CI, PR head, development, and main availability are accurately described. No force push, self-approval, review bypass, or private runtime migration is implied.

## 11. Step 1: complete secure documents, durable jobs, and parser isolation

**Estimate:** 8-12 person-days. **Phases:** E1/E2, supporting J/L/M. **Requirements:** FR-006..011, FR-002..004, FR-050/054/055, reliability/security NFRs.

### 11.1 Durable document processing

Reuse execution/receipt/transaction patterns. Persist job identity, actor/scope, source version/hash, operation/profile, state/progress, attempts, deadlines, lease/claim, safe failure code, next retry, and terminal/dead-letter status. Submission and durable dispatch state need transaction-safe coordination. Avoid using process memory or a fire-and-forget task as the authoritative queue.

API submits/returns job status; workers claim bounded work, verify original snapshot/current permission, execute isolated parsing/OCR, and persist immutable artifacts plus audit. Crash/restart reclaims expired work. Same-key retries must return the existing outcome or conflict on changed content, never duplicate a legal artifact. Permission revoked while queued or running must block release.

### 11.2 Production containment and scanner operations

Implement a verified deployment-grade parser boundary: non-root execution, restricted filesystem/input/output mounts, no private configuration/model/DB access, denied network, dropped privileges, resource/output/time limits, and safe artifact publication. Quotas/backpressure limit abusive parallel jobs and large inputs.

Finish per-upload engine/signature/time provenance. Approve signature freshness/update cadence, updater failure monitoring, scan limits, mount/socket ownership, and rescan/release policy. Rescanning quarantined bytes must verify original integrity, current grants, current scanner/policy, and auditable state transition; duplicate intake must not bypass this path.

### 11.3 Format, quality, correction, and storage completion

Add required images and approved email/export formats using explicit allowlists and immutable provenance. Complete classification/metadata/version semantics beyond duplicate hashing. Test polyglot/archive/malformed/oversized images, encrypted content, tables/headings/headers/footnotes, scanned/mixed PDFs, and safe rejection.

Design empty-region manual transcription anchored to original page/region even when no extracted text exists. Define reviewed corrected-text projection/artifact/version semantics so downstream analysis can use verified transcription without losing originals/previous decisions. Expand languages/large-document capability only against selected product requirements and quality fixtures; handwriting/table limits remain explicit until accepted.

Verify filesystem crash-durability, reconciliation/orphan handling, original viewer/download/release integrity, and the selected durable encrypted source-storage profile. Do not expose raw disk paths or enable sensitive intake before its gates pass.

**Checks:** worker kill before/after parsing/persistence, duplicate concurrent submissions/uploads, lease expiry, retries/dead letters, revoked actor, scanner stop/stale signatures, sandbox network/filesystem escape attempts, source tampering, empty-region corrections, exact locator preservation, audit rollback, and representative format quality.

**Exit:** permitted approved sources safely process, preserve lineage, recover from restart/retry, expose uncertainty, and remain quarantined/failed when prerequisites are unavailable. All E2 blockers have explicit evidence or approved bounded scope; none is silently waived.

## 12. Step 2: authorized retrieval, index cutover, and source APIs

**Estimate:** 6-10 person-days. **Phase:** E3 with F/K/L/M. **Requirements:** FR-002..004, FR-022/048/049/050/051, retrieval/integrity NFRs.

1. Define legal chunk/index schema: organization/workspace/document/version/hash/span, matter/classification, structure/quality, authority/jurisdiction/effective interval, parser/index schema versions.
2. Reuse dense/sparse/keyword/RRF/reranking components with server-derived eligible versions before context retrieval. Revalidate current access and metadata against authoritative DB records; stale index grants cannot authorize exposure.
3. Add permitted document/version lists, pagination/filtering, job state, source preview/download, span/correction views, and uniform unavailable responses required by the frontend.
4. Build source-viewer integrity/policy and exact page/section/quote/region jumps. Reviewed corrections remain visibly distinct from original transcription.
5. Provision an isolated legal collection, rebuild from immutable authoritative data, verify count/hash/ACL/citation parity, and implement reversible configuration cutover. Do not run destructive legacy promotion helpers as a rename.
6. Handle index/search outage with safe keyword/DB degradation where feasible and visible incomplete retrieval; do not fabricate an answer.

**Checks:** two-tenant identical content, restricted matter, clearance changes, revocation during retrieval/rerank/source/export, tampered payload IDs, old/new effective versions, citation quote correctness, index lag/outage, and rebuild/reindex rollback.

**Exit:** authorized users find permitted evidence and open exact sources; denied content never enters result counts, reranker/model context, or viewer output. Retrieval quality meets approved corpus thresholds.

## 13. Step 3: contract intelligence, summaries, and grounded assistant

**Estimate:** 15-22 person-days. **Phase:** F with E/I/J/K/L. **Requirements:** FR-012..025, FR-049..053/055/064/065.

### 13.1 Persistent contracts and legal analysis

Add Contract/ContractVersion/Party/Clause and analysis-run/revision records linked to exact document versions/spans. Do not merge parties globally by similar names. Store clause ordering/types, definitions, terms, dates, renewals/notices, governing-law proposals, profile/schema/model/prompt versions, and extraction quality.

Implement constrained structured proposals for duties/rights/prohibitions, actors, action, triggers, conditions, original deadline phrase, and uncertainty. Validate source IDs, quotes, scope, schema, output caps, and coverage. Model-supplied accepted states/roles/authority are rejected.

### 13.2 Governed playbooks, conflicts, and change

Persist approved versioned playbooks/templates/rules with owner, legal basis, jurisdiction/effectivity, and review. Compare clauses for deviations/unusual terms/internal conflicts. Missing-clause output must cite expected rule and inspected coverage; incomplete parsing cannot establish absence.

Provide basic source-linked cross-contract duty/deadline collisions with reviewer decisions and false-positive fixtures. Do not assume semantic similarity establishes incompatible legal meaning. Store exact redlines beside qualified semantic change summaries, preserving old/new sources and material additions/removals/conditions.

### 13.3 Summaries, Q&A, and memory

Implement executive/detailed/clause/risk/obligation/action/change profiles and audience transformation without changed meaning. Hierarchical summarization must preserve material duties, conditions, dates, limitations, and source coverage. Every substantive statement binds authorized stored spans.

Cross-document synthesis retains per-document/version citations and handles contradictory sources. Authorized assistant retrieval binds authority/effective period and separates source fact/observation/interpretation/recommendation. Weak/conflicting/unsupported evidence yields qualified output/refusal/needs-review, not a confident invented answer.

Conversation memory is workspace/matter-scoped with approved retention/revocation/hold behavior. It supports continuity, never legal truth. Model outage returns visible queued/failed/degraded states while accepted records and deterministic workflows continue.

### 13.4 Review, exports, and AI acceptance

Implement minimum exact-revision independent legal review alongside this step using existing immutable primitives. Unreviewed/rejected findings cannot create accepted obligations/reminders. Persist analysis/summary provenance and audit atomically. Export only permitted approved summaries to PDF/DOCX/structured JSON with source/version/review manifest and parity checks.

Reuse private gateway with approved legal profiles/data classification/residency, bounded schema retries, local-only permitted endpoints, and no confidential hosted fallback. Model/profile changes need evaluated approval. Actual local-model evaluation requires explicit runtime authorization, selected hardware, corpus, and thresholds.

**Checks:** clause/field/obligation precision-recall, exact citations, missing actors/timezones/conditions, incomplete parsing, summary omission/factuality across profiles, forged spans, unsupported output refusal, conflicts/redline materiality, denied documents/memory/exports, self-approval, retries, model outage, prompt injection, and approval-to-obligation idempotency.

**Exit:** all three source-grounded contract/summary/Q&A workflows are real persistent proposals with independent acceptance, evidence coverage, and truthful uncertainty; accepted obligations can hand off to I.

## 14. Step 4: persistent regulatory intelligence

**Estimate:** 8-12 person-days. **Phase:** G with E/H/I/J/L. **Requirements:** FR-026..032/056/064.

Add governed RegulatorySource/Document/Version/Change/ApplicabilityDecision models and scoped APIs. Source registry records authority tier, trust/approval, owner, jurisdiction, import/fetch policy, provenance, last-success/failure/check freshness, and approval history. Public availability alone does not establish legal authority/applicability.

Manual approved import is the first acquisition path. Preserve exact immutable source/hash/spans, publication/import/effective times, amendments and supersession. Reuse as-of/diff/freshness functions over persisted versions. Unknown/overlap is visible needs-verification; newer import does not imply earlier effectivity.

Persist exact structure/text changes beside grounded semantic proposals. Require independent human applicability/materiality decisions. Map accepted requirements/changes to jurisdictions, entities, products, and business units using permitted same-workspace links. Watchlists and alerts expose manual freshness honestly; an unconfigured feed is not live monitoring.

Accepted change campaigns identify affected requirements/contracts/policies/controls/evidence/owners and persist review/re-evaluation/task events. They do not silently rewrite obligations or declare universal applicability.

**Checks:** unauthorized source promotion/import, exact authority/version lineage, effective interval boundaries, unknown dates, failed checks versus no-change, structural reorder/add/remove, semantic-source grounding, concurrent decisions, mapping scope, watchlist freshness, and restart-safe impact campaign idempotency.

**Exit:** an approved new source version produces a reproducible diff, human applicability decision, and permitted affected-object workflow.

## 15. Step 5: persistent compliance assurance and digital twin

**Estimate:** 10-15 person-days. **Phase:** H with G/I/J/K/L. **Requirements:** FR-031/033..040/043/052/064.

Add distinct Requirement/interpretation revisions, Policy/PolicyVersion, Control, Evidence/EvidenceVersion, Assessment snapshots, Finding/FindingRevision, and tenant-qualified mappings. Retain source/version/effectivity, owners, accepted evidence decisions, and rule/profile configuration. Do not compress these into a single generic JSON status field.

Persist approved deterministic rule versions and execute explicit conditions without LLM calls. Grounded AI-assisted interpretation remains provisional and reviewable. Bind every assessment to frozen evidence/rule/applicability inputs with reasons and sufficient citations. Current review/freshness state is separate from historic result.

Implement evidence expiry/replacement/supersession and drift from source/control/contract change. Invalidate current projections and schedule re-evaluation without deleting prior snapshots. Persist relational impact traversal and visible affected-component paths. Provide explainable component status/scoring with approved weights/missing-evidence treatment, never guessed percentages.

Accepted findings hand off idempotently to remediation/tasks; unknown applicability and conflicting evidence route to review. Missing evidence is insufficient proof, not automatic violation. Not-applicable requires an authorized exact-context decision.

**Checks:** all six states, empty/ambiguous/conflicting evidence, accepted versus proposed evidence, expiry/future observation, type-incompatible rules, cross-workspace FKs, source/control drift, historical/current divergence, model proposal authority denial, approved scoring transparency, and audit rollback.

**Exit:** a user imports a requirement, maps controls, attaches/accepts evidence, receives a defensible assessment, and observes current state change when evidence or source inputs change.

## 16. Step 6: obligations, calendars, tasks, and monitoring

**Estimate:** 10-15 person-days. **Phase:** I with F/G/H/J/M. **Requirements:** FR-019/032/038/039/042/045; supporting FR-044/047/063.

Persist accepted obligations independently of proposed extracted obligations. Retain source/review identity, actor/action/conditions, owner, trigger, original date phrase, confirmed timezone/normalized date, notice window, recurrence/calendar policy version, and status. A reviewer must confirm ambiguous legal date semantics; an LLM is not the scheduler.

Implement durable deadline occurrences, event/outbox coordination, dispatch claims, idempotent receipts, reminders/escalations, in-app notifications, read state, and bounded retries/dead letters. Scan due persisted work after restart and handle clock/lease/concurrency correctly. External email/ticket delivery is explicit configured adapter work; unavailable delivery cannot erase the authoritative in-app notification.

Add owner reassignment, task dependencies/cycle denial, evidence requests, overdue state, and approved trigger changes. A changed contract/source creates impact review rather than silently cancelling accepted duties. Keep timers functional during model outage and visible to permitted users only.

**Checks:** DST/ambiguous local time/date-only/business days/leap years/recurrence, missing year/timezone, duplicate events/worker claims, kill before/after receipt, downtime catch-up, no lost timer, reassignment/current grants, task cycles, escalation policy, provider outage, and confidential recipient restrictions.

**Exit:** accepted obligations survive restart and produce accountable, explainable tasks/alerts without duplicate authoritative effects.

## 17. Step 7: legal governance, remediation, and audit/reporting

**Estimate:** 10-15 person-days. **Phase:** J with F/G/H/I/K/L/M. **Requirements:** FR-041/043/044/054..059; extension FR-046/060.

Extend immutable review primitives for exact legal target/revision approve/reject/request-changes/escalation. Requests for changes create successors; escalation does not approve. Bind decisions to source/evidence/analysis hashes, source versions, model/prompt/rule/profile/policy references, and rationale. Validate independence/current assignments under concurrent decisions/revocation/release.

Accepted findings create scoped remediation tasks idempotently. Task progress is not authoritative closure. Require closure evidence, retest where required, independent decision, and reopening after failed retest/drift. Add scoped comments/mentions/attachments with confidential recipient validation and append-only decision history.

Expand constrained audit vocabulary through forward migrations, keeping old envelopes/hash compatibility. Add workspace/matter/object-filtered audit queries, recorded-versus-effective historical snapshots, exact analysis/decision replay, source integrity checks, evidence packs, and JSON findings/basic audit exports. Exports freeze approved source/evidence/decision manifests and cannot include denied objects or unapproved conclusions.

**Checks:** self-decision/escalation bypass, changed source after review, concurrent revoke/release, same-key changed-content retry, rollback with audit failure, remediation close/retest/reopen, unauthorized comment/attachment/mention, snapshot as-of semantics, audit tampering/replay, and export content/permission parity.

**Exit:** an auditor reconstructs why a material conclusion was accepted, what evidence/version/rule/model was used, who decided, what task followed, and how closure was verified. Minimum review is built earlier; this step completes cross-domain governance/reporting.

## 18. Step 8: complete the legal frontend

**Estimate:** 20-30 person-days. **Phase:** K and deferred C acceptance. **Owner:** application owner under current scope. **Requirements:** all user-facing FRs; especially FR-011/013/020..025/037/044/047/050/052/057..059.

Retain React/Vite shell, server-derived sessions, terms/role/error/state patterns, components, and source-inspector ideas. Build incrementally against validated real APIs:

- Workspace/matter selection, permitted documents/versions, membership/configuration administration, and honest scoped dashboard.
- Upload/import, quarantine reasons, scanner/processing progress, retry/failure states, and OCR correction/source verification.
- Contract source viewer beside clause/party/playbook/deviation/obligation analysis, review, redline, and cited summaries/exports.
- Regulatory registry, authority/version/effectivity, old/new diff, applicability decision, watchlists, freshness, and impact campaign.
- Requirement/policy/control/evidence maps, six-state explanations, evidence currency, finding/remediation and retest.
- Obligations/calendar/tasks/dependencies/in-app alerts and independent review queue.
- Authorized search/assistant with citations, uncertainty, facts/interpretations, and permitted conversation history.
- Audit timeline, snapshots/replay, evidence packs, exports, profile/admin/help and truthful capability copy.

Replace active industrial navigation only after backend callers/utilities and validated replacements are separated. Do not convert equipment counts to contract counts or show mock compliance metrics as actual data.

Test keyboard order/focus/skip links, semantic headings/forms/tables, contrast, responsive/reflow, screen-reader names, source jump coordinates, disabled/pending/empty/error/degraded states, session expiry, role denial, and actual backend journeys. UI hiding supplements server policy; it never establishes authorization.

**Exit:** legal counsel, compliance reviewer, business owner, and auditor complete primary workflows without developer/admin intervention. Tests/lint/build and real E2E/accessibility checks pass; landing polish alone is insufficient.

## 19. Step 9: legal quality evaluation and consolidated security

**Estimate:** 12-20 person-days. **Phase:** L, integrated with all earlier phases. **Requirements:** FR-001..005/007/022/028/036/048..055/065/066 plus security/privacy/quality NFRs.

Create versioned public/synthetic legal golden corpora with named fixture authors, expected clause/field/obligation/source/version outcomes, review labels, and approved thresholds. Separate this from frozen industrial benchmarks. Evaluate OCR/layout/field/obligation precision-recall, retrieval recall/ranking, citation precision/coverage, summary factuality/material omissions, refusal/uncertainty, regulatory change recall/version correctness, and compliance evidence/status accuracy.

Add full resource-operation-role-tenant authorization matrix across APIs, DB relationships, workers, indexes/rerank/model context, sources, memory, audit, and exports. Exercise indirect/direct prompt injection, malicious embedded instructions, untrusted authority/source poisoning, model tool misuse/exfiltration, secret/log leakage, evidence tampering, and expensive-job abuse.

Review sessions/origin/CSRF/cookies/TLS, privileged operations, quotas/rate limits, least-privilege deployment/DB/service identities, encryption/secrets, dependency/SBOM/container findings, artifact integrity, and source parser fuzz/containment. Review private secondary copies: checkpoints, traces/prompts, caches, history, exported files, backups, and support logs.

Run complete root-router/application and applicable inherited regression checks in an approved supported environment. Record pre-existing failures honestly. Resolve frozen readiness mismatch by owner-reviewed evidence disposition, not changing expected hashes silently. Independent penetration testing remains a production/high-sensitivity gate with explicit remediation/retest scope.

**Exit:** approved quality thresholds and security gates pass; known failures, mocks, limits, and unconfigured adapters remain named. Security is implemented throughout, not postponed until L.

## 20. Step 10: enterprise identity, legal policy, and pilot operations

**Estimate:** 10-16 person-days plus external decision/provisioning lead time. **Phases:** D/L/M operational gates. **Requirements:** FR-001/004/005/053/064/065/066 and deployment NFRs.

Implement/configure selected enterprise SSO/OIDC/SAML, MFA support, identity lifecycle, privileged re-authentication, session expiry/revocation/step-up, and negative tests. Optional SCIM may be later, but enterprise Must identity gates are not waived by local development auth.

Select pilot jurisdiction/industry/entity scope and source/playbook owners. Approve authoritative sources, applicability, control/evidence policy, materiality/review/escalation, scoring, privilege/classification, legal-platform terms, retention/deletion/legal hold, and applicable privacy/subject-right workflows. Public/synthetic fixture approval is not operational legal-pack approval.

Approve private/local model endpoint/profile/hardware/data residency; validate no disallowed fallback, prompt/trace retention, model change governance, quotas/budgets, and evaluated quality. Verify ownership of all candidate DB/object/vector/model resources before provisioning/migration. Use encrypted durable source/backups, TLS, secret/key rotation, restricted network/service roles, safe temporary artifacts, and tested object retention/hold.

Provide correlated redacted logs, metrics/traces, job queue/attempt/dead-letter monitoring, scanner updater/freshness, index lag, regulatory last-success, stale evidence/overdue workflow, model latency/refusal/schema/citation quality, usage/cost, and actionable alerts. Write incident/restore/model/scanner/search/timer runbooks and named owners.

Agree availability/capacity/performance/RPO/RTO/retention targets for the actual environment. Master targets 99.5% availability and about two seconds p95 metadata/search are targets to measure, not current attainment. HA/regional deployment is an additional selected profile, not assumed delivered by Compose.

**Exit:** named pilot environment, identity, legal/privacy/model policies, operators, and recovery/performance thresholds are approved and configured. Start these decisions early to avoid blocking final acceptance.

## 21. Step 11: full acceptance, recovery, and reviewed release

**Estimate:** 8-12 person-days. **Phase:** M. **Requirements:** all delivered FRs and acceptance/NFR evidence.

### 21.1 Mandatory end-to-end demonstrations

1. Contract intake -> parse/OCR quality -> exact clause analysis -> approved playbook deviation -> independent review -> accepted owned obligation -> cited executive/risk summary -> approved export.
2. Manual governed regulatory import -> effective version -> requirement/control mapping -> accepted evidence -> explainable assessment -> evidence expiry/replacement -> stale/current-state change -> finding/remediation -> closure/retest.
3. New approved regulatory version -> exact/semantic diff -> human applicability/materiality -> affected-object campaign -> review/tasks -> auditable historical snapshot.
4. Authorized Q&A -> allowed hybrid retrieval -> citation validation -> exact source open; weak source causes qualified answer/refusal.
5. Worker/timer kill/restart, duplicate events, permission revocation, and model/scanner/storage/search outages -> visible safe states, no lost obligations, and no duplicate authoritative records.
6. Auditor selects scope/date -> source/evidence/analysis/review history -> integrity-checked permitted evidence pack/export.

### 21.2 Recovery, migration, and performance

Run fresh and historical upgrades to actual release head; verify ORM parity/repeat upgrade/immutable source/audit/review preservation and safe downgrade boundaries. Rehearse DB backup/restore plus source storage restoration, vector/full-text rebuild, configuration/key recovery, and reconciliation on dedicated synthetic resources. Verify recovered hashes/IDs/decisions/jobs/timers, not just process startup.

Measure upload/parse/search/queue/calendar/audit/export load, concurrency, tenant quotas/backpressure, index rebuild lag, and memory/file descriptor worker soak. Compare measured results to approved thresholds; document capacity envelope and degraded behavior.

### 21.3 Final handoff/release gate

Reconcile all 66 FRs with code, test command/result, fixture/profile/version, demo, blocker, and owner. Separate delivered core/pilot, extensions, and future optional work. Synchronize guide/progress/validation/architecture/reuse/FR/handoff/runbooks. Obtain independent review, legal/pilot acceptance, actual CI on latest artifacts, and normal release approval/promotion. Show full known-limitations report before authorized publication/deployment.

**Exit:** reproducible acceptance, tested recovery, real primary user journeys, named operational ownership, and truthful requirement reconciliation. No direct-main bypass or deployment from a documentation-only green checkpoint.

## 22. Catalogue extensions and the full innovation roadmap

### 22.1 Explicit catalogue extensions

These are not dropped. They have separate acceptance scope, and some may be brought into the pilot by an approved scope decision. Estimates are incremental to the core/pilot table where listed; adapter count/licensing/customer requirements change connector effort.

| Extension | Requirements | Remaining delivery | Incremental person-days |
|---|---|---|---|
| Exception/risk acceptance | FR-046 | Authorized independent rationale/source/expiry, renewal/revoke, audit, expiry monitoring; no indefinite/self-approved exception | 3-5 |
| Bulk triage/evidence campaigns | FR-047 | Per-object permission, bulk progress, idempotent retry, recipient restrictions, partial failures and audit | 3-5 |
| High-assurance archive | FR-060 | Independent anchoring/signing/key/retention policy, tamper-evident manifests, restore/verify tests | 5-10 |
| Scoped service credentials | FR-062 | Service accounts/API keys, object/operation/classification scopes, expiry/rotation/revocation, audit and no admin reuse | 4-6 |
| Signed events/webhooks | FR-063 | Signed scoped payload, timestamp/nonce/replay/rate/idempotency, retries/dead letters, summary-only egress | 4-7 |
| Connector framework + first selected adapter | FR-061 | Governed source/adapters/secrets, reconciliation, retry/dead letters, safe inbound/outbound events | 8-15 |

Connector coverage includes approved DMS/cloud drive, ticketing, email, GRC/ERP/vendor, IAM, and regulatory sources as selected. Each additional adapter needs a separate estimate and contract/security/recovery checks. Manual regulatory import and in-app notifications remain functional first paths, not fake automatic feeds/email.

FR-064 governed configuration, FR-065 model/data-residency policy, and FR-066 recovery/retention administration are in core/pilot steps; their configuration UI/API and acceptance evidence must still be completed. Conversation history FR-053 is in F/L/pilot and requires real permission/retention behavior.

### 22.2 All master-report innovation concepts

| Innovation | Delivery placement and completion meaning |
|---|---|
| Compliance digital twin | Core H: persistent typed relationships, reviewed mappings, evidence/current-versus-historical state |
| Regulatory change radar | G/I manual-source watchlists/freshness first; approved automated connectors later |
| Impact blast radius | G/H persistent authorized dependency traversal; advanced simulations later |
| Temporal legal reasoning | G/F: exact effective version/as-of grounding; approved packs required |
| Compliance time machine | J: recorded/effective snapshots and historical replay; extended UX/performance thereafter |
| Evidence freshness engine | H/I: deterministic expiry/staleness and re-evaluation/tasks |
| Compliance drift detection | G/H/I: source/control/evidence/contract changes invalidate current conclusions |
| Obligation collision detection | Basic F/I duty/deadline workflow is Must; advanced semantic simulation later |
| Semantic conflict engine | F/G source-linked qualified proposals; advanced cross-jurisdiction semantics need evaluation |
| Missing-clause detection | F: approved playbook plus inspected coverage; incomplete parser qualifies absence |
| Second-opinion engine | Later: independent constrained evaluated profiles, same permitted evidence, disagreement escalation |
| Adversarial review mode | Later: bounded falsification of proposals; source-grounded and no independent acceptance authority |
| Proof-of-compliance/evidence pack | J: permitted point-in-time provenance/decisions; output is evidence, not universal certification |
| Audit replay | J/M: reproduce source/analysis/rule/model/human basis; recovery verifies history |
| Explainable score | H/K: visible approved components/weights/missing evidence; no opaque model score |
| What-if simulator | Future: proposed changes assessed without mutating authoritative state; curated scope/thresholds |
| Regulation-to-control compiler | Future: counsel-approved interpretation to reviewed deterministic rules, no automatic legal truth |
| Source authority ranking | G/E/F: governed source tiers in retrieval/citation/applicability, never search rank as authority |
| Smart alert prioritization | I/extended: approved urgency/materiality/owner policy, honest reasons and no silent lost alert |
| Vendor compliance graph | Future: governed supplier contracts/attestations/controls/incidents/obligations and selected adapters |

Additional future scope includes technical control telemetry, evidence-freshness prediction, negotiation simulation, cross-jurisdiction what-if, SCIM, HA/scale, richer policy-as-code and graph analytics. These need scoped data/policy/customer requirements before firm estimates. The document tracks them explicitly but does not pretend an unbounded future roadmap is one fixed release.

Excluded initial product actions remain autonomous signing/filing/regulatory submission, universal compliance certification, replacing counsel/auditors, default training on confidential customer documents, and autonomous high-impact destructive remediation. These are approved product boundaries, not omitted build tickets.

## 23. Effort, staffing, timeline, and milestone targets

### 23.1 Remaining core/pilot engineering effort

| Step | Work package | Person-days |
|---|---|---|
| 0 | Existing checkpoint reconciliation/review/integration | 1-2 |
| 1 | Secure document completion, durable jobs, parser isolation | 8-12 |
| 2 | Authorized retrieval/index/source APIs | 6-10 |
| 3 | Contracts, summaries, grounded assistant, minimum review | 15-22 |
| 4 | Persistent regulatory intelligence | 8-12 |
| 5 | Persistent compliance model/digital twin | 10-15 |
| 6 | Obligations/tasks/timers/notifications | 10-15 |
| 7 | Governance/remediation/audit/reporting | 10-15 |
| 8 | Legal frontend and full user journeys | 20-30 |
| 9 | Consolidated quality/security | 12-20 |
| 10 | Enterprise identity/legal policy/pilot operations | 10-16 |
| 11 | Integrated acceptance/recovery/performance/release | 8-12 |
| TOTAL | Core/pilot base effort | 128-199 |
| CONTINGENCY | Approximately 25% for integration/evaluation rework | 32-50 |
| PLANNING TOTAL | Core/pilot with contingency | 160-249 |

Core/pilot base effort is approximately 1,024-1,592 working hours across all contributors; with contingency approximately 1,280-1,992 hours. Catalogue extensions add 27-48 base person-days before contingency and additional adapters. Estimates are preliminary planning ranges, not measured remaining-task durations or guarantees.

### 23.2 Assumptions and elapsed-time scenarios

- Reuse current stack and mature infrastructure; no full frontend/framework/storage rewrite.
- One selected pilot jurisdiction/industry/deployment profile and approved public/synthetic development corpus.
- Full-time developers with relevant Python/domain/frontend skill; predictable review access and working isolated runtime.
- Selected private model/hardware can meet approved quality gates without prolonged research/model replacement.
- Detailed implementation/security/fixture acceptance in earlier steps and consolidated L/M tests have different scopes; do not double-count broad retesting without changed risk.
- Frontend has substantial work and is currently owner-managed. Its completion is part of the overall product, even though the assistant is not implementing it under current scope.

| Capacity | Preliminary core/pilot calendar range | Interpretation |
|---|---|---|
| One backend engineer plus owner frontend in parallel | Approximately 6-10 months | Assumes frontend keeps pace; approval/provisioning/part-time limitations can extend it |
| Three full-time engineers across backend/frontend plus accessible QA/security/legal reviewers | Approximately 14-22 weeks | Includes dependency/integration overhead; not effort divided by three with no constraints |
| Three-engineer first development MVP | Approximately 10-16 weeks | All three pillars, real reviewed persistence, baseline security/recovery; enterprise/pilot acceptance may continue |
| Part-time contributors | Scale to actual weekly available hours | Do not promise full-time dates from occasional sessions |

For reference, current-model backend/non-frontend effort is about 108-169 base person-days; with 25% contingency about 135-211 days. At five working days per week that is roughly 27-42 engineering weeks before external waiting, consistent with the 6-10-month planning range when frontend overlaps.

### 23.3 Proposed three-engineer milestone windows

- Weeks 1-4: checkpoint reconciliation, durable document/scanner/parser completion, initial source/retrieval APIs; pilot decisions and quality fixture preparation start.
- Weeks 4-9: contract/clause/playbook/summary/Q&A and minimum review; frontend source/contract journeys; regulatory persistence begins after source contracts stabilize.
- Weeks 7-13: regulatory/compliance persistence and evidence freshness; tasks/timers and review/remediation integrate as predecessor objects become available.
- Weeks 10-16: all three development pillars and frontend journeys demonstrated; audit/basic exports, restart/failure, and baseline restore/security evidence.
- Weeks 14-22: enterprise/pilot configuration, consolidated quality/security fixes, full recovery/performance, UAT, independent review, and release acceptance.

These windows overlap intentionally and are a scheduling proposal, not permission to bypass source/review/migration dependencies. Re-estimate after E completion and first actual legal-model golden run; these resolve the largest remaining uncertainties.

## 24. Ownership, decision register, and immediate next actions

### 24.1 Delivery ownership

Current recorded model: integrator builds backend; owner builds frontend/landing. The historical three-workstream allocation remains useful for reassignment: documents/contracts/search; regulatory/compliance; workflows/security/recovery. Do not assume unavailable human teammates or an unattended agent are working. Any future parallel implementation needs explicit non-overlapping ownership and one agreed migration chain.

Independent human reviewer validates feature acceptance; legal/compliance owners approve source/playbook/applicability/evidence/retention/materiality rules; security/privacy validates identity/data/provider boundaries; operator/DevOps owns selected resource provisioning/keys/monitoring/recovery; QA/user owners validate actual journeys and quality. One GitHub account running multiple agents does not establish independent human review.

### 24.2 Decisions needed to keep the schedule credible

| Decision | Needed before | Owner/result |
|---|---|---|
| Pilot jurisdiction, industry, entity/product scope | G/H rules and pilot claims | Legal/compliance owner; versioned pack |
| Approved sources/playbooks/evidence and scoring thresholds | F/G/H acceptance | Counsel/compliance; reviewed fixture versus operational labels |
| Required languages/document sizes/table/email formats | E quality completion | Product/legal owner; representative corpus and bounds |
| Enterprise IdP/MFA/step-up and lifecycle | Pilot identity | Security/IT; tested configured provider |
| Private model/hardware/profile/data residency | Actual AI evaluation and pilot | AI/security owner; evaluated pinned policy |
| Retention/legal privilege/hold/deletion/terms | Sensitive pilot handling | Legal/privacy owner; approved versions/workflows |
| Storage/network/DB/vector resource ownership | Any provisioning/private migration | Operator; isolated verified targets |
| Scanner freshness/updater/rescan policy | Real application scan release | Security/operator; monitored approved policy |
| Calendar/timezone/business-day/escalation rules | Accepted deadline scheduling | Legal/business owner; versioned approved calendars |
| SLO/capacity/RPO/RTO/backups/recovery owners | M/pilot acceptance | Operations/business; measured gate and rehearsal |
| Required connectors/archive/service/webhook scope | Extension release estimate | Product/security/customer; explicit selected adapters/profile |
| Independent review and frontend weekly capacity | Reliable delivery schedule | Owner; named capacity and reviewers |

### 24.3 Next concrete actions

1. Reconcile/publish/review the actual local scanner/OCR/correction checkpoint under authorized PR rules.
2. Start the next bounded implementation milestone: durable document jobs and restart/retry, using existing recovery patterns, then production parser isolation.
3. Complete scanner operational provenance/rescan and remaining quality/source-integrity gates in E.
4. Deliver authorized retrieval/source list/viewer contracts for owner frontend integration.
5. Begin F with legal schemas, golden fixtures, private-model policy, and minimum independent review; parallelize only stable non-overlapping downstream contracts.
6. Maintain one requirement ledger with actual code/test/demo/blocker evidence; update living guide/progress/validation/handoff at each checkpoint.

The source-defined MVP must complete all three pillars. Do not call the document-only stage finished, omit review/timers/recovery to meet a short deadline, or equate main README visibility with deployed functionality.

## 25. Complete FR-001 through FR-066 delivery checklist

This appendix preserves every master-catalogue ID. FR-001..045 are Must; FR-046..066 are Should. Priority does not mean every Should is outside the first slice: authorized retrieval/audit/model policy/recovery are necessary parts of the approved development/pilot architecture. No row is declared fully accepted by this report. Current evidence is partial and recorded in sections 5-7 and the canonical traceability registry.

### Identity and access: FR-001..005

- **FR-001 (Must):** enterprise OIDC/SAML/SSO and MFA. Remaining D/L/M pilot implementation/configuration and real IdP/session/denial evidence; local auth is development-only.
- **FR-002 (Must):** server-side organization/workspace isolation. D partial evidence exists; finish and test all E-M jobs/retrieval/model/review/audit/export relationships and paths.
- **FR-003 (Must):** scoped RBAC and approved matter/jurisdiction/unit/sensitivity policy. D policy exists; complete domain-operation matrix and lifecycle/concurrency in J/L.
- **FR-004 (Must):** document/matter ACL and legal hold. D read/propose/review scope is partial; finish all source/chunk/export/delete/hold/retention paths and pilot policy.
- **FR-005 (Must):** privileged re-authentication/session controls. Complete selected step-up/stale-auth/revocation/admin tests before pilot.

### Document intelligence: FR-006..011

- **FR-006 (Must):** PDF/DOCX/TXT/images/approved email-export intake. Existing PDF/DOCX/TXT is partial; finish approved format matrix, source/provenance/malformed fixtures.
- **FR-007 (Must):** type/size/malware validation and isolation before processing. Intake/scanner fixture evidence is partial; complete operational scanner provenance/update/rescan/parser sandbox/quotas and adversarial tests.
- **FR-008 (Must):** layout-aware extraction/OCR with page/section/regions. Native/bounded English OCR exists; complete representative table/mixed/scanned/language/quality/size scope and acceptance.
- **FR-009 (Must):** classification/metadata/duplicate/version detection. Workspace duplicates exist; finish classification/version semantics/concurrent retry with no cross-tenant hash leakage.
- **FR-010 (Must):** immutable source hash and all derived lineage. Originals/spans/corrections partial; extend to analyses/indexes/evidence/exports/recovery and tamper tests.
- **FR-011 (Must):** human correction workflow retaining original regions/history. Local nonempty-span review exists; add blank-region path/projection/quality/frontend acceptance.

### Contract analysis: FR-012..019

- **FR-012 (Must):** parties/definitions/terms/dates/renewals/notices/governing-law proposals. Build F persistent schemas/profiles and field accuracy/source review.
- **FR-013 (Must):** clause segmentation/classification. Build F/K ordered stored spans, coverage/source-jump and approved labels.
- **FR-014 (Must):** duties/rights/prohibitions with actor/trigger/deadline/conditions/source. Build F/I, uncertainty/date confirmation, schema and citation tests.
- **FR-015 (Must):** approved playbook/template comparison. Build F versioned owners/rules/source context and independent review.
- **FR-016 (Must):** missing clauses/deviations/unusual terms/internal conflicts. Build F/L with expected-rule citation, inspected coverage, and incomplete-parser qualification.
- **FR-017 (Must):** cross-contract conflicts/obligation collisions. Build basic F/I/L source-linked duty/deadline workflow and false-positive review; advanced simulation remains separately tracked.
- **FR-018 (Must):** version redline and semantic change summary. Build F old/new exact differences plus grounded semantic proposal and material-term preservation tests.
- **FR-019 (Must):** accepted findings create trackable obligations/reminders. Build F/I/J exact reviewed promotion, idempotency, and rejected/unreviewed denial.

### Summarization: FR-020..025

- **FR-020 (Must):** executive/detailed/clause/risk/obligation/action/change summaries. Build every F/K profile and golden factuality/citation/coverage tests.
- **FR-021 (Must):** audience transformation preserves meaning. Build F/L material conditions/duties/date equivalence and omission checks across profiles.
- **FR-022 (Must):** every substantive statement links authorized spans. Span primitives exist; build E/F/L statement-level source validation and forged/missing citation release denial.
- **FR-023 (Must):** uncertainty and missing information. Build F/K/L explicit absent/conflicting-source labels and honest review states.
- **FR-024 (Must):** cross-document synthesis with citations. Build F/L permission/version-specific grounding, contradictions, coverage and denied-document checks.
- **FR-025 (Must):** approved summary PDF/DOCX/JSON exports. Build F/J/K manifest/content parity, approved-state and per-object access checks.

### Regulatory intelligence: FR-026..032

- **FR-026 (Must):** governed authoritative registry/tiers. Build G persistence/owners/trust/approval and no automatic public-source authority.
- **FR-027 (Must):** approved regulation/guidance import. Build E/G manual provenance/source spans and governed import permissions; feeds not fabricated.
- **FR-028 (Must):** regulatory versions/effective dates/amendments. Pure helper partial; build G/L persistence and historical/unknown/overlap/version tests.
- **FR-029 (Must):** structural/text/semantic change. Exact helper partial; build G immutable change records plus grounded semantic review and change recall.
- **FR-030 (Must):** human applicability/materiality validation. Build G/J independent exact source/version/effective-context decisions and impact gate.
- **FR-031 (Must):** jurisdictions/entities/products/units mappings. Build G/H reviewed scope-qualified persistence and invalidation.
- **FR-032 (Must):** watchlists/change alerts. Freshness helper partial; build G/I persistent manual freshness/alerts first; approved automated connectors later.

### Compliance assurance: FR-033..040

- **FR-033 (Must):** distinct requirement/obligation/policy/control/evidence/finding entities. Build H/F/I persistence, revisions, and lifecycle constraints.
- **FR-034 (Must):** requirement-control-evidence mapping. Traversal helper partial; build H authorized same-workspace FK links/integrity and missing components.
- **FR-035 (Must):** deterministic rules without model where possible. Pure engine partial; build H reviewed rule persistence/version binding and repeatable outcomes.
- **FR-036 (Must):** grounded provisional AI interpretation/uncertainty. Build H/J/L approved profile/evidence/schema/independent acceptance and insufficient-source refusal.
- **FR-037 (Must):** six explainable assessment states. Engine partial; build H/K persistent inputs/results/reasons and transitions with human applicability.
- **FR-038 (Must):** evidence freshness/expiry. Engine partial; build H/I accepted evidence persistence, clocks/scheduler/current-state invalidation.
- **FR-039 (Must):** drift after source/control/evidence/contract changes. Engine partial; build G/H/I durable change events/re-evaluation while preserving historic snapshots.
- **FR-040 (Must):** explainable visible scoring. Component counts partial; build H/K/L approved weighting/coverage/missing-evidence treatment and transparent reasons.

### Workflow/remediation: FR-041..047

- **FR-041 (Must):** durable exact-revision approvals. Legacy and transcription primitives partial; build D/J full legal target transitions, restart/concurrent decision/revoke and evidence binding.
- **FR-042 (Must):** owner/due date/dependencies/escalation. Build I/J scope/reassignment/cycles/overdue/approved-calendar logic.
- **FR-043 (Must):** remediation from accepted finding. Build H/I/J idempotent task creation, closure proof, independent review/retest/reopen.
- **FR-044 (Must):** comments/mentions/decisions/attachments with audit. Build I/J/K permitted recipient/object controls and immutable material decision history.
- **FR-045 (Must):** notice/renewal/certification/recurrence timers. Build I/M durable occurrences/receipts, timezone/calendar and no lost/duplicate effects after restart.
- **FR-046 (Should):** expiring exceptions/risk acceptance. Tracked extension J; independent authority/rationale/expiry/revocation and monitoring.
- **FR-047 (Should):** bulk triage/evidence campaigns. Tracked extension I/K; per-object access, retry, partial result/recipient controls.

### Search and assistant: FR-048..053

- **FR-048 (Should):** authorized hybrid keyword/semantic retrieval/filtering. Existing industrial pipeline reusable; implement E/F/L legal scope/version/jurisdiction/authority/recall gates.
- **FR-049 (Should):** natural-language questions over permitted corpus. Build F/L authorized context, grounded schemas, injection/no-exfiltration and outage behavior.
- **FR-050 (Should):** exact page/section/clause/version citations. Local quote primitives partial; finish E/F/K original-integrity source viewer/jump and all output citation resolution.
- **FR-051 (Should):** insufficient-support refusal/qualification. Build F/L material-claim sufficiency gate and truthful uncertainty.
- **FR-052 (Should):** distinguish fact/observation/inference/recommendation. Build F/H/K typed schemas and visible labels, no interpretation-as-fact.
- **FR-053 (Should):** scoped retained conversation history. Build F/L pilot memory ACL/revocation/delete/hold/retention; memory is never legal truth.

### Audit and reporting: FR-054..060

- **FR-054 (Should):** append-only security/business audit. Existing chain/legal intake/correction events partial; extend J to all material actions and transactional/tamper checks.
- **FR-055 (Should):** actor/time/source/model/prompt/rule/review provenance. Source/correction lineage partial; build F/J analysis/conclusion manifests without raw prompt logging by default.
- **FR-056 (Should):** point-in-time snapshot/replay. Pure as-of helper partial; build G/J recorded/effective evidence/decisions and historical reconstruction.
- **FR-057 (Should):** executive/legal/compliance/audit dashboards. Build K real permitted aggregates, changes/overdue/evidence/review metrics, no fabricated industrial relabeling.
- **FR-058 (Should):** selected scope evidence packs. Build J/K frozen source/version/review/integrity manifests and denied-object exclusion.
- **FR-059 (Should):** machine-readable findings/reports. Build J/K JSON/schema/version/content parity and export authorization.
- **FR-060 (Should):** high-assurance tamper-evident archive. Tracked J/M extension with independent key/anchor/retention/verify, not a tamper-proof claim.

### Administration and integrations: FR-061..066

- **FR-061 (Should):** governed DMS/drive/ticket/email/GRC/IAM/regulatory connectors. Tracked G/M extension with selected adapters/secrets/retry/dead-letter/reconciliation and approved content boundaries.
- **FR-062 (Should):** scoped API credentials/service accounts. Tracked D/L extension with operation/object scopes/expiry/rotation/revocation; no blanket admin identity.
- **FR-063 (Should):** finding/task/evidence webhooks/events. Tracked I/J/L extension; signed scoped summary payloads, replay/rate/idempotency and reliable delivery.
- **FR-064 (Should):** approved playbooks/taxonomy/risk/jurisdiction configuration. Build F/G/H/K versioned ownership/review/effectivity and no guessed operational pack/weights.
- **FR-065 (Should):** model/provider/data residency policy. Existing private gateway reusable; build F/L/M approved legal profiles/provider classification/no fallback/model-change evaluation and config UI/API.
- **FR-066 (Should):** backup/restore/retention/deletion administration. Existing backup guard reusable; build L/M tested restore/reindex/key/config recovery, policy/hold/admin workflow, no automatic deletion before approval.

## 26. Non-functional completeness checklist

The following categories are separate acceptance obligations even when no extra FR ID is assigned. Each needs selected thresholds, actual deployment evidence, or an explicitly documented unaccepted boundary.

- Security: trust-boundary validation, least privilege, authenticated authorized operations, TLS/encrypted storage, controlled secrets, patching/SBOM/container/artifact review, malicious input containment, and independent security review.
- Privacy: purpose/minimization, approved classification/privilege, retention/hold/deletion/subject-right handling, secondary copies/log redaction, provider data boundaries.
- Auditability: reconstruct material outcomes from exact source/retrieval/model/prompt/rule/profile/human versions and decisions, preserve history.
- Reliability: durable jobs/claims/receipts/timers, idempotency/retry/backoff/dead letters, outage/restart/reconciliation, visible safe degraded states.
- Availability: selected pilot 99.5% target evaluated with operating/incident/maintenance policy; HA higher tiers are separately scoped.
- Performance: approximately two-second p95 metadata/search target under representative capacity; async AI/OCR progress and measured queue/parse/export/rebuild latency.
- Scalability: stateless app/workers where appropriate, measured DB/query plans, partitionable rebuildable indexes, per-tenant quotas/backpressure, safe concurrent campaigns.
- Integrity: hashes/immutable versions/tenant FKs/transactions/reconciliation, source storage crash durability, recovered source/decision parity.
- Explainability: sufficient citations, current reasons/evidence/components, uncertainty and fact-versus-interpretation separation.
- Accessibility/usability: keyboard/screen-reader semantics/focus/contrast/forms/tables/reflow/responsive, source beside output, primary journeys without developer intervention.
- Maintainability: reused modular services/typed contracts/additive migrations/flags/config, meaningful automated checks and versioned docs/runbooks.
- Observability: correlation/workflow IDs, redacted logs/metrics/traces, security/job/index/freshness/timer/model quality signals and actionable ownership.
- Portability: selected cloud/private-VPC/on-prem profile with provider-neutral boundary, private model policy, reproducible artifacts; not all profiles automatically deployed.
- Recoverability: agreed RPO/RTO, dedicated DB/source backup/restore/reindex/key/config drill, hash/history/timer recovery and documented runbooks.
- Cost control: tenant usage/budgets/quotas, evaluated model routing, batch embeddings/caching where justified, expensive-job abuse tests.

## 27. Source ledger, authority, and how to maintain this report

### 27.1 Sources used

| Source | Role in this assessment |
|---|---|
| docs/Legal_Regulatory_Assurance_Platform_Master_Report.pdf | Immutable 80-page product authority; detailed FR catalogue pp.17-19, NFR p.20, roadmap/MVP/acceptance pp.51-59, workflow/output/innovation/policy appendices |
| AGENTS.md | Repository/user-work/approval/phase/frontend boundaries |
| docs/SESSION_RESUME.md and CLAUDE_HANDOFF.md | Latest pause/checkpoint context and reading index; dated snapshots reverified |
| docs/LEGAL_DOMAIN_MIGRATION_PLAN.md | A-M dependencies, actual partial stage, phase exit checks |
| docs/MIGRATION_PROGRESS.md and VALIDATION_REPORT.md | Recorded implementation/test/coverage/migration/outage/limits evidence |
| docs/LEGAL_REQUIREMENT_TRACEABILITY.md | All 66 ordered FRs, priorities, acceptance and partial evidence |
| docs/LEGAL_DOMAIN_BUILD_CONTRACTS.md | Approved role/source/time/state/AI/review/recovery invariants |
| docs/MIGRATION_CODEBASE_AUDIT.md | Historical industrial architecture and reuse inventory; historical gaps not treated as current facts |
| docs/LEGAL_PLATFORM_REUSE_MATRIX.md and LEGAL_PLATFORM_TARGET_ARCHITECTURE.md | Reuse-first boundaries and planned target entities/topology |
| backend/app/api/router.py and routes/legal_scope.py | Current registered legacy/legal API source and legal route behavior |
| backend/app/db/models/ and alembic/versions/ | Actual current local ORM/migration inventory |
| backend/app/services/regulatory_versions.py and compliance_assessment.py | Verified pure-function nature of G/H helper implementation |
| frontend/src/app/routes.jsx and source directory inventory | Current frontend shell/legacy routes, no accepted legal journey claim |
| Git root/origin/status/log and GitHub PR #13/remote heads | Read-only current checkpoint/publication/review verification on 9 October 2026 |

### 27.2 Master preservation and interpretation

The master PDF must remain byte-for-byte unchanged. Its recorded SHA-256 is 69ef7ab3f5299a765d641e1f55853dbb6d21cb0ff0610c6e6ff7846ec3b5f102. This new report is separate and does not edit the master.

Use detailed catalogue pp.17-19 rather than shifted summary ranges on p.67. Approved development resolves stack recommendations by retaining React/Vite/private AI; enterprise identity remains a pilot gate; basic collision workflow remains Must even where advanced simulations are future scope. Legal/jurisdiction/provider/retention rules require their named owners rather than invented configuration.

### 27.3 Keeping it accurate

This report is a snapshot, not the canonical execution log. At each actual checkpoint, update the living guide, progress, validation, traceability, architecture/reuse where affected, and resume/handoff. If this owner-facing report is revised, date/version the evidence and regenerate its PDF from the editable Markdown. Never convert historic failures/partial results into a completion claim.

Final summary: we are transforming an existing industrial private-AI workbench into a new evidence-first legal/regulatory product. The foundation and a bounded document/source/correction backend are implemented locally. The remaining work is real legal business persistence, grounded AI quality, monitored obligations/evidence, independent governance, full frontend, and tested security/operations/recovery. Completion is determined by the source-to-decision-to-action-to-audit journeys and all mapped acceptance checks, not branding, file count, or baseline CI alone.
