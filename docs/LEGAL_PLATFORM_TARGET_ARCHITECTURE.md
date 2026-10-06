# Legal & Regulatory Assurance Platform — target architecture

Status: **development baseline approved in Phase B; domain implementation not delivered**. Product name follows PDF pp. 1, 5 and 69. Primary intent: contract analysis, compliance monitoring and document summarization as one persistent, governed operational lifecycle. Blueprint v1.0 has 66 FRs; distinguish recommendations and jurisdiction-dependent validation from verified delivery.

Detailed execution contracts: [domain/permission/workflow/source contracts](LEGAL_DOMAIN_BUILD_CONTRACTS.md) and [all 66 FR acceptance mappings](LEGAL_REQUIREMENT_TRACEABILITY.md). Existing reusable IDs/schema/hash patterns were inspected when defining these contracts; no applied migration or stored immutable row is rewritten by planning.

## Source understanding

- Users (pp. 11,21): pilot Legal Counsel/Contract Reviewer, Compliance Officer, Business Owner, Auditor; administrators operate the tenant; risk/security/executive roles expand later.
- Workflows (pp. 22-24,72): intake, contract review, regulatory version/change applicability, compliance assessment, evidence refresh, remediation, audit snapshot and authorized Q&A.
- Contract output: entities/parties/terms/governing law, clause types, duties/rights/prohibitions, triggers/dates/renewals/notices, governed playbook deviations/missing clauses/conflicts, version redlines, cited summaries and reviewable obligations.
- Regulatory output: approved source registry/authority tiers, jurisdiction/applicability, publication/effective periods/amendment lineage, exact/structural/semantic diffs and human materiality/applicability decisions. Feed failure means stale/unavailable, not no change.
- Compliance output: separate requirements, policies, controls, evidence, assessments, findings and actions; freshness/drift and six visible states. Never an opaque AI-only score.
- Evidence (pp. 27-29,37,41,74): source hash/version/page/section/clause/quote span, authority/effective period and model/prompt/rule/decision lineage. Search/vector projections are not legal truth.
- AI is assistive extraction/retrieval/comparison/synthesis; deterministic software owns identity, permissions, state, timers, rules, audit hashing and accepted-state transitions (pp. 25,37-39).
- Pilot acceptance (pp. 52,59): real auth/isolation, PDF/DOCX ingestion/quality, reviewed clauses/obligations, grounded summaries/Q&A, manual requirements, requirement-control-evidence/freshness, durable findings/tasks/timers/in-app alerts, audit/basic export and tested recovery.
- Security/operations (pp. 34-58,75-77): scoped retrieval, SSO/MFA policy, encryption/secrets/legal hold, malicious-file isolation, redacted telemetry, quotas, retries/dead letters, model outage degraded mode, tested backups and explicit SLO/RPO/RTO. 99.5% and ~2s p95 are targets, not achieved measurements.
- Future: automated feeds, validated multi-jurisdiction packs, HA/SCIM, advanced collision/adversarial/what-if/policy compiler/vendor graph. No signing, filings, universal certification, autonomous high-impact remediation or confidential-data training by default.

## Reuse-first topology

```text
Existing React/Vite shell (evidence-first legal workspaces)
 -> FastAPI API (versioned legal contracts + compatible platform routes)
 -> server-owned organization/workspace/matter policy context
 -> bounded domain services
      documents | contracts | regulatory | compliance | obligations | reviews
      evidence | remediation | notifications | audit/reporting
 -> existing LangGraph/model gateway for scoped language tasks only
 -> PostgreSQL authoritative entities/revisions/decisions/jobs/timers
 -> immutable source storage (isolated local pilot; S3-compatible profile planned)
 -> Qdrant/hybrid retrieval + optional PostgreSQL FTS (rebuildable projections)
```

Keep existing directory layout; the PDF's apps/packages layout, Next.js, Temporal-class engine and cloud stack are recommendations, not instructions to restructure mature code. Adopt needed capabilities incrementally. No graph storage required: relational links implement the digital twin. No hosted inference enablement implied: retain the stricter private/local boundary until a separately approved data/provider policy exists.

## Proposed relational core

Preserve existing UUIDs/timestamps, Document/DocumentVersion and immutable ActionRevision/decision/manifests. Add new tables only through new migrations after 0018, with explicit tenant backfill and integrity strategy.

| Context | Entities and invariants |
|---|---|
| Identity/scope | Organization (tenant), Workspace, WorkspaceMembership/Role permissions, Matter and DocumentAccess; content ownership explicit; admin provisioning does not imply privileged document read |
| Source | Document + DocumentVersion; immutable original hash/object reference; extraction revision/quality/corrections; SourceSpan/SourceCitation bound to exact version/page/section/offset/box |
| Contract | Contract and ContractVersion reference DocumentVersion; Party/contract-party links; Clause spans; versioned Playbook/rules; AnalysisRun/Summary revisions with source coverage |
| Regulatory | RegulatorySource (authority/trust/fetch/freshness), RegulatoryDocument/RegulatoryVersion (jurisdiction, publication/effective end/start, amendment/supersession), Change and ApplicabilityDecision |
| Requirement | Requirement + immutable interpretation/version refs; jurisdiction/entity/business applicability links; requirement-control and obligation-requirement mappings |
| Compliance | Policy/PolicyVersion, Control, control-policy links, Evidence/EvidenceVersion/control links, ComplianceAssessment snapshots, Finding/FindingRevision |
| Work | Obligation (duty/right/prohibition, source, actor/owner/trigger/conditions), Deadline/occurrences/timezone/recurrence, RemediationTask/dependencies/closure evidence/retest, Notification/Alert receipts |
| Review | HumanReview/decision refs linked to FindingRevision/analysis; reuse authoritative revision ledger; mandatory rationale, policy and independent reviewer; explicit escalation/request-changes events |
| Audit | Existing AuditEvent/hash formats retained; append-only legal object/tenant/workflow/source/decision linkage for new events; audit snapshot/evidence export scope and manifest |

Use tenant/workspace-qualified foreign keys/unique constraints on relationship tables so cross-tenant mappings cannot be created accidentally. Tenant-scoped source dedupe must not leak another tenant's document existence. Migration backfill must not guess private ownership from filenames. Require explicit mapping/quarantine for legacy records.

## Digital twin and time

```text
Approved RegulatoryVersion -> RequirementVersion -> Control -> PolicyVersion
                                               -> EvidenceVersion -> Assessment
ContractVersion -> Clause -> approved Obligation -> Deadline -> owner/task
Assessment -> FindingRevision -> HumanReview -> Remediation -> closure/retest
Source/evidence/control/version changes -> impacted mappings -> stale/review -> re-evaluation
```

Each accepted mapping records its source/reviewer/version/effective period. Do not let AI-suggested semantic links silently become authoritative. Retain both effective/legal time and recorded/decision time for historical replay. Changes invalidate dependent *current* projections while retaining past approved snapshots. Live dashboards show assessed components and uncertainty, not invented compliance percentages.

## State/authority contracts

- Intake: received/quarantined/processing/needs-verification/indexed/failed; preserving original precedes parsing. Human corrections create derived revisions, not changes to PDF bytes.
- Proposed extraction/obligation/finding -> validation -> pending review -> approve/reject/request changes/escalate. Request changes creates a new immutable revision; earlier ledger remains intact.
- Compliance: satisfied, partially satisfied, unsatisfied, insufficient evidence, not applicable, needs review. Freshness/source-version drift adds reason and blocks stale green presentation. Not-applicable requires authorized applicability evidence.
- Remediation: assigned/in-progress/submitted-for-review/closed/reopened; completion is not closure without accepted evidence/retest where required.
- Timers: approved dates only; deterministic timezone/calendar/recurrence/notice-window policy; ambiguous dates need correction; idempotent occurrence and escalation receipt; restarts cannot silently lose obligations.
- AI schemas require source references and uncertainty; schema validity/confidence cannot substitute for citation sufficiency, source trust or human authority.

## Retrieval and AI boundary

Policy resolves actor/workspace/matter/document ACLs first. Apply server-derived tenant/document eligibility filters to dense, sparse, rerank input, source viewer, summaries, memory, exports and audit queries. Narrow further by jurisdiction, authority, document type, version, applicable/effective date, contract/regulation/policy/control and sensitivity. Never retrieve globally then merely hide disallowed results in UI.

Proposed specialist routes: legal router, contract intelligence, regulatory intelligence, compliance mapping, document/evidence intelligence, legal/compliance synthesis; use only where language understanding is needed. Approved manual imports, date normalization, rules, access checks, approvals and audit are deterministic. Keep scoped tools and constrained outputs; document text is untrusted data. Missing/conflicting evidence yields refusal/qualified output/needs-review; no fabricated regulatory facts.

## Security and deployment gates

Before ingesting sensitive legal data: workspace/document policy tests, scan/quarantine/type/size/zip-bomb controls, parser isolation, confidential-source storage/encryption, redacted logs/checkpoints, separate public regulatory acquisition, least-privilege runtime DB roles and protected secrets. Preserve CSRF/origin/HttpOnly and immutable history. Approval does not sign contracts, submit filings or authorize legal conclusions outside policy.

First runtime uses independently named local Compose resources and private model endpoint; design S3-compatible storage and cloud/VPC/on-prem profiles without claiming all profiles deployed. Existing checkpoint recovery must be extended and tested for async document work and timers; decide whether it can meet required durability before adding another engine. Define restore exercise, key recovery, quotas, monitoring and SLO acceptance before pilot-ready status.

## Blueprint ambiguities (do not alter the PDF)

1. FR-001 calls SSO/MFA Must, while p.14 places SSO/SCIM after pilot and p.52 MVP says real auth. Resolved for development by explicit user approval: local session auth first; enterprise SSO/MFA and privileged re-auth remain required operational-pilot gates, not completed FRs.
2. FR-017 collision detection is Must, while p.64 calls it advanced. Basic source-linked duty/deadline conflict workflow remains in F/I; advanced semantic collision/simulation later. Neither is claimed delivered by planning.
3. p.67's summary traceability ranges are shifted relative to the detailed catalogue. Use pp.17-19 IDs: contracts FR-012..019, summaries FR-020..025, regulation FR-026..032, compliance FR-033..040. Preserve PDF unchanged.
4. Jurisdiction, industry, authoritative sources/playbooks, privilege/retention/legal hold, IdP, model restrictions, scoring thresholds and actual SLO/RPO/RTO are not approved by the blueprint alone.

Explicit user-approved development handling for item 4: public/synthetic fixtures and manual approved imports, no jurisdiction-compliance claims, local/private AI and no automatic deletion/signing/filing. Deployment-specific packs/IdP/retention/recovery policies stay unconfigured approval gates. This keeps development moving without fabricating legal facts or lowering pilot acceptance.

## Implemented foundation — Phase A

Source configuration now uses an isolated legal Compose project, DB and index namespace; ports 55432 (DB), 16333/16334 (Qdrant), 18000 (backend), 15173 (frontend) and dedicated local model candidate 21434. Container model access requires explicit private endpoint/host values. CI is manual-only and exact-repository gated; foreign-target Compose backups fail closed. These replace hazardous inherited defaults, not existing storage resources. Runtime and legal feature capabilities remain proposed; private config/instance ownership must be accepted before provisioning. See the current runtime guide and validation evidence.
