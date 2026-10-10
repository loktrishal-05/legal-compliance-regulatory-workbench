# Parallel 8-hour build plan — 2026-10-09

Owner-directed. Source of truth: `docs/LEGAL_PLATFORM_APPLICATION_AND_COMPLETE_BUILD_PLAN_2026-10-09.md` (Steps 0-11, FR-001..066). Master PDF stays byte-for-byte unchanged. Three agents run **at the same time in the same root directory on the same branch** (`integration/backend-continuation-20261007`), with strict file ownership. No separate worktrees (AGENTS.md: single application root).

## Honest scope

The plan estimates 128-199 person-days; this window is ~3 agent-days. Goal: a **development MVP slice of every Step** — all three pillars working end to end with real persistence, independent review, durable timers, audit, frontend journeys, and tests. External gates (enterprise IdP/MFA, legal-pack approval, independent human review, pen test, real-infra recovery/SLO, live private-model evaluation) are implemented as far as code allows and are **recorded as open gates, never as accepted**. No FR is marked "accepted" in `LEGAL_REQUIREMENT_TRACEABILITY.md`; use "MVP implemented + tested" with evidence.

## Agents and ownership

| Agent | Tool | Steps | Owns (create/edit only these) |
|---|---|---|---|
| **A — Integrator/platform** | Claude Code (builder terminal) | 0, 1, 2, 6, 7, 9 (authz/security matrix), 11 | `legal_jobs*`, `legal_search*`, `legal_review*`, `legal_events*`, `legal_scheduler*`, `legal_obligations*`, `legal_audit_export*` models/schemas/services/routes/tests; existing `legal_scope.py`/`legal_correction.py`/`legal_extraction.py`/`legal_intake.py` changes; migrations 0026, 0027, 0031; `infra/`, `.github/`; consolidated living docs |
| **B — Contracts & summaries** | OpenCode (quality) | 3 (+ contract part of 9 golden corpus) | `legal_contract*`, `legal_playbook*`, `legal_summary*`, `legal_assistant*` models/schemas/services/routes/tests; `backend/tests/fixtures/legal_contracts/`; migration 0028 |
| **C — Regulatory, compliance, frontend** | Codex (speed) | 4, 5, then 8, 10 docs | `legal_regulatory*`, `legal_compliance*` models/schemas/services/routes/tests; `backend/tests/fixtures/legal_regulatory/`; migrations 0029, 0030; `frontend/src/features/legal/**`, frontend route/nav/api additions; `docs/parallel/PILOT_DECISION_REGISTER.md`, `docs/parallel/RUNBOOKS.md` |

Shared files (one-line additive edits only, never reformat/reorder others' lines): `backend/app/api/router.py`, `backend/app/db/models/__init__.py`. Re-read the file immediately before editing; it changes under you.

Existing code that only Agent A changes (B/C call it, never rewrite it): `legal_policy.py` (authorize_workspace/authorize_document), `audit.py` (append_event), `legal_intake.py`, `legal_extraction.py`, `legal_correction.py`, `regulatory_versions.py`/`compliance_assessment.py` (C may *add* functions, not change existing behavior), `governance.py`, `durable_execution.py`, `model_gateway/`. Need a change there? Write the request in your evidence file under "Requests to A".

## Migration chain (pre-allocated, linear)

Agent A commits **stubs** for all of these first (empty `upgrade()/downgrade()`), so the chain is always valid. Each owner fills in only its own file. Never renumber, never add another head.

```
0025_legal_corrections -> 0026_legal_jobs (A) -> 0027_legal_reviews_events (A)
 -> 0028_legal_contracts (B) -> 0029_legal_regulatory (C) -> 0030_legal_compliance (C)
 -> 0031_legal_obligations (A)
```

All new tables: `organization_id` + `workspace_id` columns, workspace-qualified FKs (composite with the workspace where the parent is scoped), immutable rows for decisions/revisions (DB trigger like 0024/0025), and ORM/migration parity (`test_legal_scope_migration.py` must keep passing — add your tables to whatever parity list it uses).

## Cross-agent contracts (Agent A publishes by T+0:45 in `backend/app/services/legal_review.py`, `legal_events.py`, `legal_scheduler.py`)

```python
# legal_review.py — exact-revision independent review ledger (Step 7 core)
submit(db, *, workspace_id, target_type: str, target_id: UUID, target_revision_sha256: str,
       requester_id: UUID, idempotency_key: str) -> LegalReview
decide(db, *, workspace_id, review_id: UUID, reviewer_id: UUID,
       decision: Literal["approve","reject","request_changes","escalate"], rationale: str) -> LegalReviewDecision
is_approved(db, *, workspace_id, target_type, target_id, target_revision_sha256) -> bool
register_target(target_type: str, *, on_approve: Callable[[Session, LegalReview], None] | None = None)
# Reviewer != requester; reviewer needs current review permission (legal_policy); escalate never approves;
# a changed revision hash makes an earlier approval inapplicable; handlers run in the decision transaction.

# legal_events.py — transactional outbox
emit(db, *, workspace_id, event_type: str, payload: dict, idempotency_key: str) -> LegalEvent
#   same key + same payload -> existing row; same key + changed payload -> LegalEventConflict
register_handler(event_type: str, handler: Callable[[Session, LegalEvent], None])
#   dispatched by the worker with lease/retry/dead-letter; handlers must be idempotent

# legal_scheduler.py — durable periodic scans
register_scan(name: str, fn: Callable[[Session, datetime], int])  # e.g. evidence expiry, regulatory freshness
```

Target types: `contract_finding`, `contract_obligation`, `playbook`, `summary`, `regulatory_applicability`, `regulatory_change`, `requirement_interpretation`, `evidence_acceptance`, `assessment`, `compliance_finding`, `remediation_closure`, `exception`, `transcription` (existing). New ones: register in your module and list in your evidence file.

Event types: `legal.document.extracted` (A→B/C), `legal.contract.obligation_accepted` (B→A creates Obligation), `legal.compliance.finding_accepted` (C→A creates remediation task), `legal.regulatory.change_accepted` (C→C impact campaign, A tasks), `legal.compliance.evidence_expired` (C→A task).

Before T+0:45, B and C build models/pure logic/tests and code against these signatures.

## API surface (all under `/v1/workspaces/{workspace_id}`; session/terms/policy enforced server-side; uniform 404 `legal_resource_unavailable` on deny, as in `legal_scope.py`)

- A: `POST /documents/{id}/versions/{vid}/jobs`, `GET /jobs/{job_id}`, `GET /documents` (paged/filter), `GET /documents/{id}/versions`, `GET /documents/{id}/versions/{vid}/spans`, `GET /documents/{id}/versions/{vid}/original` (hash-verified), `GET /search?q=`, `GET|POST /reviews`, `POST /reviews/{id}/decisions`, `GET /obligations`, `GET|PATCH /tasks`, `GET /notifications`, `GET /audit`, `GET /audit/snapshot?as_of=`, `POST /evidence-packs`, `GET /exports/{id}`
- B: `/contracts`, `/contracts/{id}/versions/{vid}/analysis`, `/clauses`, `/contract-findings`, `/obligation-proposals`, `/playbooks`, `/contracts/{id}/redline?from=&to=`, `/summaries`, `/summaries/{id}/export?format=pdf|docx|json`, `/assistant/questions`, `/conversations`
- C: `/regulatory/sources`, `/regulatory/documents`, `/regulatory/versions`, `/regulatory/changes`, `/regulatory/applicability`, `/regulatory/watchlists`, `/regulatory/campaigns`, `/compliance/requirements`, `/compliance/policies`, `/compliance/controls`, `/compliance/evidence`, `/compliance/mappings`, `/compliance/assessments`, `/compliance/findings`, `/compliance/impact`

Each agent writes exact request/response JSON into its evidence file as soon as a route works — Agent C's frontend codes against those.

## AI policy for this build

No live model execution is authorized. Default analysis profiles are **deterministic** (`legal-contract-deterministic-v1`, etc.: headings/numbering/regex/playbook rules over stored spans). A model-gateway path may exist behind a setting (off by default) and is tested only with a fake gateway returning schema-valid and malicious outputs (forged span IDs, wrong quotes, self-accepted state, injection) — all rejected or `needs_review`. Every output statement cites stored span IDs; unsupported → `needs_review`/refusal.

## Testing (concurrency-safe)

- Each agent uses its **own compose project**: `docker compose -p lrw-<a|b|c> -f infra/docker-compose.legal-core-test.yml run --rm tests python -B -m unittest discover -s tests -p "test_legal_scope_<area>*.py" -v`. Clean up: `docker compose -p lrw-<x> -f infra/docker-compose.legal-core-test.yml down --volumes`.
- Code is mounted read-only from the working tree, so no image rebuild is needed for code changes. Only Agent A rebuilds the image or adds dependencies; others request it.
- New test files: `backend/tests/test_legal_scope_<area>.py` so the full legal-core suite picks them up.
- Frontend: `cd frontend; npm test; npm run lint; npm run build`.
- Failing test first (RED), then implement (GREEN). Never weaken an existing test.

## Git rules (all agents)

- Branch `integration/backend-continuation-20261007`. First verify root and `git remote get-url origin` = `https://github.com/loktrishal-05/legal-compliance-regulatory-workbench.git`; stop if different.
- Commit often, **only your own paths**: `git add <explicit paths>`; never `git add -A`/`git add .`/`commit -a`; never stage `benchmark/`, `.impeccable/`, `.playwright-mcp/`, `docs/.phase11_*`, `claudex-loop/`, `*.log`, the 2026-10-09 plan .md/.pdf (A handles those). If `.git/index.lock` exists, wait a few seconds and retry; never delete it.
- Commit message prefix `[A]`, `[B]`, `[C]`.
- **No push, PR, merge, reset, rebase, stash, checkout of other branches, cherry-pick, or force.** Agent A asks the owner for push authority after the final report.

## Evidence (no shared-doc clobbering)

Each agent records progress only in `docs/parallel/EVIDENCE_<A|B|C>.md`: endpoints + JSON shapes, files, RED/GREEN commands and results, FRs touched, limitations, open gates, "Requests to A/B/C". Agent A alone folds these into `LEGAL_DOMAIN_MIGRATION_PLAN.md`, `MIGRATION_PROGRESS.md`, `VALIDATION_REPORT.md`, `LEGAL_REQUIREMENT_TRACEABILITY.md`, `CLAUDE_HANDOFF.md`, `SESSION_RESUME.md` at checkpoints.

## Timeline (T = start)

| Time | A (Claude) | B (OpenCode) | C (Codex) |
|---|---|---|---|
| 0:00-0:45 | Step 0 verify; migration stubs; review/events/scheduler + 0027; commit "[A] Freeze parallel build contracts" | Read docs/code; contract models + deterministic clause segmenter tests (no migration edit until stubs land) | Read docs/code; regulatory/compliance models + tests over existing pure helpers |
| 0:45-3:00 | Step 1 durable jobs/worker/retry/quotas, blank-region transcription; Step 2 lists/original/spans/search | Step 3 contracts/clauses/parties/playbooks/deviations/missing/redline + review hand-off | Step 4 regulatory registry/versions/changes/applicability/watchlists/campaigns |
| **3:00 checkpoint** | Full legal-core suite; fix shared-file breakage; fold evidence | Report in EVIDENCE_B | Report in EVIDENCE_C |
| 3:00-5:30 | Step 6 obligations/occurrences/tasks/notifications/exceptions; Step 7 remediation, audit query/snapshot/evidence pack/exports, comments | Step 3 summaries/exports/assistant/memory/golden corpus | Step 5 compliance twin/assessments/drift/findings (until ~5:00), then Step 8 frontend |
| 5:30-7:00 | Step 9 cross-tenant/role matrix + injection/forgery; Step 11 journeys 1-6 as backend tests; migrations fresh/0018→0031 | Fix A's integration findings; denial hardening | Step 8 frontend journeys against real APIs |
| 7:00-8:00 | Code freeze; full suite + frontend build; fold docs; final report; ask owner before push | Final EVIDENCE_B | Step 10 decision register/runbooks; final EVIDENCE_C; frontend test/lint/build green |

If behind schedule: keep every Step at a thin, tested, honest slice rather than finishing one Step perfectly and leaving another untouched. Record what's thin.
