# Legal requirement traceability — Phase B baseline

Date: 2026-10-06. Source: unchanged master PDF detailed catalogue pp.17-19. **No legal FR is fully accepted yet.** Initial D implementation provides partial evidence for FR-002..004/054; remaining paths and phase gates stay planned. Industrial benchmarks do not establish legal correctness. Backend ownership is assigned in `TEAM_WORK_ALLOCATION.md`; frontend acceptance remains with the owner.

Read `LEGAL_DOMAIN_BUILD_CONTRACTS.md` for approved development scope, role/state/source invariants and release boundaries. Priorities below reproduce the catalogue. Build labels: **Core** = initial development slice; **Extended** = later bounded development increment; **Pilot gate** = required before operational pilot; **Later** = post-core Should extension. These labels sequence work; they do not downgrade catalogue Must requirements or authorize calling an incomplete feature complete.

Initial D evidence: `app/db/models/legal_scope.py`, `app/services/legal_policy.py`, `app/api/routes/legal_scope.py`, migrations 0019/0020 and four `test_legal_scope*` targets: 27/27 scoped tests; fresh/0018-to-head parity/idempotency/source/audit/trigger preservation pass. Demonstration is bounded synthetic metadata/session/denial tests, not full document/search/review/recovery journeys. Provisioning, tenant dedupe, legacy-path isolation and legal hold/retention policy acceptance remain unfinished.

D provisioning evidence (2026-10-06, partial): `app/services/legal_provisioning.py`, `scripts/legal_provisioning_cli.py`, migration 0021, `tests/test_legal_scope_provisioning.py` 7 SQLite + 7 PostgreSQL. Strengthens FR-002/003 (tenant/role isolation, independent provisioning) and FR-054 (audited access changes). Migration 0022 + `tests/test_legal_scope_isolation.py` (9 SQLite + 9 PostgreSQL): per-workspace dedupe, legacy-path guards, root audit exclusion. Not FR acceptance.

Part 2 deterministic core evidence (2026-10-06, partial, not acceptance): `app/services/regulatory_versions.py`, `app/services/compliance_assessment.py`, `tests/test_legal_regulatory_core.py` 14/14 with synthetic fixtures; mutation checks confirmed failures are caught. Partial for FR-028/029 (exact part)/032 (freshness)/035/037/038/039/040 and relational part of FR-034. Persistence, tenant FKs, registry/import (FR-026/027), human applicability (FR-030), jurisdiction mapping (FR-031), AI interpretation (FR-036) and APIs remain open.

| Requirement | Priority | Build label / phases | Deliverable and acceptance evidence (planned) |
|---|---|---|---|
| FR-001 | Must | Pilot gate — D/L/M | Enterprise OIDC/SAML/SSO and MFA support; configured IdP/session/authentication tests. Local auth is development-only and does not satisfy this gate. |
| FR-002 | Must | Core — D/E/L | Organization/workspace isolation in API, DB relationships, jobs, retrieval and exports; cross-tenant deny tests. |
| FR-003 | Must | Core — D/J/L | Scoped role permissions; optional ABAC for matter/jurisdiction/unit/sensitivity; full resource-operation authorization matrix. |
| FR-004 | Must | Core / Pilot gate — D/E/L | Document/matter ACLs and legal-hold restrictions; denied source/chunk/export/delete tests. Actual hold/retention policies required for pilot. |
| FR-005 | Must | Pilot gate — D/L/M | Privileged re-auth and session policy; stale auth/revocation/step-up tests before protected administration. |
| FR-006 | Must | Core + Extended — E | PDF/DOCX initially, TXT/images/approved email-export increments; real format import/provenance and malformed input tests. |
| FR-007 | Must | Core — E/L | File type/size/malware/quarantine and parser isolation; malicious/oversize/polyglot/archive-bomb rejection tests. |
| FR-008 | Must | Core — E | Layout-aware parsing/OCR with page/section/region coordinates; scanned/mixed/table fixture quality and locator tests. |
| FR-009 | Must | Core — E/F | Classification/metadata and scoped duplicate/version detection; no cross-tenant hash-existence leakage. |
| FR-010 | Must | Core — D/E/J | Immutable source hash and lineage for originals/derived artifacts; tampering/version-replacement tests. |
| FR-011 | Must | Core — E/K | Low-confidence extraction correction review; retain original text/region and audit correction revision. |
| FR-012 | Must | Core — F | Parties/definitions/terms/dates/renewals/notices/governing-law proposals; field precision/recall and exact source review. |
| FR-013 | Must | Core — F/K | Clause segmentation/classification with stored spans; coverage/order/source-jump fixture tests. |
| FR-014 | Must | Core — F/I | Duty/right/prohibition actor/trigger/deadline/conditions proposals; missing actor/date uncertainty and citation checks. |
| FR-015 | Must | Core — F | Approved versioned playbook/template comparison; exact rule/source linkage and independent review. |
| FR-016 | Must | Core — F/L | Missing expected clause/deviation/unusual term/internal conflict findings; qualify incomplete parsing and cite playbook/coverage. |
| FR-017 | Must | Extended — F/I/L | Basic source-linked cross-contract duty/deadline collisions, reviewer decisions and false-positive fixtures; advanced semantic simulation later, not claimed. |
| FR-018 | Must | Core + Extended — F | Exact redline plus qualified semantic change summary; verify old/new versions, additions/removals and preserved material terms. |
| FR-019 | Must | Core — F/I/J | Only reviewed findings promote persistent obligations/reminders; idempotency and rejected/unreviewed proposal denial tests. |
| FR-020 | Must | Core + Extended — F/K | Executive/detailed/clause/risk/obligation/action/change summary profiles; golden factuality/coverage and citation tests for each. |
| FR-021 | Must | Core — F/L | Audience-specific summaries preserve meaning/conditions; compare materially equivalent source coverage across profiles. |
| FR-022 | Must | Core — E/F/L | Every substantive summary statement binds authorized stored spans; forged/missing citation blocks accepted output. |
| FR-023 | Must | Core — F/K/L | Explicit uncertainty/missing-information labels; absent/conflicting source tests and honest UI. |
| FR-024 | Must | Extended — F/L | Scoped cross-document synthesis with per-document/version citations; denied-document and contradictory-source tests. |
| FR-025 | Must | Extended — F/J/K | Approved-summary PDF/DOCX/JSON exports with source/version/review manifest; unauthorized/unapproved export denial and content parity. |
| FR-026 | Must | Core — G | Governed authoritative-source registry and authority tiers; fixture tiers labelled synthetic/unvalidated and source promotion review tests. |
| FR-027 | Must | Core — E/G | Manual approved regulatory text/guidance import with provenance; no connector fabrication. |
| FR-028 | Must | Core — G/L | Regulatory version/effective intervals/publication/amendment refs; historical/as-of and unknown-date tests. |
| FR-029 | Must | Core + Extended — G | Structural/text differences retained with semantic proposals; change recall and old/new source/version correctness. |
| FR-030 | Must | Core — G/J | Independent human applicability/materiality decision; no automatic AI legal authority or unreviewed impact promotion. |
| FR-031 | Must | Extended — G/H | Requirement applicability links to jurisdiction/entities/products/business units; approved scoped mapping/invalidation tests. |
| FR-032 | Must | Core + Extended — G/I | Watchlists/change alerts with manual-source freshness initially; stale/unavailable source != no change; automatic connectors later. |
| FR-033 | Must | Core — D/H | Distinct requirement/obligation/policy/control/evidence/finding entities; constraints and lifecycle tests. |
| FR-034 | Must | Core — H | Requirement-control-evidence links with authorized same-workspace FKs; cross-tenant/missing-component tests. |
| FR-035 | Must | Core — H | Versioned deterministic rules where explicit logic suffices; repeatable rule outcomes without model calls. |
| FR-036 | Must | Core — H/J/L | Grounded provisional AI interpretation with confidence/uncertainty; review and insufficient-source refusal tests. |
| FR-037 | Must | Core — H/K | Six explainable assessment states; per-state fixtures, reasons and transition/invalidation tests. |
| FR-038 | Must | Core — H/I | Evidence freshness/expiry; clock, stale evidence and dependent current-state invalidation tests. |
| FR-039 | Must | Core — G/H/I | Control/evidence/contract/source drift marks current conclusions stale and schedules re-evaluation; historical snapshot remains intact. |
| FR-040 | Must | Extended — H/K/L | Visible rule/component-based scoring with approved weights and missing-evidence treatment; no opaque AI score or invented numbers. |
| FR-041 | Must | Core — D/J | Durable exact-revision review/approval state machine; restart, self-approval, concurrent decision/revoke and evidence-binding tests. |
| FR-042 | Must | Core — I/J | Owners/due dates/dependencies/escalation; scope validation, reassignment, cycles and deterministic overdue tests. |
| FR-043 | Must | Core — H/I/J | Accepted finding creates idempotent remediation task; closure evidence/retest and independent decision. |
| FR-044 | Must | Extended — I/J/K | Scoped comments/mentions/attachments/decisions with audit; confidential recipient checks and immutable decision history. |
| FR-045 | Must | Core — I/M | Durable renewal/notice/certification/recurrence timers; timezone/calendar, duplicate delivery and restart-loss tests. |
| FR-046 | Should | Later — J | Authorized exception/risk acceptance with source/rationale/expiry; no self-approved exception or indefinite acceptance. |
| FR-047 | Should | Later — I/K | Bulk triage/evidence requests; per-object permissions and retry/idempotency tests. |
| FR-048 | Should | Core — E/F/L | Existing hybrid retrieval adapted with server-owned scope/jurisdiction/version filters; recall and denied-context checks. |
| FR-049 | Should | Core — F/L | Assistant only over authorized corpus; no model context from denied documents or external untrusted content. |
| FR-050 | Should | Core — E/F/K | Source citations resolve page/section/clause and exact version; source-viewer authorization and quote correctness. |
| FR-051 | Should | Core — F/L | Refuse/qualify insufficient support; unsupported material claim blocked from release. |
| FR-052 | Should | Core — F/H/K | Separate source facts/observations/interpretations/recommendations in schemas and UI; no interpretation presented as fact. |
| FR-053 | Should | Extended / Pilot gate — F/L | Matter/workspace-scoped conversation memory and approved retention; revoke/delete/hold behavior before pilot, no memory treated as legal truth. |
| FR-054 | Should | Core — J | Existing append-only chain extended to material legal/security events; transaction rollback and tamper tests. |
| FR-055 | Should | Core — F/J | Actor/time/source/model/prompt/rule/profile/review provenance for conclusions; no raw sensitive prompts in default logs. |
| FR-056 | Should | Core + Extended — G/J | As-of source/evidence/decision snapshot and replay; recorded-vs-effective date and version-drift tests. |
| FR-057 | Should | Core + Extended — K | Real scoped legal/compliance/audit dashboard; executive aggregates only when backed by permitted data. |
| FR-058 | Should | Extended — J/K | Scoped point-in-time evidence packs with provenance/integrity/reviewer decisions; deny unauthorized objects. |
| FR-059 | Should | Core + Extended — J/K | JSON findings/reports/basic audit export; schema/version/content parity and access checks. |
| FR-060 | Should | Later — J/M | High-assurance tamper-evident archive/anchors with independent key/retention policy; no tamper-proof claims. |
| FR-061 | Should | Later — G/M | Governed DMS/drive/ticket/email/GRC/IAM/regulatory adapters; source approval, secrets isolation, retry/dead-letter/reconciliation tests. |
| FR-062 | Should | Later — D/L | Scoped service accounts/API credentials; expiration/revocation/object permissions and no admin identity reuse. |
| FR-063 | Should | Extended — I/J/L | Signed scoped events/webhooks; timestamp/nonce/replay/rate-limit/idempotency tests and summary-only external payloads. |
| FR-064 | Should | Core + Extended — F/G/H | Versioned playbooks/taxonomies/risk/jurisdiction config with approval owners; no guessed legal pack or weights. |
| FR-065 | Should | Core / Pilot gate — F/L/M | Reuse private model gateway; approved profiles/data residency, no hosted confidential fallback; model change/evaluation gate. |
| FR-066 | Should | Core / Pilot gate — L/M | Backup/restore administration and approved retention/deletion/legal hold; separate resources, restore rehearsal and no automatic deletion until policy approved. |

## NFR and innovation acceptance

- **Isolation/security/privacy:** authorization before all retrieval/export/model context, malicious upload/parser isolation, least privilege, encrypted storage/transport, redacted telemetry, governed secondary copies. Verified by D/E/L/M; actual encryption/IdP/retention deployment remains unconfigured.
- **Integrity/audit/explainability:** exact source lineage, immutable decisions and old hash compatibility, sufficient citations, visible uncertainty/status reasons, point-in-time replay. Verified by E-J/L.
- **Reliability/recovery:** durable processing/receipts/timers, retry/restart/dead letters, model-outage deterministic workflow, dedicated backup/restore/reindex. Verified by E/I/J/M; no SLO or RPO/RTO attainment assumed.
- **Usability/accessibility/performance:** real data/empty/loading/error states, source beside output, keyboard/responsive evidence review, observable asynchronous tasks; measure PDF availability/p95 targets under the selected environment in K/M.
- **Digital twin:** relational scoped links first; evidence freshness and change blast radius invalidate current projections without deleting historical decisions. Advanced graph/simulation/compiler/analytics are explicitly later; fixture data cannot masquerade as a live compliance state.

## Definition of implementation acceptance

For each requirement, append actual component/file, test command/result, fixture version, demonstration evidence and blockers as its owning phase runs. Change status only after those checks pass. SSO/MFA, legal-pack validation, retention/legal privilege, authoritative source ownership and deployment SLO/RPO/RTO need named approval before operational-pilot claims. The approved development baseline authorizes building/testing, not silently treating those gates as complete.
