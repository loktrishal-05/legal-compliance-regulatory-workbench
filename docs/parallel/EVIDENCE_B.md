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

Routes not published as working yet. Exact request/response examples will be appended after GREEN HTTP checks, before frontend integration.

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

## Files / FR scope

Owned files only, as in binding plan. Intended FRs: FR-012..025, FR-048..053, FR-064/065, supporting source/auth/review/audit invariants.

## Limitations / open gates

Deterministic headings/regex/keyword slice; no claim of universal contract understanding or legal accuracy. Synthetic fixtures are authored for this repository, not counsel-approved playbooks or jurisdiction labels. Live-model evaluation, calibrated legal quality, counsel approval, enterprise/pilot/independent human acceptance remain open. No requirement is marked fully accepted.
