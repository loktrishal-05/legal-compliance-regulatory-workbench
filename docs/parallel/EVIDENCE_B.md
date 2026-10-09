# Agent B evidence — contracts, summaries and assistant

Started 2026-10-09 on `integration/backend-continuation-20261007`, authorized root/origin verified at `b3b6a71`. Follow `PARALLEL_BUILD_PLAN_2026-10-09.md`. No live models, dependency/image changes, push/PR/merge or branch operations.

## Current milestone

In progress: synthetic corpus and RED deterministic clause/fact/obligation tests; then immutable tenant-bound contract models and persistence. Migration 0028 is not edited until A's committed stub exists. All outputs remain proposals/needs-review unless the exact target/hash has approved independent review.

## Requests to A

- Please publish/freeze `search_spans` signature and return shape (actor, workspace, matter, terms, query, bounded limit; each hit needs stored span/extraction/document/version/hash/quote/locator/quality). B will re-resolve every hit and check matter before using it.
- Please make review target authorization check **all cited documents** for requester/read/reviewer access, not workspace membership alone. B can expose a resolver per target returning document IDs/hash/requester. Playbooks need scoped legal reviewer authority without a self-grant; summary approval must inspect every cited source.
- Proposed `legal.contract.obligation_accepted` payload: `proposal_id`, `proposal_sha256`, `review_id`, `requester_id`, `document_id`, `version_id`, `source_sha256`, `actor`, `action`, `obligation_type`, `trigger`, `conditions`, `original_deadline_phrase`, `uncertainties`, `citations` (stored span IDs/quotes/locators). B never chooses a normalized legal due date; A's accepted-obligation handoff must keep ambiguous dates pending human confirmation.
- `legal.document.extracted` payload needs originating `actor_id`, workspace/document/version/extraction IDs. B handler will recognize registered contracts or document type `contract`, then queue deterministic analysis using your job API; please freeze that API and worker handler registration contract.
- Audit request resolved: B reuses A's new `LEGAL_ACTIVITY_RECORDED` (0027) for redacted contract/summary/chat metadata; no extra event enum/migration needed. Intermediate persistence tests correctly rejected the initially proposed unregistered event type; no audit checks weakened.
- Please extend migration parity/validator registration for B's tables after models land; B cannot edit the A-owned validator/test. B adds its own migration/immutability checks in contract test files.

## Requests to B

No received requests yet. Re-read A/C evidence at integration checkpoints.

## API contracts

### Working HTTP slice — published for C

Prefix `/v1/workspaces/{workspace_id}`. Cookie/terms/policy enforced; 404 deny/unknown is `{"detail":{"code":"legal_resource_unavailable"}}`, stable conflicts 409, forbidden extras/invalid command 422, bad mutation origin 403, absent real session 401. JSON UUID/hash placeholders below are illustrative, not live records. Current list responses are `{"items": [...]}` (no count leakage; bounded first 200). B's router has one additive registration line; A should preserve/commit shared registration if it also has pending lines.

**POST `/contracts`**, 201:
```json
{"document_id":"<UUID>","version_id":"<document-version UUID>","title":"Synthetic MSA"}
```
```json
{"contract_id":"<UUID>","contract_version_id":"<UUID>","document_id":"<UUID>","version_id":"<document-version UUID>","title":"Synthetic MSA","source_sha256":"<64 hex>"}
```
GET `/contracts` item:
```json
{"contract_id":"<UUID>","document_id":"<UUID>","title":"Synthetic MSA","versions":[{"contract_version_id":"<UUID>","version_id":"<document-version UUID>","source_sha256":"<64 hex>"}]}
```

**POST `/contracts/{contract_id}/versions/{contract_version_id}/analysis`**, body `{}` or `{"playbook_id":"<approved UUID>"}`, 201. GET same path returns latest stored analysis, 200. Path version is **contract_version_id**, not the underlying document-version UUID. Top-level fields:
```json
{"analysis_id":"<UUID>","contract_version_id":"<UUID>","revision_sha256":"<64 hex>","profile_version":"legal-contract-deterministic-v1","schema_version":"legal-contract-output-v1","prompt_version":"no-model-deterministic-v1","rule_version":"synthetic-keyword-rules-v1","status":"needs_review","review_required":true,"parties":[],"facts":[],"clauses":[],"findings":[],"obligations":[],"coverage":{"total_spans":12,"covered_spans":12,"quality":"ready","inspected_span_ids":["<UUID>"]},"uncertainties":[]}
```
Arrays above contain these item shapes (all citations are exact stored quotes, not client claims):
```json
{"span_id":"<UUID>","quote":"Buyer shall pay within 30 days of invoice.\n","locator":{"kind":"line","line":6,"offset_unit":"unicode_codepoint"},"document_id":"<UUID>","version_id":"<document-version UUID>","source_sha256":"<64 hex>","extraction_id":"<UUID>"}
```
```json
{"clause_id":"<UUID>","ordinal":3,"title":"Payment","clause_type":"payment","text":"3. Payment\nBuyer shall pay within 30 days of invoice.","citations":["<citation object above>"]}
```
```json
{"name":"Atlas Buyer","citations":["<citation object above>"]}
```
```json
{"kind":"date","name":"source_date","value":"2027-01-01","citations":["<citation object above>"]}
```
```json
{"proposal_id":"<UUID>","revision_sha256":"<64 hex>","outcome":"proposed","obligation_type":"duty","actor":"Buyer","action":"pay within 30 days of invoice","trigger":null,"conditions":[],"original_deadline_phrase":"within 30 days of invoice","normalized_deadline":null,"uncertainties":["actor_identity_requires_review","deadline_calendar_and_trigger_require_confirmation"],"citations":["<citation object above>"],"review_required":true}
```
Finding item: `{"finding_id":"<UUID>","revision_sha256":"<hex>","outcome":"proposed","kind":"deviation","rule_id":"<UUID>","rationale":"Source matches a synthetic playbook deviation rule","citations":[<citation>]}`; missing-clause additionally has `absence_established` and `coverage`, with incomplete extraction explicitly qualifying absence. Schema examples use the citation-object reference for readability; actual wire arrays contain objects, not strings.

**GET `/clauses|contract-findings|obligation-proposals?analysis_id=<UUID>`** returns `items`; each item uses `id` (not clause_id/finding_id/proposal_id), `analysis_id` plus payload fields above; findings/proposals also have exact `revision_sha256`/`outcome` from the review ledger. **POST `/obligation-proposals/{id}/review`** and **POST `/contract-findings/{id}/review`**, no body, 201:
```json
{"review_id":"<UUID>","target_id":"<UUID>","target_revision_sha256":"<hex>","status":"pending"}
```
Approve/reject/request-changes/escalate through A's `/reviews/{id}/decisions`; never edit outcome in B commands.

**POST `/playbooks`**, 201 (automatically submits exact review):
```json
{"name":"Synthetic payment","version":"v1","legal_basis":"Synthetic fixture only","jurisdiction":"Fictional Territory","effective_from":null,"effective_until":null,"rules":[{"clause_type":"payment","kind":"forbidden_text","label":"Synthetic unusual term","pattern":"30 days"}]}
```
```json
{"playbook_id":"<UUID>","revision_sha256":"<hex>","review_id":"<UUID>","outcome":"pending","name":"Synthetic payment","version":"v1","legal_basis":"Synthetic fixture only","jurisdiction":"Fictional Territory"}
```
GET `/playbooks`: items have same metadata except review_id, and outcome approved/proposed. Unknown effective dates are metadata-only; configured intervals must be timezone-aware and currently applicable before analysis.

**POST `/summaries`**, 201 (automatically submits exact review):
```json
{"sources":[{"document_id":"<UUID>","version_id":"<document-version UUID>"}],"profile":"executive","audience":"business"}
```
```json
{"summary_id":"<UUID>","revision_sha256":"<hex>","review_id":"<UUID>","outcome":"pending","profile":"executive","audience":"business","profile_version":"legal-summary-extractive-v1","schema_version":"legal-summary-v1","prompt_version":"no-model-deterministic-v1","rule_version":"source-coverage-v1","statements":[{"text":"Buyer shall pay within 30 days of invoice.","category":"source_fact","citations":["<citation object above>"]}],"coverage":{"total_spans":12,"covered_spans":12,"omitted_span_ids":[]},"uncertainties":["extractive_summary_not_legal_interpretation"],"missing_information":["Legal applicability and accepted duties require independent review."],"contradictions":[],"review_required":true}
```
Profiles: executive/detailed/clause/risk/obligation/action/change; audience legal/compliance/business/executive/auditor. GET `/summaries` returns items; GET `/summaries/{id}` same stored content without review_id, outcome approved/proposed. **GET `/summaries/{id}/export?format=json|pdf|docx`**: unapproved 409 `summary_not_approved`; approved attachment with no-store/no-referrer. JSON is `{"summary":<GET detail>,"manifest":{"schema_version":"legal-summary-export-v1","summary_id":"<UUID>","revision_sha256":"<hex>","review_id":"<UUID>","decision_id":"<UUID>","reviewer_id":"<UUID>","sources":[<citation>]}}`. DOCX contains this exact JSON at `legal/manifest.json`; PDF attachment `legal-manifest.json` contains it. No authority is inferred from file generation.

**POST `/assistant/questions`**, 201:
```json
{"question":"invoice","matter_id":null,"conversation_id":null}
```
```json
{"status":"qualified","statements":[{"text":"Buyer shall pay within 30 days of invoice.","category":"source_fact","citations":["<citation object above>"]}],"uncertainties":["extractive_matches_not_legal_advice_or_complete_answer"],"missing_information":[],"profile_version":"legal-assistant-extractive-v1","schema_version":"legal-assistant-v1","prompt_version":"no-model-deterministic-v1","rule_version":"authorized-exact-source-v1","conversation_id":null,"memory_is_legal_evidence":false}
```
Unsupported: status refused, statements empty, missing_information `No current authorized source support found.`; fake-only gateway outage: status degraded and uncertainty model_unavailable. No actual live model configuration/execution.

**POST `/conversations`**, body `{"matter_id":null}`, 201: `{"conversation_id":"<UUID>","matter_id":null,"messages":[],"memory_is_legal_evidence":false}`. GET `/conversations` items contain conversation_id/matter_id. GET `/conversations/{id}` adds messages `[{"question":"invoice","answer":<assistant response>}]`; history is owner-only and current source/matter grants rechecked. DELETE same path: `{"conversation_id":"<UUID>","deleted":true}`; erases chat, not original evidence, and refuses legal hold.

**GET `/contracts/{id}/redline?from=<contract-version UUID>&to=<contract-version UUID>`** and **POST `/contract-findings/collisions`** are implemented but detailed HTTP cases are next; do not claim complete FR-017/018 acceptance. Collision body: `{"left_contract_id":"<UUID>","left_version_id":"<contract-version UUID>","right_contract_id":"<UUID>","right_version_id":"<contract-version UUID>"}`; result `{"finding_ids":["<UUID>"],"status":"needs_review"}`. Exact redline includes changes(section/kind/text_diff), old_sources/new_sources, qualified_summary and profile/schema/prompt/rule versions. No semantic legal equivalence asserted.

## RED/GREEN evidence

Runtime target verified: `desktop-linux`, isolated compose `lrw-b`, internal network, synthetic PostgreSQL, model/vector loopback port 9, source mounts read-only; compose configuration passes.

### Milestone B1 — deterministic corpus/analysis GREEN

Command: `docker compose -p lrw-b -f infra/docker-compose.legal-core-test.yml run --rm tests python -B -m unittest discover -s tests -p "test_legal_scope_contracts*.py" -v`.

- RED: six executed tests, nine intended missing `legal_contract_analysis` errors (including four fixture subtests). No unrelated dependency failure.
- GREEN: **6/6 PASS**, all four authored fixtures retain ordered classified clauses, source citations, obligation conditions/deadline phrases without normalized-date guessing; incomplete coverage qualifies absence; document instructions cannot grant acceptance; empty/duplicate/oversize inputs reject.
- Files: `services/legal_contract_analysis.py`, `tests/test_legal_scope_contracts.py`, four TXT fixtures + provenance/expected-label README. No migration/shared registration changes yet.
- Outputs record `legal-contract-deterministic-v1`, `legal-contract-output-v1`, `no-model-deterministic-v1`, `synthetic-keyword-rules-v1`. All remain `needs_review`.
- Golden numerical benchmark and persistence/HTTP/model-output/denial checks follow; six pure tests are not full FR acceptance.

### Milestone B2 — immutable contract persistence GREEN

Same contracts discovery command: RED **10 intended missing-model errors** with six earlier tests passing; GREEN **16/16 PASS**, including five SQLite and five real disposable PostgreSQL persistence checks. An intermediate run rejected unregistered audit vocabulary; reused A's `LEGAL_ACTIVITY_RECORDED`, leaving constraint/atomicity intact.

Implemented `db/models/legal_contract.py` and `services/legal_contracts.py`: tenant/source-qualified contracts/versions/analysis/parties/facts/clauses/clause-span links/findings/obligation proposals; immutable ORM revisions, idempotent source/analysis replay, current grants, no globally merged parties, all-child rollback on mandatory audit failure. Models also allocate summary/playbook/chat tables for later owned service slices. Full migration SQL/triggers/API and review callbacks are next, not claimed delivered by ORM-only tests.

Shared migration stubs landed in A commit `f79c6a9`; 0028 now available for B. Shared model registration not yet changed.

### Milestone B3 — migration 0028 GREEN

Contracts target now **17/17 PASS**. Own migration test RED failed because B tables were absent from stub; GREEN upgrades fresh to 0028 twice, compares every B column/constraint using PostgreSQL's real name truncation, denies TRUNCATE CASCADE for all 13 immutable tables, and verifies 26 update/delete/truncate triggers. Fixture query/name-normalization bugs corrected; trigger expectations kept intact. Conversation memory is intentionally mutable/erasable and not a source-evidence table.

0028 body filled without changing preallocated revision IDs. One additive model import `from app.db.models import legal_contract` appended after re-reading shared registration. **A: please commit shared registration with your own pending registration edits**; B checkpoints exclude this mixed-ownership file to avoid capturing A/C work. Own migration, migration tests and evidence are checkpointed by B. Please incorporate B's migration coverage and table parity in your consolidated validator.

### Milestone B4 — approved playbooks and obligation review handoff GREEN

Contracts target RED: four expected missing playbook/submit errors; GREEN **21/21 PASS**. New schemas forbid authority extras, bound rules/strings and require aware valid playbook intervals. Stored playbooks have owner/basis/jurisdiction/version; unapproved playbooks cannot drive analysis. A's `authorize` callback checks each source document and exact stored quotes/hash. `contract_finding`, `contract_obligation`, and `playbook` registered with exact-revision/requester checks on approval.

Independent obligation approval emits one `legal.contract.obligation_accepted` event in the decision transaction; repeat decisions do not emit duplicates; unreviewed proposals have no event. Payload includes `normalized_deadline: null` plus original phrase/conditions/uncertainties; no legal calendar guessed. Self-review denied. SQLite and PostgreSQL journey checks exercise the real shared ledger/outbox.

Next: routes/exact API examples, source redline/collision proposals, summaries/exports and assistant. Additional forged-hash/matter/role/revocation tests remain integration hardening work, not implied by this 21-test milestone.

### Milestone B5 — summaries/exports and fake-output/redline validation GREEN

- Summaries discovery command (`-p "test_legal_scope_summaries*.py"`): RED six intended missing-service errors; GREEN **6/6 PASS** on SQLite/PostgreSQL. All seven profiles and legal/business audience variants preserve all source statements/conditions, exact citations, coverage/no omitted spans, replay and independent approval. Unapproved exports refuse; approved JSON equals the approved content; DOCX ZIP and PDF embedded manifests equal JSON byte-for-content after parsing. Visible PDF conditions checked across reflow. Revoked/cross-tenant export denied.
- Advanced contracts command (`-p "test_legal_scope_contracts_advanced.py"`): RED two missing-feature errors; GREEN **2/2 PASS**. Strict fake-gateway validator rejects authority/role extras, garbage/empty statements, forged IDs/quotes/claims and injection. Exact redline reuses `regulatory_versions.exact_diff`; literal deadline/duty collision remains review-only. No gateway/model executed.
- Citation schema initially stripped newline whitespace; fixed citation-specific configuration so quotes remain byte-for-text exact. PDF uses installed PyMuPDF Story rendering (no new dependency) and an exact approved manifest; test normalizes only layout whitespace for visible content, not manifests/citations.
- Thin slice: summary profiles/audiences are extractive full-coverage views, not evaluated abstractive audience rewriting; collisions are literal heuristics, not established legal incompatibility. Missing date/applicability/change inputs remain explicitly labelled.

### Milestone B6 — assistant/memory GREEN

Assistant discovery command (`-p "test_legal_scope_assistant*.py"`): RED eight intended missing-service errors; GREEN **8/8 PASS**, SQLite + PostgreSQL. Uses A's SQL-authorized `search_spans(db, ctx, q, limit, current_terms_version=...)`, re-resolves exact quotes/hash, labels source facts, refuses weak support/instruction attacks, detects potential contradictory version support, and exposes fake-model outage as `degraded`. Gateway is **off by default and fake injection only**, no live endpoint wiring/execution.

Conversation memory is workspace/matter/owner-bound; histories recheck all document grants; owner deletion erases messages even after source revocation (legal hold still blocks deletion). Bounded 50 turns, no memory citations as legal truth. Golden/cross-matter/hold/full HTTP tests follow. Search is A's FTS/substring thin slice; dense hybrid and broader natural-language recall remain open.

Requests resolved: `search_spans` frozen and used; reviewer document callback published and used. A: worker must import `legal_contracts`, `legal_playbooks`, `legal_summaries` (and C's domain modules) to register targets/handlers/scans before dispatch. B will queue deterministic analysis through your durable outbox (no second in-memory queue) upon `legal.document.extracted`.

### Milestone B7 — HTTP API and extracted-event dispatch GREEN

Contracts HTTP target RED: three missing-router errors; GREEN **3/3 PASS** on migrated disposable PostgreSQL with real cookie/terms/shared origin/no-store middleware: contract creation/analysis/clauses/proposals; summary generation/independent review/JSON-PDF-DOCX downloads; assistant/conversation/revocation/delete; origin/session/authority extras/unknown uniform-deny.

Persistence event RED: two missing-handler errors; GREEN **16/16 PASS** in persistence target. `legal.document.extracted` recognizes document type contract, registers source contract and enqueues one `legal.contract.analysis_requested` durable outbox row per extraction. B's analysis handler binds exact extraction and reauthorizes the original actor, including after replay/revocation. Worker import integration remains A-owned.

### Milestone B8 — review/matter/version hardening GREEN

Hardening RED: four intended errors exposed absent new-source version attachment and automatic event title conflicting with an existing user-created contract. Shared service fixes preserve user title, allow independently authorized immutable document versions under one contract, validate each version before list exposure, and recheck all multi-source finding citations before returning analysis.

Full contracts discovery target **38/38 PASS**, including SQLite/PostgreSQL business-owner/auditor denial, true self-review with platform/scoped reviewer eligibility, forged review hash rollback (no decision/event), missing document-review grant, restricted matter, source/version ACL revocation and event title replay. No source lineage/role/audit test weakened.

New endpoint **POST `/contracts/{contract_id}/versions`**, body `{"document_id":"<UUID>","version_id":"<document-version UUID>"}`, 201 `{"contract_id":"<UUID>","contract_version_id":"<UUID>","document_id":"<UUID>","version_id":"<document-version UUID>","source_sha256":"<hex>"}`. Both base-contract and new-source propose grants required. GET contracts version items now additionally include `document_id`; inaccessible versions omitted. Contract-version IDs can then be used for redline/analysis.

A's checkpoint confirms worker imports every legal service, so B handlers/targets registration integration request is resolved. B still awaits A's final actual accepted-obligation consumer/combined E2E evidence; emits confirmed agreed payload without guessing due dates.

### Milestone B9 — requester revocation before approval GREEN

Hardening target RED **two actual assertion failures**: approving after originating analyst's propose grant was revoked still emitted accepted obligation. Fixed in shared B approval callback: recompute proposal hash against immutable analysis/collision inputs, verify exact requested revision/requester, and reauthorize every cited document for originating propose permission before release. Same hardening target GREEN **12/12 PASS**, SQLite/PostgreSQL; failed approval rolls back both decision and outbox event.

## Files / FR scope

Owned files only, as in binding plan. Intended FRs: FR-012..025, FR-048..053, FR-064/065, supporting source/auth/review/audit invariants.

## Limitations / open gates

Deterministic headings/regex/keyword slice; no claim of universal contract understanding or legal accuracy. Synthetic fixtures are authored for this repository, not counsel-approved playbooks or jurisdiction labels. Live-model evaluation, calibrated legal quality, counsel approval, enterprise/pilot/independent human acceptance remain open. No requirement is marked fully accepted.
