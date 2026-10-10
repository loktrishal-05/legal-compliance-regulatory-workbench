# Agent C evidence — 2026-10-09

Status: Step 4 bounded persistence slice tested; Step 5 in progress; Step 8/10 pending. No full FR/pilot acceptance claimed.

Scope: regulatory/compliance owned models, schemas, services, routes and tests; migrations 0029/0030 only after A commits stubs; legal frontend and additive route/nav/API integration; pilot decision and runbook drafts. Existing pure helpers, policy, intake, extraction, shell and UI will be reused. No dependencies, live models, deployment or remote operations.

Boundary verified: authorized root/origin, branch integration/backend-continuation-20261007 at b3b6a71; root/common metadata .git; only sample hooks. Historical external worktree metadata is untouched. Existing benchmark/nested/untracked artifacts preserved.

## Checks

`docker compose -p lrw-c -f infra/docker-compose.legal-core-test.yml run --rm tests python -B -m unittest discover -s tests -p "test_legal_scope_regulatory*.py" -v`: RED (missing legal_regulatory_projection), then GREEN **4/4**. Tests cover historical knowledge cutoff, unknown effectivity, fixture amendment/reorder/add/remove and manual freshness/outage. No persistence/API acceptance yet. Migration stubs and cross-agent services are not present at initial inspection.

Files: `legal_regulatory_projection.py`, `test_legal_scope_regulatory_projection.py`, synthetic fixture README and retention-v1/v2 JSON. Existing pure helpers unchanged. Next: scoped registry/version models and service persistence tests.

Compliance snapshot RED: missing `legal_compliance_snapshot`; GREEN **4/4** using `docker compose -p lrw-c -f infra/docker-compose.legal-core-test.yml run --rm tests python -B -m unittest discover -s tests -p "test_legal_scope_compliance*.py" -v`. Reuses existing six-state evaluator; covers all states, conflicting evidence, future validity/exclusive expiry and unchanged historical snapshot versus stale current projection. These are trusted-input adapter tests, not evidence-acceptance/API/persistence acceptance. Files: `legal_compliance_snapshot.py`, `test_legal_scope_compliance_snapshot.py`.

Regulatory persistence: **21/21** service/projection checks pass (SQLite and disposable PostgreSQL). Includes real clean synthetic intake/extraction, registry independent review, source verification, replay, immutable ORM versions, forged-hash/self-review denial, unknown-effective applicability denial, audit rollback and one campaign/event per accepted change. Subsequent HTTP checks pending at this update. Original RED tuple diff was incompatible with canonical hashing; adapter now emits JSON lists. Audit integration uses A's existing `LEGAL_ACTIVITY_RECORDED` with `domain: regulatory`, not new audit types. Initial audit-allowlist blocker resolved without weakening checks.

`python -B -m scripts.validate_legal_migrations` in lrw-c: **fresh and 0018 -> head PASS**, ORM parity/repeat upgrades/legacy preservation. Initial unconditional 0029 downgrade refusal broke the empty-table rollback check; replaced with row-presence guards, retaining refusal for any regulatory data. This shared validator does not yet specifically attack new regulatory DB triggers; that remains a required follow-up.

Current thin boundaries: change proposals are deterministic observations with stored citations, not semantic legal interpretations; imported ordinal/locator sections can miss semantic reordering without stable section labels. Campaign is persisted idempotently but affected links await compliance integration. Source freshness scanner registered, manual import only; no configured feed. Independent review target names: `regulatory_source`, `regulatory_change`, `regulatory_applicability`. Worker must import C services for target/scan registration.

## Regulatory API contract

Latest regulatory command: **23/23 PASS**, including real cookie/terms/middleware HTTP registry/list/denial checks on migrated disposable PostgreSQL. Starlette's existing httpx deprecation warning remains. Shared `models/__init__.py` currently includes B's uncommitted contract import as well as C's import; C does not stage B's line. Integrator must preserve/register both.

Prefix `/v1/workspaces/{workspace_id}/regulatory`. Authenticated cookie, current terms and scoped policy required. Denial: HTTP 404 `{"detail":{"code":"legal_resource_unavailable"}}`. Unknown/extra proposal fields: 422. Conflicting retry: 409. All IDs below are illustrative UUID placeholders, not live records. Response fields are actual ORM serialization; timestamps use ISO 8601, dates YYYY-MM-DD, null stays null.

GET `/sources|documents|versions|changes|applicability|watchlists|campaigns?offset=0&limit=50` returns `{"items":[],"has_more":false,"next_offset":null}` when empty. Nonempty `items` contain the corresponding POST response below, with review_state (`approved` or `not_approved`) additionally on sources/changes/applicability. Paging follows authorization filtering. Registry metadata is workspace-visible; version/diff/applicability/campaign source content requires document grants.

POST `/sources` request:
```json
{"name":"SYNTHETIC Registry","jurisdiction":"SYNTHETIC","authority_tier":"unverified","owner_id":"<UUID>"}
```
Response 201:
```json
{"id":"<UUID>","created_at":"<timestamp>","organization_id":"<UUID>","workspace_id":"<UUID>","owner_id":"<UUID>","actor_id":"<UUID>","name":"SYNTHETIC Registry","jurisdiction":"SYNTHETIC","authority_tier":"unverified","trust_state":"proposed","import_policy":"manual","revision_sha256":"<64-hex>","last_success_at":null,"last_failure_at":null,"last_check_at":null}
```
POST `/documents` request and 201 response:
```json
{"source_id":"<UUID>","title":"SYNTHETIC Data Retention Regulation"}
```
```json
{"id":"<UUID>","created_at":"<timestamp>","organization_id":"<UUID>","workspace_id":"<UUID>","source_id":"<UUID>","title":"SYNTHETIC Data Retention Regulation"}
```
POST `/versions` binds bytes already received/extracted through the governed document APIs. Source registry must have exact-revision approval. Request and 201 response:
```json
{"regulatory_document_id":"<UUID>","document_id":"<UUID>","version_id":"<UUID>","extraction_id":"<UUID>","published_at":"2026-09-01","effective_from":null,"effective_until":null,"amends_id":null,"supersedes_id":null}
```
```json
{"id":"<UUID>","created_at":"<timestamp>","organization_id":"<UUID>","workspace_id":"<UUID>","regulatory_document_id":"<UUID>","document_id":"<UUID>","version_id":"<UUID>","extraction_id":"<UUID>","source_sha256":"<64-hex>","actor_id":"<UUID>","published_at":"2026-09-01","effective_from":null,"effective_until":null,"imported_at":"<timestamp>","amends_id":null,"supersedes_id":null}
```
GET `/versions/as-of?regulatory_document_id=<UUID>&effective_on=2026-10-09&known_at=2026-10-09T12:00:00Z`:
```json
{"status":"needs_verification","version_id":null,"reasons":["<UUID>: effective_from unknown"],"effective_on":"2026-10-09","known_at":"2026-10-09T12:00:00+00:00"}
```
POST `/changes` request and 201 response:
```json
{"from_version_id":"<UUID>","to_version_id":"<UUID>"}
```
```json
{"id":"<UUID>","created_at":"<timestamp>","organization_id":"<UUID>","workspace_id":"<UUID>","regulatory_document_id":"<UUID>","from_version_id":"<UUID>","to_version_id":"<UUID>","actor_id":"<UUID>","exact_diff":[{"section_ref":"1","kind":"modified","text_diff":["--- old","+++ new","@@ -1 +1 @@","-Old text","+New text"]}],"semantic_proposal":{"kind":"observation","profile":"regulatory-exact-v1","review_required":true,"text":"Exact source differences require human materiality and applicability review.","citations":[{"span_id":"<UUID>","extraction_id":"<UUID>","document_id":"<UUID>","version_id":"<UUID>","source_sha256":"<64-hex>","artifact_sha256":"<64-hex>","quote":"Old text","start":0,"end":8,"locator":{"kind":"line","line":1,"offset_unit":"unicode_codepoint"},"status":"ready","warnings":[]}],"uncertainties":["No semantic legal interpretation performed."]},"revision_sha256":"<64-hex>"}
```
POST `/applicability` request and 201 response:
```json
{"regulatory_version_id":"<UUID>","state":"applicable","jurisdiction":"SYNTHETIC","entity":"Synthetic entity","product":"Synthetic product","business_unit":"Synthetic unit","effective_on":"2026-10-09","rationale":"Synthetic applicability proposal"}
```
```json
{"id":"<UUID>","created_at":"<timestamp>","organization_id":"<UUID>","workspace_id":"<UUID>","regulatory_version_id":"<UUID>","actor_id":"<UUID>","state":"applicable","jurisdiction":"SYNTHETIC","entity":"Synthetic entity","product":"Synthetic product","business_unit":"Synthetic unit","effective_on":"2026-10-09","rationale":"Synthetic applicability proposal","revision_sha256":"<64-hex>"}
```
The state is a proposal; approval comes only through A's `/reviews` exact-revision ledger. Unknown/out-of-interval effectivity blocks approval.

POST `/watchlists` request and 201 response:
```json
{"source_id":"<UUID>","max_age_days":7}
```
```json
{"id":"<UUID>","created_at":"<timestamp>","organization_id":"<UUID>","workspace_id":"<UUID>","source_id":"<UUID>","owner_id":"<UUID>","max_age_days":7}
```
GET watchlist items additionally carry:
```json
{"monitoring":"not_monitored","import_policy":"manual","freshness":"never_checked","reason":"no successful import or check recorded"}
```
GET `/campaigns` item:
```json
{"id":"<UUID>","created_at":"<timestamp>","organization_id":"<UUID>","workspace_id":"<UUID>","change_id":"<UUID>","affected":[]}
```
No POST campaign endpoint: independent approved change persists it and emits `legal.regulatory.change_accepted` in the decision transaction.

## Requests to A

- **Resolved audit blocker:** C adopted A's `LEGAL_ACTIVITY_RECORDED`, with domain/operation/object metadata. No additional audit names needed.
- C needs review target `regulatory_source` in addition to the allocated targets, to approve an exact registry revision independently before manual imports. Registry approval is never accepted from client fields.

- Register C tables in migration parity validation when models land; C cannot edit the shared validator.
- Provide a legal domain audit event type (and exclude it from legacy audit reads) for regulatory/compliance transactional writes. Current audit type allowlist and legal-policy audit exclusion are A-owned. Proposed names: LEGAL_REGULATORY_RECORDED and LEGAL_COMPLIANCE_RECORDED.
- Confirm review target authorization supports current document grants on source-bound targets, not membership alone; C will register exact-revision targets and recheck source permissions in approval callbacks.
- Fold this evidence into the living guide/progress/validation/handoff at integration checkpoints. Latest owner instruction authorizes C frontend implementation, superseding earlier frontend prohibition.

## Open gates

Independent human/legal approval, enterprise identity, operational source packs, deployment/recovery and live-model quality remain unaccepted. No routes or persistence delivered yet.

## Step 5 (completed by A) — compliance persistence, migration 0030 and API

Commit a47447f. C models/schemas/service kept as written; A filled migration 0030 from the models (12 tables, workspace-qualified FKs, append-only triggers on requirements, interpretations, policy versions, evidence versions, mappings, rules, assessments, findings, reevaluations; downgrade refuses with data). Validator PASS fresh and 0018 -> 0031. Evidence-expiry scan `compliance_evidence_expiry` (C) is registered with `legal_scheduler`. Full legal-core 376/376 OK; `test_legal_scope_compliance_api.py` 3/3 (PG HTTP).

Prefix `/v1/workspaces/{workspace_id}/compliance`; cookie + current terms + scoped policy; deny/unknown → 404 `{"detail":{"code":"legal_resource_unavailable"}}`; extra fields (e.g. client `status`) → 422; conflicts → 409 `{"detail":{"code":"..."}}`. Approval only through `POST /reviews` (targets `requirement_interpretation`, `compliance_rule`, `evidence_acceptance`, `assessment`, `compliance_finding`).

POST bodies (201 returns the stored row with all columns; reviewable resources add `"review_state":"approved|not_approved"`):

```json
POST /requirements      {"regulatory_version_id":"<uuid>","title":"Synthetic retention duty"}
POST /interpretations   {"requirement_id":"<uuid>","text":"Approved reading","span_ids":["<stored span uuid>"]}
POST /policies          {"title":"Records policy"}
POST /policy-versions   {"policy_id":"<uuid>","document_id":"<uuid>","version_id":"<uuid>"}
POST /controls          {"title":"Retention control","description":"Retain records","owner_id":"<member uuid>"}
POST /evidence          {"title":"Synthetic proof"}
POST /evidence-versions {"evidence_id":"<uuid>","document_id":"<uuid>","version_id":"<uuid>","observed_at":"2026-10-09T10:00:00Z","valid_from":"2026-10-09T10:00:00Z","expires_at":"2027-10-09T10:00:00Z","replaces_id":null,"facts":{"retention_years":7},"span_ids":["<uuid>"]}
POST /mappings          {"requirement_id":"<uuid>","control_id":"<uuid>","policy_version_id":null,"evidence_version_id":"<uuid>"}
POST /rules             {"control_id":"<uuid>","interpretation_id":"<uuid>","checks":[{"fact":"retention_years","op":"ge","value":7}]}
POST /assessments       {"requirement_id":"<uuid>","applicability_id":"<uuid>"}
POST /findings          {"assessment_id":"<uuid>","text":"Synthetic gap"}
```

Assessment response (stored immutable snapshot):
```json
{"id":"<uuid>","organization_id":"<uuid>","workspace_id":"<uuid>","requirement_id":"<uuid>","applicability_id":"<uuid>","actor_id":"<uuid>","evaluated_at":"<ts>","inputs":{"components":[...]},"result":{"status":"satisfied","reasons":[],"components":[...]},"status":"satisfied|partially_satisfied|unsatisfied|insufficient_evidence|not_applicable|needs_review","revision_sha256":"<hex>","created_at":"<ts>","review_state":"not_approved"}
```

`GET /{resource}?offset=0&limit=50` for requirements|interpretations|policies|policy-versions|controls|evidence|evidence-versions|mappings|rules|assessments|findings|reevaluations → `{"items":[row...],"has_more":false,"next_offset":null}` (denied rows never counted).

`GET /assessments/{id}/current` → `{"assessment":{stored row},"current":{"status":"...","reasons":["..."],"freshness":"stale|...","review_state":"approved|not_approved", ...}}` — evidence expiry/replacement or accepted change marks `freshness:"stale"` with reasons; the stored snapshot is never rewritten.

`GET /impact?changed_id=<requirement|control|policy|evidence uuid>` → `{"changed_id":"<uuid>","paths":[{"id":"<uuid>","kind":"requirement|control|policy|evidence|regulatory_version","path":["<uuid>", "..."]}]}`.

Over HTTP the tests show insufficient_evidence → satisfied → stale after real expiry, unsatisfied for failing facts, cross-tenant/unknown 404, forged client status 422. All six evaluator states are covered in `test_legal_scope_compliance_snapshot.py`.
