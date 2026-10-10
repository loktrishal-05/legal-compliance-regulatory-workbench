# Rebalanced prompts — 2026-10-09 21:00 (supersedes prompts #3/#4 in PROMPTS_PAUSE_AND_RESUME)

Verified state at 20:57: the freeze commit reports legal-core 363/363 and journeys 12/12 (J2/J3 run against C's UNCOMMITTED compliance files). Still uncommitted:
- the shared registration lines in `router.py`/`models/__init__.py`
- B's last test-hardening edits (`legal_contract_analysis.py` and 4 test files, plus `fixtures/legal_contracts/check_coverage.py`)
- C's compliance files; migration 0030 is still a stub and there is no compliance route

Step 8 frontend and Step 10 docs are not started.

New split:
- **Claude** now: secure the uncommitted work, finish Step 5, build the frontend foundation and the contract journey pages.
- **OpenCode** at ~22:45: compliance, regulatory, summaries and assistant pages.
- **Codex** at ~00:40: obligations, audit and dashboard pages, Step 10 docs, and an accessibility pass.

The frontend is split by page folder so nobody edits the same page file.

---

## 1. Claude Code builder — paste NOW
```
Owner update: Codex and OpenCode are out of usage. You have limited Claude credit left, so be economical: target your tests and avoid broad re-reading. You now take over unfinished B/C work, in this order. Commit after each step with explicit paths only. No push.

1) Secure uncommitted work. Run the full legal-core suite (docker compose -p lrw-a ... -p "test_legal_scope*.py").
   - If green: commit backend/app/api/router.py + backend/app/db/models/__init__.py as "[A] Register contract and regulatory routers/models".
   - Then commit B's pending edits (backend/app/services/legal_contract_analysis.py, backend/tests/test_legal_scope_{assistant,contracts_advanced,contracts_api,summaries}.py, backend/tests/fixtures/legal_contracts/check_coverage.py) as "[B] Contract/summary/assistant hardening (committed by A)".
   - If anything is red, fix the root cause; don't commit a red state.

2) Finish Step 5 compliance from C's uncommitted files (backend/app/db/models/legal_compliance.py, schemas/legal_compliance.py, services/legal_compliance.py, tests/test_legal_scope_compliance_persistence.py). Don't rewrite what works.
   - Fill migration 0030_legal_compliance from the models: tenant FKs, immutability triggers like 0024/0025, and the migration validator must PASS fresh and 0018->0031.
   - Add api/routes/legal_compliance.py (requirements, policies, controls, evidence, mappings, assessments, findings, impact) using the legal_scope uniform-404 pattern, register it with one line in router.py and one in models/__init__.py, and add a legal_scheduler evidence-expiry scan if one is missing.
   - Add HTTP tests: six states, cross-tenant denial, expiry -> stale.
   - Commit as "[A/C5] Complete compliance persistence, migration 0030 and API".
   - Publish the exact JSON for each route in docs/parallel/EVIDENCE_C.md under "Step 5 (completed by A)".

3) Frontend foundation and contract journey (Step 8). Spec: the "Step 8 frontend" section of docs/parallel/PROMPT_C_CODEX_REGULATORY_COMPLIANCE_FRONTEND.md. Read PRODUCT.md and DESIGN.md (the /app area stays light and calm). Inspect routes.jsx, navigation.js, AppShell.jsx, session.jsx, components/ui.jsx and services/api.js first.
   Build, in order, under frontend/src/features/legal/:
   a) shared/: a legal API client (all A/B/C endpoints, shapes from EVIDENCE_A/B/C) + tests, a WorkspaceContext + workspace/matter picker, and shared state components (loading/empty/error/denied/degraded) plus a citation-link component
   b) a "Legal" navigation group placed first, with routes for every planned page; pages not built yet show an honest "coming in this build" state
   c) documents/: list, upload, quarantine reason, job status/retry, versions
   d) source/: span list, exact quote, page/region, correction propose/decide, corrected vs original
   e) contracts/: list, analysis (clauses/parties/findings/obligation proposals), redline, submit for review
   f) reviews/: the queue with approve/reject/request changes/escalate
   Commit "[A/C8]" after each green step (cd frontend; npm test; npm run lint; npm run build). No new dependencies, no mock data.

4) Before your credit runs out, record in docs/parallel/EVIDENCE_C8.md which pages are done, which shared components/hooks exist and how to use them, plus the remaining page list. Then stop.
```

## 2. OpenCode — paste at reset (~22:45)
```
Resume as Agent B. Read docs/SESSION_RESUME.md, docs/parallel/PROMPTS_REBALANCE_2026-10-09_2100.md, docs/parallel/EVIDENCE_C8.md, EVIDENCE_C.md and EVIDENCE_B.md, and `git log --oneline -30`. Claude committed your pending edits, finished Step 5 compliance, and built the legal frontend foundation ([A/C8] commits). Reuse its shared API client, WorkspaceContext, state components and citation link. Don't duplicate them.

Your job: frontend pages (Step 8, spec in docs/parallel/PROMPT_C_CODEX_REGULATORY_COMPLIANCE_FRONTEND.md), only in these folders: frontend/src/features/legal/compliance/, regulatory/, summaries/, assistant/. Swap each page's "coming in this build" placeholder route for your page; edit only those route lines.
- compliance: requirement->control->evidence map, six-state badge with reasons and citations, evidence expiry/stale, findings -> remediation link, impact view
- regulatory: source registry/approval, versions, diff, applicability decision, watchlist freshness ("not monitored", never "no change"), campaigns
- summaries: profile/audience, statements with citation links to the source, coverage/uncertainty, approved-only export
- assistant: cited answers with fact/observation/interpretation/recommendation labels, refusal/degraded state, conversation history with delete

Every page needs loading/empty/error/denied/degraded states, keyboard focus, labelled forms, semantic tables, and must be responsive. Real APIs only.

If a backend route misbehaves, fix it in your own B-owned backend files, or write it under "Requests to A" in EVIDENCE_C8.md.

Commit "[B/C8]" after each green step (cd frontend; npm test; npm run lint; npm run build). Update EVIDENCE_C8.md. No push.
```

## 3. Codex — paste at reset (~00:40)
```
Resume as Agent C. Read docs/SESSION_RESUME.md, docs/parallel/PROMPTS_REBALANCE_2026-10-09_2100.md, docs/parallel/EVIDENCE_C8.md and all other EVIDENCE files, and `git log --oneline -40`. While you were paused: Claude finished your Step 5 compliance and built the frontend foundation and the documents/source/contracts/reviews pages ([A/C8]). OpenCode built the compliance/regulatory/summaries/assistant pages ([B/C8]). Do not redo or restyle their work.

Your tasks:
1) Pages in frontend/src/features/legal/obligations/, audit/ and dashboard/:
   - obligations/tasks/calendar list with dependencies, overdue and reassignment; notifications with read state; exceptions with expiry
   - audit timeline with filters, as-of snapshot, evidence pack create/download, JSON findings export
   - an honest dashboard of permitted aggregates from real APIs only
   Replace only those placeholder routes.
2) Accessibility/responsive pass across all legal pages: focus order, labels, headings, table semantics, 320px reflow. Fix issues with minimal edits.
3) Step 10: docs/parallel/PILOT_DECISION_REGISTER.md and RUNBOOKS.md, as specified in your original prompt.

Commit "[C]" after each green step (cd frontend; npm test; npm run lint; npm run build). Update EVIDENCE_C8.md. No push.
```

## 4. Claude — final integration (after Codex has run ~1.5-2 h)
Use prompt #5 in `PROMPTS_PAUSE_AND_RESUME_2026-10-09.md`.
