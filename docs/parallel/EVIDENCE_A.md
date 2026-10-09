# EVIDENCE_A — integrator/platform (Claude Code)

Branch `integration/backend-continuation-20261007`, root/origin verified (`loktrishal-05/legal-compliance-regulatory-workbench`). Baseline at b3b6a71: `docker compose -p lrw-a -f infra/docker-compose.legal-core-test.yml run --rm tests` → **Ran 168 tests, OK**.

## Commits

| Commit | Content |
|---|---|
| 746e7c4 | `[A] Add parallel build plan` (docs/parallel + owner 2026-10-09 plan .md/.pdf) |
| f79c6a9 | `[A] Pre-allocate linear legal migration stubs 0026-0031` (head now `0031_legal_obligations`) |
| (next) | `[A] Freeze parallel build contracts` — 0027 reviews/outbox/scheduler, services, routes, tests |

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

## Requests to A (answered here)

(none yet)
