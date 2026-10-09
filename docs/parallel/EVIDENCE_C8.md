# EVIDENCE_C8 — Step 8 legal frontend (shared handoff file for A, B and C)

Started by agent A (Claude) 2026-10-09 per `docs/parallel/PROMPTS_REBALANCE_2026-10-09_2100.md`. Frontend checks after every step: `cd frontend; npm test; npm run lint; npm run build` → 52/52 tests, 0 lint errors (2 pre-existing warnings in `src/app/session.jsx`), build OK. No new dependencies, no mock data.

## Commits by A

| Commit | Content |
|---|---|
| 0d2eb7b / 2e4d0b9 | Secured shared registrations and B pending hardening (suite 373/373 before commit) |
| a47447f / 59eab20 | Step 5 compliance completed: migration 0030, `/compliance` API, HTTP tests, contract in EVIDENCE_C (suite 376/376) |
| 874fc7e | Backend `GET /v1/workspaces` — caller's own authorized workspaces (picker source) |
| 3055716 | Shared client/context/states + Legal nav group (first) + placeholder routes |
| b36d30f | documents page |
| 0667e74 | source viewer |
| 4e74ffe | contracts page |
| 38c84d1 | review queue |

## Pages done (A)

| Route `/app/legal/...` | File | Covers |
|---|---|---|
| `documents` | `features/legal/documents/DocumentsPage.jsx` | permitted list + filters (no counts), raw-body upload with status/quarantine reasons, versions with hash, extraction job submit/refresh/retry, open source, original download (blocked when quarantined) |
| `source?document=&version=&span=` | `features/legal/source/SourcePage.jsx` | span list with exact quote + locator, select span, propose transcription correction (quote SHA-256 bound), decide correction by ID (original vs proposed side by side), blank-region transcription + submit for review, labelled corrected projection (never replaces original) |
| `contracts` | `features/legal/contracts/ContractsPage.jsx` | permitted contracts, register from document version, run/read deterministic analysis, parties/clauses/findings/obligation proposals with citation links, submit finding/obligation for review, exact redline between versions |
| `reviews` | `features/legal/reviews/ReviewsPage.jsx` | queue with status/target filters, exact revision hash, decision history, approve/reject/request changes/escalate; self-review hidden (server still enforces) |

## Shared pieces — reuse, do not duplicate

`features/legal/shared/legalApi.js` (plain JS, tested in `legalApi.test.js`):
- `legalPaths(workspaceId)` → every A/B/C path builder: `documents(params)`, `versions(d)`, `jobs(d,v)`, `job(id)`, `spans(d,v,params)`, `projection(d,v)`, `proposeCorrection`, `correction`, `decideCorrection`, `regionTranscription`, `search(q)`, `reviews(params)`, `decide(id)`, `obligations(params)`, `tasks(params)`, `notifications(params)`, `audit(params)`, `snapshot(asOf)`, `evidencePacks`, `exportItem(id)`, `contracts`, `contractVersions`, `analysis`, `redline`, `obligationProposals`, `submitObligation`, `submitFinding`, `summaries`, `assistant`, `conversations`, `regulatory(resource)`, `compliance(resource)`, `assessmentCurrent(id)`.
- `query(path, params)` (drops empty values), `nextOffsetPage` (for A lists `{items,has_more,limit,offset}`; use `nextPage.envelope` from `services/api.js` for C lists `{items,has_more,next_offset}`), `newIdempotencyKey()`, `problemKind(error)` → `denied|terms|session|conflict|invalid|busy|degraded|error`, `conflictCode`, `canDecide(review, userId)`, `citationHref(citation)`, `locatorLabel(locator)`, `shortHash`, `sha256Hex(text)`, `uploadDocument(...)`, `legal.get/post/patch/remove`, `REVIEW_DECISIONS`, `REVIEW_STATUS`, `JOB_TERMINAL`.

`features/legal/shared/workspace.js`: `useWorkspace()` → `{workspaces, workspace:{workspace_id,name,role,organization_id}, select, status, error, reload}`. Every page under `/app/legal` is rendered inside `LegalLayout`, so `workspace` is always set there.

`features/legal/shared/LegalShared.jsx`: `LegalLayout` (route element), `WorkspacePicker`, `LegalProblem({error, onRetry, what})` (uniform-404 shown as "does not exist or you do not currently have access", degraded/terms/conflict/busy states), `LegalResource({resource, empty, emptyMessage, what, children: data => ...})` for `useResource` results, `CitationLink({citation})` (links to the source viewer at the exact span), `ReviewBadge({status})`, `ComingInThisBuild`.

Hooks: reuse `useResource`, `useRequest`, `usePaged` from `src/hooks/useApi.js`; `ListState` and `PageHeader` from `src/components/ui.jsx`.

Page pattern: `const { workspace } = useWorkspace(); const paths = useMemo(() => legalPaths(workspace.workspace_id), [workspace.workspace_id])`, then `useResource(paths.x)` + `<LegalResource>` or `usePaged(path, nextPage.envelope)` + `<ListState>`. Mutations: `useRequest().run(path, { method: 'POST', body })`, show errors with `<LegalProblem>`. Semantic tables (`table-scroll` > `table` with `th scope`), labelled inputs, `aria-live` result regions.

## Routing

`frontend/src/app/routes.jsx` has ONE line per legal page: `legalPage('<path>', placeholders, '<Name>Placeholder', '<Title>')`. To ship a page replace only that line with `legalPage('<path>', () => import('../features/legal/<folder>/<Page>.jsx'), '<Page>', '<Title>')`. Navigation (`navigation.js`) already lists every page in the Legal group.

## Remaining pages

- **B (OpenCode)**: `compliance/` (route `compliance`, placeholder `CompliancePlaceholder`), `regulatory/` (`RegulatoryPlaceholder`), `summaries/` (`SummariesPlaceholder`), `assistant/` (`AssistantPlaceholder`). Compliance API contract: EVIDENCE_C "Step 5 (completed by A)"; regulatory: EVIDENCE_C "Regulatory API contract"; summaries/assistant: EVIDENCE_B.
- **C (Codex)**: `obligations/` (`ObligationsPlaceholder`), `audit/` (`LegalAuditPlaceholder`), `dashboard/` (`LegalDashboardPlaceholder`) — APIs in EVIDENCE_A Step 6/7; then the accessibility/responsive pass and Step 10 docs.

## Limitations / notes

- No matter list endpoint exists, so the matter picker is a UUID field on upload; documents API supports `matter_id` filtering. Add a matters endpoint (A) if needed.
- Correction decisions are loaded by correction ID (no correction list endpoint yet).
- Pages were verified by unit tests, lint and build only; no browser/E2E run against a live backend in this session.
- CSS: uses existing tokens/classes; a few new class names (`legal-picker`, `span-list`, `citation-link`, `projection-text`, `diff`, `citations`) have no dedicated styles yet and fall back to base element styles.

## Requests to A

(none yet)

## Final build branding/media checkpoint - 2026-10-10
Generated supplied middle-third navy mark and right-third app icon, PNG/ICO favicons (32/180/192/512) and eight 256px WebP workflow icons. Human-review artwork explicitly labels a human gate. Six 8-second H.264 auth clips (desktop/mobile), posters and 12,136,088-byte guide video generated with the prompt ffmpeg settings; desktop crop offsets changed to 0:0 after visual inspection showed centered crops retained corner watermark fragments. In-app legal guide and v2 draft reuse exact repository Markdown; legacy resources/active v1.0 consent preserved. Auth uses approved footage only when motion/data allow, starts on poster, has pause control and dark overlay. Development notice/sign-in aside/metadata now state synthetic demo data and no legal advice. Frontend: 63/63 PASS, lint 0 errors/2 inherited warnings, build PASS. No new dependency. Initial public assets 35,676,958 bytes; after replacement/new guide/icons 37,697,299 bytes (new content adds ~2MB overall; guide source 48,077,129 -> 12,136,088). LegalHelpPage remains a lazy ~26.67KB JS chunk. Next: remaining pages/dashboard and size pass.
