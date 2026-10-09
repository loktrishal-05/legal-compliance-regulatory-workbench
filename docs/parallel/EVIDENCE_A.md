# EVIDENCE_A — integrator/platform (Claude Code)

Branch `integration/backend-continuation-20261007`, root/origin verified (`loktrishal-05/legal-compliance-regulatory-workbench`). Baseline at b3b6a71: `docker compose -p lrw-a -f infra/docker-compose.legal-core-test.yml run --rm tests` → **Ran 168 tests, OK**.

## Commits

| Commit | Content |
|---|---|
| 746e7c4 | `[A] Add parallel build plan` (docs/parallel + owner 2026-10-09 plan .md/.pdf) |
| f79c6a9 | `[A] Pre-allocate linear legal migration stubs 0026-0031` (head now `0031_legal_obligations`) |
| c4e56aa | `[A] Freeze parallel build contracts` — 0027 reviews/outbox/scheduler, services, routes, tests |
| 5ae83d1 | Step 1: 0026 durable jobs + region transcriptions, worker, parser sandbox profile, projection |
| 8d316ee | Step 2: document/version/span lists, hash-verified original, `search_spans`, HTTP authz matrix |

## Frozen contracts (T+0:45) — import, don't rewrite

### `app/services/legal_review.py`

```python
class LegalReviewConflict(ValueError)  # str(error) is a stable code
register_target(target_type: str, *, on_approve: Callable[[Session, LegalReview], None] | None = None,
                authorize: Callable[[Session, LegalContext, UUID], None] | None = None,   # additive: object-level check, raise LegalAccessDenied
                operation: str | None = None)  # default review_compliance for COMPLIANCE_TARGETS else review_legal
submit(db, *, workspace_id, target_type, target_id: UUID, target_revision_sha256: str, requester_id: UUID,
       idempotency_key: str, current_terms_version: str | None = None) -> LegalReview
decide(db, *, workspace_id, review_id, reviewer_id, decision: "approve"|"reject"|"request_changes"|"escalate",
       rationale: str, current_terms_version: str | None = None) -> LegalReviewDecision
is_approved(db, *, workspace_id, target_type, target_id, target_revision_sha256) -> bool
get(db, *, workspace_id, review_id, actor_id, current_terms_version=None, lock=False) -> LegalReview
status(db, review) -> "pending"|"escalated"|"approved"|"rejected"|"changes_requested"
decisions(db, review_id) -> list[LegalReviewDecision]
```

Semantics (tested): requester needs `propose` in its scoped role; reviewer needs the target's review operation in its scoped role **and** platform role reviewer/admin **and** ≠ requester (service + DB CHECK). One review per exact `(workspace, target_type, target_id, revision_sha256)`; one terminal decision per review (service row lock + partial unique index); escalations may precede it and never approve. Exact replay returns the existing row; changed content → conflict. `on_approve` runs inside the decision transaction after the audit event; any exception rolls everything back (caller commits/rolls back). Reviewer is re-authorized after the handler. Audit: `LEGAL_REVIEW_REQUESTED`, `LEGAL_REVIEW_DECIDED`. Rows immutable (ORM listeners + 0027 triggers). `current_terms_version` defaults to `settings.current_terms_version`; tests pass `"1.0"`.

`COMPLIANCE_TARGETS = {regulatory_applicability, regulatory_change, requirement_interpretation, evidence_acceptance, assessment, compliance_finding, remediation_closure, exception}`. Each owner calls `register_target(...)` at import time of its service module.

### `app/services/legal_events.py`

```python
class LegalEventConflict(ValueError)
emit(db, *, workspace_id, event_type: str, payload: dict, idempotency_key: str) -> LegalEvent   # joins caller txn
register_handler(event_type: str, handler: Callable[[Session, LegalEvent], None])            # many per type
dispatch_one(db, *, worker_id, now=None) -> LegalEvent | None   # worker; commits
dispatch_due(db, *, worker_id, now=None, limit=100) -> int
audit_activity(db, ctx: LegalContext, action: str, **details)   # LEGAL_ACTIVITY_RECORDED, no migration needed
```

Key scope = `(workspace_id, event_type, idempotency_key)`. Payload is JSON-normalized and SHA-256 bound; payload/type/key/scope immutable (ORM listener + trigger). All handlers for an event run in one transaction with the `dispatched` mark (exactly-once on commit); failure → rollback, `attempts+1`, backoff `30s·2^n`, `dead_letter` after 5 with `last_error_code` = exception class name only. Handlers must still be idempotent (use unique keys) for safety under manual replay.

### `app/services/legal_scheduler.py`

```python
register_scan(name: str, fn: Callable[[Session, datetime], int])
run_due(db, now=None, *, force=False) -> dict[str, int | "error:<Class>"]
```

Receipt row `legal_scheduler_scans(name, last_started_at, last_success_at, last_count, last_error_code, runs)`; claimed `FOR UPDATE SKIP LOCKED`; at most once per 60 s per scan; each scan commits on its own.

### Audit vocabulary (0027)

`LEGAL_REVIEW_REQUESTED`, `LEGAL_REVIEW_DECIDED`, `LEGAL_ACTIVITY_RECORDED` (generic; payload `action` + ids/hashes/codes only). B/C: use `legal_events.audit_activity` instead of adding audit types. Migration helper pattern if anyone still needs one: `audit_vocabulary(events, add)` in 0027 (copy the pattern; do not import migrations).

### Routes (`app/api/routes/legal_review.py`, all under `/v1/workspaces/{workspace_id}`; deny → 404 `{"detail":{"code":"legal_resource_unavailable"}}`; conflict → 409 `{"detail":{"code":"<code>"}}`)

`POST /reviews` body:
```json
{"target_type": "contract_finding", "target_id": "<uuid>", "target_revision_sha256": "<64 hex>", "idempotency_key": "client-key-1"}
```
`POST /reviews/{review_id}/decisions` body: `{"decision": "approve|reject|request_changes|escalate", "rationale": "text"}`
`GET /reviews?status=&target_type=&limit=50&offset=0`, `GET /reviews/{review_id}` → `ReviewResponse`:
```json
{"review_id": "<uuid>", "target_type": "contract_finding", "target_id": "<uuid>",
 "target_revision_sha256": "<hex>", "requester_id": "<uuid>", "status": "pending|escalated|approved|rejected|changes_requested",
 "created_at": "2026-10-09T10:00:00Z",
 "decisions": [{"decision_id": "<uuid>", "reviewer_id": "<uuid>", "decision": "escalate", "rationale": "…", "created_at": "…"}]}
```
List skips objects the actor's `authorize` hook denies before paging (no count leakage).

### Tests

`backend/tests/test_legal_scope_reviews.py` (SQLite + disposable PostgreSQL subclasses), `WorkflowFixture` is reusable (alice analyst requester, bob + carol legal reviewers, other tenant). GREEN: `discover -p test_legal_scope_reviews.py` → **Ran 26, OK**. Covers self-approval, stale revision, wrong-domain reviewer, idempotency/conflict, terminal-decision uniqueness (service + DB), escalation hand-off, request-changes successor, revoked reviewer, other tenant, audit failure + handler failure rollback, immutability, outbox idempotency/conflict, dispatch/backoff/dead letter, scan interval/receipts/error isolation.

`test_legal_scope_migration.py` parity check now pins 0019's own tables (later parity = `alembic check` in `scripts/validate_legal_migrations.py`).

## Requests to B/C

- **C (blocks `validate_legal_migrations`)**: with your in-progress 0029, `alembic check` reported `remove_table` for all 7 `legal_regulatory_*` tables (models not in `Base.metadata` when the script imports `app.db.models`, or definitions differ). Please make `docker compose -p lrw-c ... run --rm tests python -B -m scripts.validate_legal_migrations` pass. `test_legal_scope_regulatory_registry` also had 2 errors at that time.
- **B/C**: register review targets in your service module (`legal_review.register_target(...)`) and emit `legal.contract.obligation_accepted` / `legal.compliance.finding_accepted` / `legal.compliance.evidence_expired` / `legal.regulatory.change_accepted` from your `on_approve` handlers via `legal_events.emit` with a deterministic key (e.g. `f"{target_type}:{target_id}:{revision}"`). Payload shapes A consumes are listed in the Step 6 section once 0031 lands.

## Step 1 — durable jobs, containment, FR-011 (0026)

Service `app/services/legal_jobs.py`: `submit(db, *, actor_id, workspace_id, document_id, version_id, operation: "extract"|"ocr", idempotency_key, current_terms_version) -> LegalJob`, `get(...)`, `claim(db, *, worker_id, now)`, `execute(db, job, *, data_root, current_terms_version, now)`, `run_once(db, *, worker_id, data_root, current_terms_version, now=None, job_limit=10) -> {"jobs", "events", "scans"}`, `transcribe_region(...)`, `projection(...)`, `original(...)`. Worker `python -m scripts.legal_worker [--once]` imports every `app.services.legal_*` module (registration side effects), then loops `run_once`.

Semantics (tested, `test_legal_scope_jobs.py` 22/22 SQLite+PG): one active job per version/operation (duplicates join); same key + different version/op → 409 `job_retry_conflict`; workspace backpressure `MAX_ACTIVE_JOBS_PER_WORKSPACE=20` → 429 `workspace_job_quota`; quarantined → 409. Claim = `FOR UPDATE SKIP LOCKED` + 10-min lease; an expired lease is reclaimed; a final-attempt crash → `dead_letter` (`lease_expired`). Extraction runs as the ORIGINAL actor through `legal_extraction.process` (re-authorize, re-verify stored hash, idempotent per version/policy); artifact + job state + `legal.document.extracted` event commit together. Revoked actor → `failed/actor_not_authorized`, nothing persisted. ParserFailed → failure audit kept, retry 30s·2^n, `dead_letter` after 3. Transient exceptions keep the class name only.

Event `legal.document.extracted` payload: `{"job_id","document_id","version_id","extraction_id","source_sha256","status","actor_id"}`, key `extracted:<extraction_id>`. The synchronous `POST .../extractions` route does not emit it; only jobs do.

Containment: compose profile `parser-sandbox` in `infra/docker-compose.legal-core-test.yml` (network none, read-only root, uid 65534, cap_drop ALL, no-new-privileges, 512m, 64 pids, tmpfs /tmp, code-only mount). Verified 2026-10-09: TXT parse OK; `id` = nobody; writes to `/sandbox` and `/etc` → read-only FS; outbound socket → `Network is unreachable`; no DB/secret env vars; no data root. **Open gate:** the worker still runs the parser as an isolated subprocess (`python -I`, empty env, timeout, output cap) inside its own container; spawning the sandbox container per parse is not wired.

FR-011: `legal_region_transcriptions` (immutable, trigger) anchors manual text to extraction + page + bbox with no stored span; review target `region_transcription` (independent legal reviewer with document read). Projection = original text segments + `approved_correction` overlays (latest approved correction per span) + `approved_manual_transcription` regions, labelled `corrected_projection_not_original`, with `original_text_sha256`; the original artifact is untouched.

Routes (`legal_scope.py`): `POST /documents/{id}/versions/{vid}/jobs` body `{"operation":"extract","idempotency_key":"k"}` → 202 `JobResponse {job_id, document_id, version_id, operation, profile, state, attempts, max_attempts, failure_code, extraction_id, next_retry_at, created_at, finished_at}`; `GET /jobs/{job_id}`; `POST /documents/{id}/versions/{vid}/region-transcriptions` body `{"extraction_id","page","bbox":[x0,y0,x1,y1],"text","rationale","idempotency_key"}` → `{transcription_id, extraction_id, page, bbox, text, transcription_sha256, review_target_type}`; `GET /documents/{id}/versions/{vid}/projection[?extraction_id=]` → `{label, extraction_id, source_sha256, artifact_sha256, original_text_sha256, segments:[{kind, text, span_id?, original_text?, correction_id?, locator?}], manual_regions:[...], text}`.

## Step 2 — lists, source APIs, search

`app/services/legal_search.py`: `readable_documents(ctx)` (SQL subquery mirroring `authorize_document`), `list_documents(db, ctx, *, limit, offset, matter_id, classification, status, filename)`, and the frozen B contract:

```python
search_spans(db, ctx: LegalContext, q: str, limit: int = 20, *, current_terms_version: str | None = None) -> list[dict]
# each: {"span_id","locator","extraction_id","document_id","version_id","source_sha256","extraction_status","quote","rank"}
```

Eligibility (workspace/org, active scope, clearance, active read grant, matter access, non-quarantined version) is applied in SQL **before** ranking/limit; each returned document is then re-authorized (revocation mid-request drops it). PostgreSQL: `to_tsvector('simple', span) @@ plainto_tsquery` ranked by `ts_rank`; SQLite fallback = substring. Empty/overlong (>200)/NUL query → `[]`. No totals anywhere. Optional Qdrant/hybrid path: **not built (open gate)**; no FTS index yet (ponytail note).

Routes: `GET /documents?limit=&offset=&matter_id=&classification=&status=&filename=` → `{"items":[{document_id, filename, document_type, ingestion_status, matter_id, classification, legal_hold, created_at}], "has_more", "limit", "offset"}`; `GET /documents/{id}/versions` → `{"items":[{version_id, status, source_sha256, format, created_at, quarantine_reasons}]}`; `GET /documents/{id}/versions/{vid}/spans?extraction_id=&limit=&offset=` → `{extraction_id, status, source_sha256, artifact_sha256, warnings, items:[{span_id,start,end,locator,quote}], has_more}`; `GET /documents/{id}/versions/{vid}/original` → bytes with `Content-Disposition: attachment`, `X-Content-Type-Options: nosniff`, `X-Source-SHA256`, `Cache-Control: no-store` (hash re-verified, quarantined → 409, audited `original_downloaded`); `GET /search?q=&limit=` → `{"items":[search_spans rows], "mode":"postgres_fulltext"}`.

Tests: `test_legal_scope_search.py` 12/12 (two tenants with identical bytes, restricted matter, revocation mid-search, tampered/foreign IDs, original tamper → integrity error, bad queries). `test_legal_scope_authz_matrix.py` (PG HTTP, all `app.api.routes.legal_*` routers, 7 roles) 4/4 at 8d316ee.

## 3:00 checkpoint

Full suite `-p "test_legal_scope*.py"`: **Ran 302, errors=8**. All 8 are in `test_legal_scope_assistant.py` (B WIP: `ImportError: cannot import name 'legal_assistant'`). No shared-file breakage found. `validate_legal_migrations` PASS (fresh + 0018 → head, including 0026-0030 as present then).

## Requests to A (answered here)

- **B — `search_spans`**: frozen above. `ctx` comes from `authorize_workspace(db, actor_id, workspace_id, current_terms_version=...)`; matter + clearance + read grant are enforced in SQL and re-checked per document. `extraction_status` is the quality signal (`ready`/`needs_verification`); still re-resolve through `legal_extraction.resolve_span` before citing.
- **B/C — review authorization over all cited sources**: supported now. Pass `authorize=` to `register_target`; it runs for the requester at `submit`, for any reader at `get`/list, and for the reviewer at `decide` (before and after `on_approve`). Resolve the target's cited document IDs and call `authorize_document(db, ctx.actor_id, ctx.workspace_id, doc_id, current_terms_version=...)` for each; raise `LegalAccessDenied` to deny. `operation=` lets playbooks require `review_legal` and C targets `review_compliance`. Workspace admin has no review operations (ROLE_OPERATIONS), so there is no self-grant path.
- **B — `legal.contract.obligation_accepted` payload**: accepted as proposed. The Step 6 handler creates the Obligation with `status="needs_confirmation"` until a human confirms timezone + normalized due date; `original_deadline_phrase` is stored verbatim; no date is guessed.
- **B — `legal.document.extracted`**: payload includes `actor_id` (see Step 1). Register with `legal_events.register_handler("legal.document.extracted", fn)` in your service module; the worker imports every `app.services.legal_*` module. Run your deterministic analysis inside the handler (it has the transaction) or emit your own event; `legal_jobs.submit` is only for extraction/OCR.
- **B/C — migration parity**: `scripts/validate_legal_migrations.py` runs `alembic check` against `Base.metadata`, which includes every model imported by `app/db/models/__init__.py`, so your one-line imports are enough. Confirmed PASS with 0028/0029/0030 present.
- **C — `regulatory_source` target**: register it in your module: `legal_review.register_target("regulatory_source", operation="review_compliance", authorize=...)`.
- **C — audit type**: resolved by C (uses `LEGAL_ACTIVITY_RECORDED`, which is already excluded from legacy audit reads via `LEGAL_AUDIT_EVENT_TYPES`).
