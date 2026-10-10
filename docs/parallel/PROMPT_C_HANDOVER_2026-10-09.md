# Agent C handover (Codex hit its usage limit at ~20:20; resets ~00:00)

Agent C's remaining work is split so nothing waits 3.5 hours:

| Work | New owner | Prompt |
|---|---|---|
| Step 5 compliance twin (finish C's uncommitted files) | **B — OpenCode** | Prompt 1 below, pasted into the OpenCode session **after** its current task commits |
| Step 8 legal frontend | **New Claude Code terminal ("C2")** | Prompt 2 below |
| Step 10 decision register/runbooks + frontend tests/polish | **Codex after reset** | Prompt 3 below |

---

## Prompt 1 — paste into OpenCode (Agent B)

```
Owner update: Codex (Agent C) hit its usage limit. You now also own Agent C's Step 5 compliance work, as an additional owner of C's backend paths. First finish and commit your current task.

Then read docs/parallel/PARALLEL_BUILD_PLAN_2026-10-09.md, docs/parallel/PROMPT_C_CODEX_REGULATORY_COMPLIANCE_FRONTEND.md (the "3:00-5:00 Step 5 compliance twin" section is now YOURS, with the same rules and tests), and docs/parallel/EVIDENCE_C.md.

C left UNCOMMITTED in-progress work. Do not delete or overwrite it blindly. Inspect it first with `git status --short` and `git diff`: backend/app/db/models/legal_compliance.py, backend/app/schemas/legal_compliance.py, backend/app/services/legal_compliance.py, any backend/tests/test_legal_scope_compliance*.py, migration backend/alembic/versions/0030_legal_compliance.py, and C's lines in backend/app/db/models/__init__.py. Continue from it. backend/app/db/models/legal_obligations.py belongs to Agent A; don't touch it.

Deliver Step 5 fully: requirements/interpretation revisions, policy versions, controls, evidence versions with expiry and review-based acceptance, tenant-qualified mappings, versioned deterministic rules, frozen assessment snapshots with all six states plus reasons and citations, findings that emit legal.compliance.finding_accepted, drift/stale projections, a legal_scheduler evidence-expiry scan emitting legal.compliance.evidence_expired, an impact traversal endpoint, and explainable component status (no guessed weights). Use migration 0030 only, test first, and run `docker compose -p lrw-b ...` with -p "test_legal_scope_compliance*.py". Commit with the prefix "[B/C5]" and explicit paths only. Record routes with exact JSON request/response shapes in docs/parallel/EVIDENCE_C.md under a new heading "Step 5 (completed by B)", because the frontend agent builds from it. No push.
```

## Prompt 2 — paste into a NEW Claude Code terminal (Agent C2, frontend)

```
You are Agent C2: legal frontend (Step 8) for C:\Users\Lohith k\Desktop\OLD hard work\legal-compliance-regulatory-workbench. Agents A (Claude) and B (OpenCode) are working in the same directory and branch right now. The owner authorizes you to implement the frontend and make local commits. No push, PR, merge, reset, rebase, stash, cherry-pick or branch switch.

Read: AGENTS.md; docs/parallel/PARALLEL_BUILD_PLAN_2026-10-09.md (git/test/ownership rules); docs/parallel/PROMPT_C_CODEX_REGULATORY_COMPLIANCE_FRONTEND.md, section "5:00-7:00 Step 8 frontend". That section is your full spec. Follow it exactly. Also read PRODUCT.md, DESIGN.md, and docs/parallel/EVIDENCE_A.md, EVIDENCE_B.md and EVIDENCE_C.md for the real endpoint JSON shapes.

Inspect before writing: frontend/src/app/routes.jsx, navigation.js, AppShell.jsx, session.jsx, components/ui.jsx, services/api.js and their tests, plus an existing feature folder for patterns.

Owned paths: frontend/src/features/legal/** and additive edits to frontend/src/app/routes.jsx, navigation.js and services/api.js. Never edit backend files. If an API is missing or wrong, write it under "Requests to A/B" in docs/parallel/EVIDENCE_C2.md. Build the page with an honest "not available yet" state; never use mock data or fake metrics.

Build in this order, committing after each green step with the prefix "[C2]" and explicit paths only:
(1) API client functions + tests
(2) Legal nav group + workspace/matter picker + documents/upload/job progress
(3) Source viewer with spans/corrections
(4) Contracts, summaries (citations jump to source), assistant
(5) Review queue
(6) Regulatory registry/diff/applicability/watchlists/campaigns
(7) Compliance map/six-state badges/evidence expiry/findings
(8) Obligations/tasks/notifications
(9) Audit timeline/evidence pack/exports
(10) Honest dashboard

Every page needs loading/empty/error/denied/degraded states, keyboard focus, labelled forms, semantic tables, and must be responsive. No new npm dependencies. The /app area stays light and calm, as PRODUCT.md says.

Checks after each step: cd frontend; npm test; npm run lint; npm run build. Keep docs/parallel/EVIDENCE_C2.md current with files, commands/results, FRs covered, limitations and open gates.
```

## Prompt 3 — paste into Codex after its limit resets (~00:00)

```
You are Agent C again (Codex), after a usage-limit pause. Your earlier work is committed as [C] commits. Since then: Step 5 compliance was completed by OpenCode ([B/C5] commits, recorded in docs/parallel/EVIDENCE_C.md), and the frontend is being built by a Claude terminal ([C2] commits, recorded in docs/parallel/EVIDENCE_C2.md). Do NOT redo or overwrite their work.

Read AGENTS.md, docs/parallel/PARALLEL_BUILD_PLAN_2026-10-09.md, docs/parallel/PROMPT_C_CODEX_REGULATORY_COMPLIANCE_FRONTEND.md, all docs/parallel/EVIDENCE_*.md files and `git log --oneline -40`.

Your remaining tasks:
(1) Step 10: write docs/parallel/PILOT_DECISION_REGISTER.md and docs/parallel/RUNBOOKS.md exactly as specified in your original prompt.
(2) Run the regulatory tests (`docker compose -p lrw-c ... -p "test_legal_scope_regulatory*.py"`) and fix anything Agent A lists under "Requests to C" in EVIDENCE_A.md.
(3) Only if the C2 terminal has stopped (check its last commit time and EVIDENCE_C2.md): pick up its remaining unchecked frontend pages from that list, the same way.

Commit with the prefix "[C]" and explicit paths only. No push. Update EVIDENCE_C.md.
```
