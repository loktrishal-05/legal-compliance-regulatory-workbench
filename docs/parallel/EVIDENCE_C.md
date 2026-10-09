# Agent C evidence — 2026-10-09

Status: Step 4 started; Step 5/8/10 pending. No feature acceptance claimed.

Scope: regulatory/compliance owned models, schemas, services, routes and tests; migrations 0029/0030 only after A commits stubs; legal frontend and additive route/nav/API integration; pilot decision and runbook drafts. Existing pure helpers, policy, intake, extraction, shell and UI will be reused. No dependencies, live models, deployment or remote operations.

Boundary verified: authorized root/origin, branch integration/backend-continuation-20261007 at b3b6a71; root/common metadata .git; only sample hooks. Historical external worktree metadata is untouched. Existing benchmark/nested/untracked artifacts preserved.

## Checks

`docker compose -p lrw-c -f infra/docker-compose.legal-core-test.yml run --rm tests python -B -m unittest discover -s tests -p "test_legal_scope_regulatory*.py" -v`: RED (missing legal_regulatory_projection), then GREEN **4/4**. Tests cover historical knowledge cutoff, unknown effectivity, fixture amendment/reorder/add/remove and manual freshness/outage. No persistence/API acceptance yet. Migration stubs and cross-agent services are not present at initial inspection.

Files: `legal_regulatory_projection.py`, `test_legal_scope_regulatory_projection.py`, synthetic fixture README and retention-v1/v2 JSON. Existing pure helpers unchanged. Next: scoped registry/version models and service persistence tests.

## Requests to A

- Register C tables in migration parity validation when models land; C cannot edit the shared validator.
- Provide a legal domain audit event type (and exclude it from legacy audit reads) for regulatory/compliance transactional writes. Current audit type allowlist and legal-policy audit exclusion are A-owned. Proposed names: LEGAL_REGULATORY_RECORDED and LEGAL_COMPLIANCE_RECORDED.
- Confirm review target authorization supports current document grants on source-bound targets, not membership alone; C will register exact-revision targets and recheck source permissions in approval callbacks.
- Fold this evidence into the living guide/progress/validation/handoff at integration checkpoints. Latest owner instruction authorizes C frontend implementation, superseding earlier frontend prohibition.

## Open gates

Independent human/legal approval, enterprise identity, operational source packs, deployment/recovery and live-model quality remain unaccepted. No routes or persistence delivered yet.
