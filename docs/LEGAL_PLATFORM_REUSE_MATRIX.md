# Legal platform reuse matrix

Status: reuse-first development baseline approved; legal feature implementation remains planned. **RETIRE means remove from active legal routes only after dependency/replacement proof; no immediate deletion.** BUILD below is split into NEW and narrowly justified REBUILD.

| Subsystem | Decision | Existing assets / target change | Dependency / gate |
|---|---|---|---|
| FastAPI/Pydantic API foundation | KEEP | `main.py`, router, validated schemas; additive legal `/v1` routes | Preserve origin/terms/error/cache controls for new paths |
| PostgreSQL/SQLAlchemy/Alembic | KEEP | UUIDs, timestamps, naming, constraints | New migrations only; actual applied revision unknown |
| Account sessions/password/recovery | ADAPT | Argon2, HttpOnly sessions, rate limits, signup/terms | Enterprise identity/MFA/re-auth and scoped roles remain gaps |
| RBAC / reviewer separation | ADAPT | Shared deps and service-level checks | Add workspace membership/matter ACLs; no admin content bypass by default |
| Organization/workspace/matter isolation | NEW | Relational ownership/membership/ACL model | First gate before legal corpus retrieval; backfill only explicitly owned data |
| Document/version/hash storage | ADAPT | Document, DocumentVersion, ingestion manifests | Tenant-scoped dedupe; immutable original lifecycle; retain mature IDs |
| PDF extraction/chunking | ADAPT | PyMuPDF/Docling/native quality/page/box contracts | Preserve original text and all source spans; legal heading/table tests |
| PaddleOCR/image infrastructure | ADAPT | Local engines/region locators | Generic scanned contract/regulation OCR and correction workflow |
| Secure browser upload / DOCX import | NEW | Existing path validation and parser reuse | Scan/quarantine/size/type/archive limits/parser isolation |
| Qdrant / BGE / sparse / RRF / reranking | ADAPT | Existing dense+sparse pipeline | Server-derived ACL/effectivity/authority filters; controlled reindex |
| Citations / evidence provenance | ADAPT | EvidenceRefs, validators, integrity manifests | Legal source-span types; sufficient evidence gate; historical replay |
| Local model gateway | KEEP | Ollama structured output, bounded repairs, locality | Keep private/local default; approved model/data profile only |
| Legal AI task profiles/evaluation | NEW | Reuse gateway and output contracts | Benchmark citations/coverage/extraction; confidence is not legal accuracy |
| LangGraph/checkpoint/observability | ADAPT | SQL saver, durable execution/receipts | Tenant context, legal specialists, actual worker/timer behavior |
| Immutable proposal/decision/release | ADAPT | ActionRevision/ApprovalDecision and release checks | Link FindingRevision; add request-changes/escalation without mutating prior decisions |
| Audit chain/canonicalization | KEEP | Deterministic append/verify/DB triggers | Add event vocabulary via migration; preserve old envelopes/hash versions |
| Legal audit context/snapshots/exports | NEW | Reuse events/manifests | Scoped point-in-time bundle; actor/source/model/prompt/rule/decision refs |
| Verified knowledge/gaps/packs | ADAPT | Candidate/verified/stale/revoked workflows | Approved legal/jurisdiction content; no chat memory as legal truth |
| Contract/party/clause/playbook | NEW | DocumentVersion and governed analysis integration | Parties, clause types, missing/deviation/conflict, redlines, summaries |
| Regulation/source/version/requirements | NEW | Source/version patterns and controlled import | Authority/jurisdiction/publication/effectivity; human applicability |
| Compliance requirements/controls/policies | NEW | Relational join patterns | Six explainable states; approved deterministic rule versions |
| Evidence freshness/findings/remediation | NEW | Hash/review primitives | Expiry invalidates dependent state; closure evidence and retesting |
| Obligations/deadlines/notifications | NEW | Persistent owner/date/source references | Deterministic recurrence/timezone/timers/idempotency/escalation |
| Living compliance digital twin | NEW | Relational typed mappings/version refs | Change blast radius and stale propagation; graph DB unjustified initially |
| Durable scheduling/job dispatch | NEW | Extend receipt/checkpoint capabilities | Prove restart/retry/no duplicate side effect; Temporal only if needed/approved |
| Generic document review pane | ADAPT | Source inspector, citation rendering, image viewer patterns | Legal clause and exact-version display, accessibility |
| Frontend shell/auth/components | KEEP | Lazy routes, session, UI states, responsive tokens | Preserve existing uncommitted improvements |
| Industrial frontend pages | REBUILD (bounded pages) | Contracts/compliance/regulatory/obligations workspaces | Keep shell; each new page backed by real API |
| Dashboard/review/knowledge/execution/audit | ADAPT | Live-data surfaces and review desk | No industrial counts converted to legal metrics |
| Public identity/help/terms/assets | ADAPT | Text/manifest/favicon/package/service title | Product name from PDF; new branding asset decision; version terms safely |
| Maintenance/sensor/equipment/P&ID topology | RETIRE | Industrial models/services/tools/routes/prompts | Extract generic OCR/provenance first; retain old data/history/tests |
| Shift handover/refinery/safety/optimization BI | RETIRE | Operational agents/prompts/pages | Replace preflight/routing/evidence policy together, not strings alone |
| Local voice | ADAPT, later optional | H3 transcript review and local adapters | Legal vocabulary/quality gate; not necessary for first MVP |
| Public resource connectors/n8n | ADAPT | Allowlisted resource and signed webhook concepts | Manual authoritative import first; no fabricated live regulators |
| Docker/offline/local backup | ADAPT | Existing image/lock/volumes/offline/backup | Independent legal resources; backup/restore and encryption verification |
| CI and agent custody configuration | ADAPT | Existing test jobs/hook instructions | Remove operational old runner/tool linkage only through approved plan |
| Frozen industrial benchmark | KEEP as historical | Preserve corpus/hash contract | Separate legal fixture/evaluation pack; resolve existing modified report |
| Platform regression tests | KEEP / ADAPT | Preserve security, provenance, decision semantics | Run on isolated resources; classify mixed tests before edits |
| Incoming bundle/archived siblings/tooling | KEEP archive/reference | No duplicate application copy or worktree merge | Historical pointers left unchanged; nested Git operations blocked |

No blanket backend rebuild, Next.js replacement, graph database, microservice split, Kubernetes or new AI provider is justified for the first slice. Required missing controls are not deferred merely for simplicity.

E2a reuse delta (2026-10-07): reused source/version IDs, `_verify_original` returning the exact verified snapshot, shared current-policy checks, audit writer and native `inspect_pdf` with opt-in retained headings; stdlib subprocess/resource/XML/ZIP handles deterministic native extraction. Added immutable extraction/span records, typed IPC and exact source routes through 0024; bounded test image uses already-locked PyMuPDF 1.28.2. No Docling/model invocation or new queue/framework. Native quality, real scanner/kernel sandbox, OCR/corrections and durable jobs remain explicit E2 gates.

2026-10-07 E1 reuse delta: retained the shared intake service, scoped policy and existing document/version/audit envelopes; stdlib Expat supplies streaming decoded XML validation, ZipFile member/compression guards bound archives, and `os.link` supplies create-only original publication. No new library/storage abstraction or migration. 93 scoped tests pass; actual head 0023. Scanner, parser sandbox/OCR/corrections/source spans and scoped retrieval remain E2/E3 work, not provided by these primitives.

Initial D milestone: reuse Base UUID/timestamps/naming, model registry, session/terms dependencies and audit writer/hash envelopes; add scope tables/policy/metadata APIs through migrations 0019/0020. Disposable PostgreSQL policy/API/migration checks pass. Scoped dedupe, legacy-path compatibility and audited provisioning remain pending. No new frontend work; team ownership/PR/reconciliation rules are in `TEAM_WORK_ALLOCATION.md`.

Phase A execution update: Docker/CI/defaults/runbooks were adapted for source-level isolation; existing password/terms/security/domain behavior remains intact. Backup Compose-target validation was extended and tested. Auxiliary tools/history remain quarantined reference material instead of being deleted or retargeted. Live resource provisioning, legal identity migration and all NEW domain capabilities remain unfinished.

Phase B acceptance contracts retain React/Vite, FastAPI/PostgreSQL/Qdrant, local gateway, session/RBAC and immutable review/audit infrastructure. Scoped legal memberships/ACLs and tenant-qualified relations are additive; account administrator is not automatically a confidential-content reader. Tenant deduplication needs a reviewed forward transition from the inherited global source-hash constraint. Material output still needs actual sufficient source spans, not merely a schema-valid response or empty manifest. See domain contracts and FR traceability for required tests and unconfigured operational-pilot gates.
