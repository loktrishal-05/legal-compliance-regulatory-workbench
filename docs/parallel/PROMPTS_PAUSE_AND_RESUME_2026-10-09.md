# Pause / resume prompts — 2026-10-09 20:45

Supersedes `PROMPT_C_HANDOVER_2026-10-09.md`. The C2 Claude frontend terminal is NOT started, to save Claude usage.

State at 20:45:
- A: Steps 0, 1, 2, 6 and 7 are committed. Step 9 injection/forgery tests are committed. The journeys test is uncommitted.
- B: Step 3 is complete (B1-B10).
- C: Step 4 is committed. Step 5 compliance is uncommitted work in progress: models, schemas, service and one test; migration 0030 is still a stub and the route is not registered. Step 8 frontend and Step 10 docs are not started.
- Shared `router.py` / `models/__init__.py` have uncommitted registration lines for contracts and regulatory.

---

## 1. OpenCode — paste NOW (4% left)
```
Usage limit is nearly reached. Do not start new work. If your current change is GREEN, commit it now with explicit paths only and the [B] prefix. Do NOT commit backend/app/api/router.py, backend/app/db/models/__init__.py or any legal_compliance* file; Agent A handles those. Add one line to docs/parallel/EVIDENCE_B.md: "Paused <time>: last commit <hash>, in-progress <none|what>". Then stop.
```

## 2. Claude builder (Agent A) — paste NOW
```
Owner update: Codex is paused until ~00:40 and OpenCode until ~22:45. Claude usage is at 60%, so be economical: no broad re-reading, and target the tests you run. Finish in this order and commit after each step:
1) Shared registration: run the full legal-core suite (-p "test_legal_scope*.py") with the CURRENT router.py/models __init__ lines for legal_contracts and legal_regulatory (do NOT add legal_compliance; C's untracked compliance files are work in progress and must be left untouched and uncommitted). If green, commit router.py + __init__.py as "[A] Register contract and regulatory routers/models".
2) test_legal_scope_journeys.py: commit the journeys that pass now (1 contract->obligation->summary export, 4 Q&A citation/refusal, 5 restart/revocation/outage, 6 auditor evidence pack). Mark journeys 2 and 3 (compliance-dependent) as skipped with the reason "pending Step 5 compliance (B at ~22:45)". Do not fake them.
3) Migrations: fresh and 0018->0031 upgrade, parity and immutability. Record the results.
4) Fold EVIDENCE_A/B/C into LEGAL_DOMAIN_MIGRATION_PLAN.md, MIGRATION_PROGRESS.md, VALIDATION_REPORT.md and LEGAL_REQUIREMENT_TRACEABILITY.md ("MVP implemented + tested", never "accepted"). Write a PAUSE checkpoint at the top of docs/SESSION_RESUME.md: what is done, what is uncommitted (C's compliance WIP), next owners (B: Step 5 at ~22:45; Codex: frontend + Step 10 at ~00:40; A: final integration). Commit the docs, plus docs/parallel/*.md and docs/product-resources/ as "[A] Pause checkpoint and product resource drafts".
5) Stop. No push. Report test counts to the owner.
```

## 3. OpenCode — paste at reset (~22:45)
```
Resume as Agent B. Read docs/SESSION_RESUME.md (pause checkpoint), docs/parallel/PARALLEL_BUILD_PLAN_2026-10-09.md, docs/parallel/EVIDENCE_A.md and EVIDENCE_C.md, and `git log --oneline -30`. Codex (Agent C) is out of usage. You now own Agent C's Step 5 compliance twin. The spec is the "3:00-5:00 Step 5 compliance twin" section of docs/parallel/PROMPT_C_CODEX_REGULATORY_COMPLIANCE_FRONTEND.md: same rules, migration 0030 only.

C left UNCOMMITTED work in progress. Inspect it first and continue from it, never delete it blindly: backend/app/db/models/legal_compliance.py, schemas/legal_compliance.py, services/legal_compliance.py and tests/test_legal_scope_compliance_persistence.py. Migration 0030 is still a stub, so fill it. Register the model (one line in models/__init__.py) and a new route file api/routes/legal_compliance.py (one line in router.py).

Deliver:
- requirement/interpretation revisions, policy versions, controls
- evidence versions with expiry and acceptance via review target evidence_acceptance
- tenant-qualified mappings and versioned deterministic rules
- frozen assessments with all six states plus reasons and citations
- findings that emit legal.compliance.finding_accepted
- drift/stale projections, and a legal_scheduler evidence-expiry scan emitting legal.compliance.evidence_expired
- an impact traversal endpoint and explainable component status

Test first: `docker compose -p lrw-b ... -p "test_legal_scope_compliance*.py"`. Then un-skip journeys 2 and 3 in tests/test_legal_scope_journeys.py and make them pass. Run the full suite. Commit with "[B/C5]" and explicit paths only. Publish the exact route JSON in docs/parallel/EVIDENCE_C.md under "Step 5 (completed by B)"; the frontend needs it. No push.
```

## 4. Codex — paste at reset (~00:40)
```
Resume as Agent C. Read docs/SESSION_RESUME.md, docs/parallel/PARALLEL_BUILD_PLAN_2026-10-09.md, docs/parallel/PROMPT_C_CODEX_REGULATORY_COMPLIANCE_FRONTEND.md, all docs/parallel/EVIDENCE_*.md files and `git log --oneline -40`. While you were paused, OpenCode finished Step 5 compliance ([B/C5] commits). Do not redo it.

Your job now is the Step 8 frontend (spec: the "5:00-7:00 Step 8 frontend" section of your original prompt), then Step 10 docs. Owned paths: frontend/src/features/legal/** plus additive edits to frontend/src/app/routes.jsx, navigation.js and services/api.js. No backend edits; put backend issues under "Requests to A" in EVIDENCE_C.md.

Build in DEMO-FIRST order, committing "[C]" after each green step (cd frontend; npm test; npm run lint; npm run build):
(1) API client + tests
(2) Legal nav + workspace/matter picker + documents/upload/job status
(3) Source viewer
(4) Contracts + review queue + obligations/tasks (demo journey 1)
(5) Compliance map + six-state badges + evidence expiry (demo journey 2)
(6) Summaries/assistant with citations
(7) Regulatory registry/diff/applicability
(8) Audit timeline/evidence pack
(9) Honest dashboard

Real APIs only; honest "not available yet" states; accessible, responsive, no new dependencies. Finally write docs/parallel/PILOT_DECISION_REGISTER.md and RUNBOOKS.md (Step 10). No push.
```

## 5. Claude (Agent A) — final integration after Codex has been running ~2 h
```
Final integration as Agent A. Read docs/SESSION_RESUME.md and all EVIDENCE files, plus `git log` since the pause. Run: the full legal-core suite, fresh and 0018->0031 migrations, and cd frontend; npm test; npm run lint; npm run build. Fix shared-file breakage only. Fold the evidence into the living docs, list the open gates, update SESSION_RESUME/CLAUDE_HANDOFF and commit. Show the owner the final report and ask before any push or PR.
```
