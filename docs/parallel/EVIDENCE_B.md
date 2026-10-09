# Agent B evidence — contracts, summaries and assistant

Started 2026-10-09 on `integration/backend-continuation-20261007`, authorized root/origin verified at `b3b6a71`. Follow `PARALLEL_BUILD_PLAN_2026-10-09.md`. No live models, dependency/image changes, push/PR/merge or branch operations.

## Current milestone

In progress: synthetic corpus and RED deterministic clause/fact/obligation tests; then immutable tenant-bound contract models and persistence. Migration 0028 is not edited until A's committed stub exists. All outputs remain proposals/needs-review unless the exact target/hash has approved independent review.

## Requests to A

- Please publish/freeze `search_spans` signature and return shape (actor, workspace, matter, terms, query, bounded limit; each hit needs stored span/extraction/document/version/hash/quote/locator/quality). B will re-resolve every hit and check matter before using it.
- Please make review target authorization check **all cited documents** for requester/read/reviewer access, not workspace membership alone. B can expose a resolver per target returning document IDs/hash/requester. Playbooks need scoped legal reviewer authority without a self-grant; summary approval must inspect every cited source.
- Proposed `legal.contract.obligation_accepted` payload: `proposal_id`, `proposal_sha256`, `review_id`, `requester_id`, `document_id`, `version_id`, `source_sha256`, `actor`, `action`, `obligation_type`, `trigger`, `conditions`, `original_deadline_phrase`, `uncertainties`, `citations` (stored span IDs/quotes/locators). B never chooses a normalized legal due date; A's accepted-obligation handoff must keep ambiguous dates pending human confirmation.
- `legal.document.extracted` payload needs originating `actor_id`, workspace/document/version/extraction IDs. B handler will recognize registered contracts or document type `contract`, then queue deterministic analysis using your job API; please freeze that API and worker handler registration contract.
- B will use existing audit type `LEGAL_CONTRACT_RECORDED` through 0028 for redacted domain metadata (no source text), plus your review/outbox events. Please add it to ORM audit vocabulary and scoped root exclusion (A-owned files).
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

## Files / FR scope

Owned files only, as in binding plan. Intended FRs: FR-012..025, FR-048..053, FR-064/065, supporting source/auth/review/audit invariants.

## Limitations / open gates

Deterministic headings/regex/keyword slice; no claim of universal contract understanding or legal accuracy. Synthetic fixtures are authored for this repository, not counsel-approved playbooks or jurisdiction labels. Live-model evaluation, calibrated legal quality, counsel approval, enterprise/pilot/independent human acceptance remain open. No requirement is marked fully accepted.
