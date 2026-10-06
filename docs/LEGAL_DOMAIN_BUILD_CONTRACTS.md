# Legal platform build contracts — Phase B

Date: 2026-10-06. Status: **approved development baseline; implementation contracts, not delivered features**. Read with the living migration plan, requirement traceability, target architecture and unchanged master PDF. These contracts guide C-M; no runtime or legal accuracy is accepted here.

## 1. Approved scope and release boundary

The user explicitly approved retaining React/Vite, FastAPI/PostgreSQL/Qdrant/LangGraph and local/private AI. Build real persistence, authorization, review, evidence and timers using labelled public/synthetic fixtures. Do not ship a mock dashboard or an ungrounded document chatbot as the finished product.

Initial end-to-end slice:

1. A scoped user imports a PDF/DOCX contract, preserving original hash and version; extraction/OCR uncertainty is visible.
2. Clause/party/obligation proposals and executive/detailed/risk/obligation summaries reference exact source spans.
3. An independent authorized reviewer accepts a finding/obligation; an owner and an approved deadline persist.
4. A compliance reviewer manually imports a governed regulation/requirement, maps a control and attaches versioned evidence.
5. A deterministic assessment explains its state; expiry/replacement/version change invalidates current dependent results and creates review/remediation work.
6. New approved regulatory text yields an exact diff, proposed impact and human applicability decision.
7. Notifications/timers survive retry/restart; an auditor reconstructs source, analysis, decision and evidence history.

Local cookie auth is an approved **development** profile, not a waiver of FR-001. Enterprise SSO/MFA and privileged re-auth remain an operational-pilot gate. Manual approved regulatory imports satisfy the initial ingestion path; a configured watchlist may track manual updates/freshness but cannot claim an automatic authority connector.

FR-017 gets a basic reviewable collision/conflict workflow over exact source-linked duties/dates in F/I; advanced semantic collision/simulation remains later. Basic logic must not silently infer incompatible legal meanings. Report p.67's shifted ranges are resolved by using the detailed pp.17-19 FR catalogue.

No validated jurisdiction/industry pack exists. All fixture sources/playbooks carry public/synthetic/unvalidated labels, provenance and a named fixture author. Public publication does not equal authoritative applicability. No signing, filing, universal compliance certification, destructive automation or silent risk acceptance. Automatic retention/deletion stays disabled until an approved policy exists; legal-hold controls must still prevent protected deletion.

## 2. Data ownership and compatible schema strategy (D)

| Entity family | Minimum contract |
|---|---|
| Organization | Tenant boundary with UUID and active state; never chosen by an untrusted identity header |
| Workspace | Belongs to exactly one organization; owns legal objects/configuration; inactive workspace denies new work |
| WorkspaceMembership | User + workspace + scoped role + active state; unique user/workspace membership; roles validated deterministically |
| Matter | Workspace-bound legal scope; optional document matter membership narrows access |
| Document / DocumentVersion | Reuse existing UUIDs; add reviewed scope linkage; version points to preserved original bytes/hash, classification, quality and extraction lineage |
| Contract / ContractVersion / Party / Clause | Contract identity separate from immutable source/version and analysis; clauses bind exact spans; parties are scoped records, not globally merged by names |
| RegulatorySource / Document / Version | Authority tier, trust/approval state, jurisdiction, publication, effective interval, retrieved/imported time and amendment/supersession refs |
| Requirement / interpretation revision | Source-bound obligation interpretation and applicability; no rule invented without approved evidence/policy |
| Policy / version / Control | Distinct organizational measures with owners, version/effectivity and requirement/control/policy links |
| Evidence / version / links | Proof artifact metadata + immutable content/version/hash, observed/valid-until times, scope, freshness and accepted reviewer |
| Assessment / Finding / FindingRevision | Evaluation inputs/rule/profile version, six-state proposal, rationale, evidence sufficiency, immutable finding revision and review binding |
| Obligation / Deadline occurrence | Duty/right/prohibition with source/actor/trigger/conditions; owner, approved time/recurrence policy, status and idempotent occurrence key |
| Human review / remediation | Exact revision and independent decision; task owner/dependencies/closure evidence/retest; history append-only |
| Notification / audit linkage | Object/workspace context, event/occurrence identity and delivery/read receipt; old audit hash envelopes stay verifiable |

Every legal object has explicit organization/workspace ownership. Relationship rows use tenant-qualified FK/unique constraints so cross-tenant links fail at the DB boundary as well as the service policy. Clients may select an authorized workspace but cannot supply an actor, role, approval status, accepted-state flag or trusted source authority.

Add forward migrations after the verified actual source head, currently `0020_legal_policy_audit` (original Phase B baseline was 0018; initial D added 0019/0020). Fresh/0018 upgrades are verified on disposable PostgreSQL only; private applied database state remains unknown/unaccepted. Preserve old rows/IDs/hashes/triggers and applied migration files. Do not assign legacy ownership from facility names or account role; require operator mapping or keep unassigned legacy rows quarantined from legal APIs/search.

Current `DocumentVersion.source_sha256` is globally unique. Tenant-scoped duplicates require an explicitly reviewed forward constraint transition/backfill; do not reuse another tenant's version or return a global duplicate error that reveals its existence. Deduplicate accepted intake only within the authorized workspace, with source-hash/version/metadata idempotency rules.

Current `ActionRevision`, decision and audit rows are immutable. Add scoped legal target/link records and tenant references in new audit payloads instead of mutating historic envelopes. Existing root audit/review APIs must not become a back door to scoped legal content. Old records without approved scope remain privileged legacy history, not automatically exposed to members.

## 3. Role and access contract (D/J/K)

Account identity/session/terms remain server-owned. Existing requester/reviewer/admin values remain compatible platform roles; scoped legal memberships add permissions without automatically changing those old account roles.

| Scoped role | Source access | Writes / workflow | Review authority |
|---|---|---|---|
| Analyst | Explicitly permitted matter/documents | Intake, propose clauses/findings/mappings/summaries | None; cannot accept own proposal |
| Legal reviewer | Permitted contract matters and source evidence | Review/correct legal analysis and approved playbooks | Contract/finding/obligation decisions within assigned scope |
| Compliance reviewer | Permitted requirements/controls/evidence | Source/applicability, evidence, assessments/remediation | Applicability/evidence/compliance decisions within assigned scope |
| Business owner | Assigned obligation/task and permitted supporting sources | Supply evidence, update own task progress | Cannot approve interpretation or close material remediation alone |
| Auditor | Granted read-only audit scope and authorized sources | Record separate audit observations | No hidden editing or binding review decisions |
| Workspace administrator | Membership/configuration metadata | Provision/configure scoped users/resources | No inherent legal review or privileged document-read authority |
| Viewer | Permitted aggregate data; source access only if explicitly granted | Read-only | None |

Legacy account admin manages accounts; it does not receive all document text by default. A workspace administrator cannot self-grant material review authority. Initial reviewer provisioning requires an independent authorized administrator; bootstrap procedures must be explicit, audited and not a hidden runtime endpoint.

Until J safely adapts the mature approval service, legal review must require **both** its existing server-owned reviewer/admin eligibility and the relevant scoped membership/ACL/assignment. Never bypass the old service guard to make a new role work. Final legal decision authority comes from current policy, independent requester/reviewer binding and exact revision evidence—not a global role alone.

Authorization guarantee: active account/session/terms -> active membership -> workspace/matter/object ACL + classification -> operation permission. Recheck on async execution/resume, viewing sources, retrieval, reranker context, assistant memory, reviews, audit and export. A worker carries the originating actor/scope; membership revocation prevents later release. Service actors need explicitly scoped permissions, not a blanket admin identity.

Default legal content access is deny unless explicitly granted; membership alone does not reveal a restricted matter/document. Authorized intake may create an audited uploader read grant in the same workspace; it must not grant review authority. Aggregate counts omit denied objects. Finding severity uses `low`, `medium`, `high`, `critical` plus explicit unknown/needs-review handling; fixture severity/playbook rules are labelled synthetic, and no real risk-scoring weights are assumed approved.

Unknown or inaccessible IDs return a consistent unavailable/not-found response; lists/counts/search do not reveal denied objects. Access denials are audited without leaking content. Role hiding in navigation is supplementary, never enforcement.

## 4. Workflow and state contract (E-J)

Keep source processing, legal acceptance, assessment state and remediation progress separate. An indexed source is not an approved legal conclusion; completed AI computation is not accepted compliance.

| Workflow | Allowed transitions and owner |
|---|---|
| Intake | received -> quarantined / processing -> needs verification / ready / failed; scan/type/quality policy is deterministic, corrections create derived revisions |
| Proposal | proposed -> pending review; approve/reject/request changes/escalate by assigned independent human; request changes creates a successor revision, escalation does not approve |
| Accepted obligation | approved -> active -> due/overdue -> submitted evidence -> verified completion; source change marks impact pending, it does not silently cancel the duty |
| Assessment | deterministic rules/grounded interpretation produce status proposal; material/high-impact interpretations stay needs review until authorized decision |
| Remediation | open -> assigned -> in progress -> submitted for review -> closed or reopened; required closure evidence/retest and authorized review precede closed |
| Regulatory change | imported version -> diff/impact proposal -> applicability/materiality review -> accepted impact campaign or rejected interpretation; all source versions retained |

Six assessment values:

- `satisfied`: every required component is supported by accepted current sufficient evidence and applicable approved rules.
- `partially_satisfied`: known supported components exist, but specified components are incomplete; reasons list each gap.
- `unsatisfied`: supported facts demonstrate failure of an applicable approved requirement; missing evidence alone is not proof of violation.
- `insufficient_evidence`: required evidence absent, expired, invalid or unavailable; no fabricated green status.
- `not_applicable`: an authorized applicability decision with source/version/effective context exists.
- `needs_review`: ambiguous/conflicting or material interpretation/changed-source impact awaiting an authorized person.

Freshness and review state are explicit dimensions alongside the stored assessment result. Evidence expiry/replacement or an accepted source/control change invalidates the *current* projection, adds reasons and schedules re-evaluation; it does not rewrite history. Pending interpretation cannot be made authoritative by a high AI confidence value.

The model never approves, changes permissions, accepts risk, deletes evidence or chooses the final status. Mandatory state change and audit event share a transaction. Reviewed commands use idempotency keys bound to actor/workspace/operation/request content; same-key different-content retries return conflict. Concurrent decisions/revocations use existing row-lock/hash-binding patterns.

## 5. Source, time and citation contract (E/F/G/L)

Original bytes have SHA-256, immutable version/object reference and storage provenance. Replacing content creates a new version. OCR/manual corrections point to original page/region and retain extractor/version/quality/correction actor; they never modify the original file.

A material citation carries document ID/version ID/source hash/span ID, exact quote, page/section/clause/offset or bounding box, extraction quality, and when regulatory, source authority and effective interval. Validate the quote/locator against authorized stored evidence, not against model-generated source metadata. Native DOCX/TXT structures use version-bound paragraph/section offsets; never invent page numbers absent reliable rendering.

Keep `published_at`, `effective_from/effective_until`, `imported_at`, `observed_at` and `decided_at` distinct. Effective intervals are half-open where defined; unknown dates are null/needs verification, not guessed. Historical queries bind an explicit as-of date and approved applicability; newer imports do not prove they were effective earlier. Source freshness records last successful import/check separately from last substantive change. A failed source check means stale/unavailable, not no change.

Approved playbooks/rules/jurisdiction packs are versioned configuration with owner, source basis, effective period and review. The development synthetic pack has no legal jurisdiction authority. External regulatory acquisition does not get confidential user/model context. Chat memory is separately scoped/retained and cannot establish a legal fact.

Every substantive summary statement cites spans; summary coverage checks preserve material duties, conditions, dates and limitations. Missing-clause results cite the expected playbook rule/version plus inspected source coverage and qualify absence if parsing is incomplete. Semantic similarity is not legal equivalence; exact text stays available. Empty integrity manifests are not sufficient legal evidence.

## 6. AI and API contracts (D/F/J)

Pydantic legal schemas use forbidden extra fields and bounded input/output collections. A task profile pins schema/prompt/model/rule policy references and data classification. Reuse the gateway/checkpoint/evidence validators; extend legal evidence types without changing old hash formats or industrial S1-S7 expectations. Treat document instructions as untrusted data; tool parameters are actor/workspace scoped and allowlisted.

Legal proposal envelope (contract, not an implemented response):

```json
{
  "schema_version": "legal-proposal-v1",
  "analysis_id": "<server-issued UUID>",
  "source_version_ids": ["<authorized stored version UUID>"],
  "observations": [{"text": "<extracted fact>", "source_span_ids": ["<stored span UUID>"]}],
  "interpretations": [{"text": "<proposed interpretation>", "source_span_ids": ["<stored span UUID>"]}],
  "uncertainties": ["<missing or disputed information>"],
  "confidence": 0.0,
  "review_required": true
}
```

Server validates/rebinds every identifier and sets review/acceptance metadata. Model confidence is an uncalibrated signal until evaluated, never permission or probability of legal correctness. Include schema failure, model outage and insufficient-source responses with visible retry/review states.

Introduce bounded `/v1` domain APIs for documents, contracts/analysis, regulatory sources/versions, requirements/controls/evidence/evaluations, findings/decisions, obligations/tasks/notifications, search/assistant and audit snapshots. Preserve existing platform auth and compatible routes; versioned routes must inherit no-store/origin/terms controls, not bypass prefix middleware. UUID path validation is not object authorization. Error envelopes expose stable code/correlation/retryability without source text or secrets.

## 7. Deterministic deadline and recovery contract (I/M)

An accepted deadline stores original source phrase, normalized timezone-aware value, trigger/conditions, recurrence/calendar policy version and confirming human. Date-only/legal notice semantics need explicit timezone/calendar; ambiguous business-day conventions remain needs review. Do not use an LLM as scheduler or infer a missing year/timezone silently.

Deadline occurrence identity is obligation/version + approved trigger/recurrence occurrence + notification/escalation type; durable receipt/outbox records prevent duplicate effects under retries. Re-scan persisted due work after restart; claim work under concurrency control; bounded retries/dead-letter visible to owners. Timer progress remains usable during model outage. No email delivery is claimed without a configured adapter; in-app notification remains authoritative.

Pilot targets from PDF: 99.5% availability and approximately 2s p95 metadata/search are **targets**, not current measurements. Actual deployment capacity/retention/RPO/RTO require owners and environment. Development acceptance proves deterministic restart/retry, backup/restore/reindex and no silent timer loss using disposable resources; it does not fabricate customer SLO attainment.

## 8. Acceptance and Phase D entry

`LEGAL_REQUIREMENT_TRACEABILITY.md` maps every FR to build phase, deliverable and verification. No legal FR is marked implemented by planning. C may rebrand and adapt truthful capability copy; D may add legal models only after its source dependencies/callers are inspected and isolated migration verification is prepared.

Before legal data handling: active workspace/document authorization, immutable original storage, safe upload/quarantine/parser policy, denied cross-tenant retrieval, private model policy, no prompt/body logging by default and human review enforcement must pass their tests. Before operational pilot: approved jurisdiction/playbooks/retention/identity/legal hold, enterprise identity/MFA/re-auth, actual encryption/least privilege, recovery and deployment acceptance. These remain visible release gates even though development building is approved.
