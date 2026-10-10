# Legal & Regulatory Assurance Platform — User Guide

**Version:** 1.0 draft, 9 October 2026 — matches the development MVP being built on `integration/backend-continuation-20261007`. Sections marked *(MVP)* describe features that are implemented and tested in development but not yet accepted for production pilot use.

---

## 1. What the Platform is for

The Platform turns documents into **reviewed, source-linked decisions and actions**. It connects three jobs that are usually done in separate tools:

| Pillar | You get |
|---|---|
| Contract analysis | Clauses, parties, dates, renewals, notice periods, duties/rights/prohibitions, playbook deviations, missing clauses, conflicts, version redlines |
| Document summarization | Executive, detailed, clause, risk, obligation, action and change summaries — every statement linked to the exact source text |
| Compliance monitoring | Regulation → requirement → control → evidence → assessment → finding → remediation, kept current as evidence expires or rules change |

**Golden rule:** the Platform *proposes*; a person *decides*. Nothing becomes an accepted obligation, assessment or finding until an independent, authorized reviewer approves it.

## 2. Roles

| Role | Can do | Cannot do |
|---|---|---|
| Legal counsel / contract reviewer | Review clauses and findings, approve interpretations, compare versions | Approve their own proposals |
| Compliance officer | Govern regulatory sources, decide applicability, map controls, accept evidence, approve assessments and remediation closure | Approve their own proposals |
| Business owner | Own obligations and tasks, upload evidence, submit completion | Approve legal interpretation or close remediation alone |
| Auditor | Read granted sources, history, snapshots and evidence packs | Change decisions |
| Workspace administrator | Manage members and configuration | See confidential documents without a grant; give themselves review authority |

You only see the organization, workspaces, matters and documents you were granted. If something is not yours to see, the Platform says "unavailable", without revealing whether it exists.

## 3. Getting started

1. **Sign in** with your account. On first sign-in, read and accept the current **Terms and Conditions**. Every acknowledgement is required.
2. **Choose a workspace and matter** from the picker at the top of the Legal area.
3. The **Legal dashboard** shows real counts for your scope: documents, open reviews, upcoming deadlines, stale assessments, overdue tasks. An empty dashboard means there is no data yet, not that you are "compliant".

## 4. Documents and sources

### 4.1 Upload *(MVP)*
- **Legal → Documents → Upload.** Accepted formats: PDF, DOCX and TXT. Size and content limits apply.
- Every file is checked: format, size, archives, macros, active content and malware scan. A file that fails, or that can't be scanned, goes to **Quarantine** with a reason. Quarantined files are not processed.
- The original is stored unchanged with a SHA-256 fingerprint. Uploading the same file again reuses it; a changed file becomes a **new version**.

### 4.2 Processing jobs *(MVP)*
- Extraction runs as a background **job**: queued → running → succeeded, failed, or dead-lettered after retries. The job page shows progress and a safe failure reason.
- Scanned pages can use English OCR, where it is enabled. OCR text is marked with its method and quality, and needs verification.

### 4.3 Source viewer and corrections *(MVP)*
- Open a version to see its **source spans**: exact text with page/region (PDF) or part/paragraph (DOCX) locations. Every citation elsewhere in the Platform jumps here.
- Found an OCR mistake? Select the span → **Propose correction**. A different authorized reviewer approves or rejects it. Corrected text is shown alongside the original and is never silently replaced. Blank regions that OCR missed can also be transcribed against a page region.

## 5. Contract analysis *(MVP)*

1. **Legal → Contracts → New contract**, then link an extracted document version.
2. **Run analysis.** The default profile is deterministic (rules over the stored text). It proposes clauses, parties, definitions, dates, renewals, notice periods, governing law, and obligations (who must do what, when, and on what condition).
3. **Playbook comparison.** Choose an approved playbook to see deviations, unusual terms and missing clauses. A "missing clause" always shows which rule expected it and how much of the document was actually read. If parsing was incomplete, the Platform says absence is *not established*.
4. **Redline.** Compare two versions to see the exact text differences plus a summary of what materially changed.
5. **Submit for review.** Findings and obligation proposals go to the **Review queue**. Approved obligation proposals become tracked **Obligations** (section 8).

## 6. Summaries and the assistant *(MVP)*

- **Summaries:** choose a profile (executive, detailed, clause, risk, obligation, action, change) and an audience. Every sentence carries citations; click a citation to open the source. The summary also lists coverage, uncertainties and missing information. Only **approved** summaries can be exported, to PDF, DOCX or JSON, with a manifest of sources and reviews.
- **Assistant:** ask questions about documents you are allowed to see. Answers cite exact spans and label each statement as *fact*, *observation*, *interpretation* or *recommendation*. When support is weak or conflicting, the assistant qualifies the answer or declines. Conversation history is kept only within your workspace or matter and can be deleted; it is never treated as a source of legal truth.

## 7. Regulatory intelligence and compliance *(MVP)*

### 7.1 Regulatory sources and versions
- **Legal → Regulatory → Sources:** register an authoritative source (authority tier, jurisdiction, owner). A reviewer approves it before imports are allowed.
- **Import** a regulation version manually. Record its published and effective dates; unknown dates stay *unknown* and are flagged for verification.
- **Changes:** compare versions to see structural and text changes. A reviewer decides applicability and materiality for your jurisdictions, entities, products and business units.
- **Watchlists** show freshness honestly. A source without an automated feed shows "not monitored", never "no change".
- An approved change starts an **impact campaign** listing the affected requirements, controls, evidence and obligations, and creates review tasks.

### 7.2 Compliance map and assessments
- **Legal → Compliance:** requirements link to policies, controls and evidence. Evidence has validity dates and must be **accepted** by a reviewer.
- An **assessment** gives one of six states, each with reasons and citations:
  - **Satisfied** — every required component is supported by accepted, current evidence.
  - **Partially satisfied** — some components are supported; the gaps are listed.
  - **Unsatisfied** — the evidence shows an applicable rule is not met.
  - **Insufficient evidence** — proof is missing, expired or invalid. This is not the same as a violation.
  - **Not applicable** — an authorized decision says the requirement doesn't apply, in that exact context.
  - **Needs review** — there is ambiguity, a conflict or a change waiting for a decision.
- When evidence expires or a regulation or control changes, the current assessment is marked **stale**, with the reason, and re-evaluation is scheduled. Past assessments are never rewritten.

## 8. Obligations, tasks and notifications *(MVP)*

- **Obligations** come only from approved proposals. Each one shows the source clause, the owner, the trigger, the original deadline wording, and the confirmed date and timezone. If the date wording is ambiguous, the obligation stays *needs confirmation* until a person confirms it.
- **Deadlines and reminders** are durable: they survive restarts and are never sent twice.
- **Tasks** have an owner, a due date, dependencies (circular dependencies are blocked) and evidence requests. Overdue tasks are highlighted. Tasks can be reassigned only to people who have access.
- **Remediation** is created from accepted findings. Closing it requires evidence plus an independent review; a failed retest reopens it.
- **Exceptions / risk acceptance** always carry a rationale, an approver and an expiry date.
- **Notifications** (the bell icon) are the authoritative reminder record, even if email isn't configured.

## 9. Reviews

- **Legal → Reviews** lists items waiting for your decision: approve, reject, request changes, or escalate.
- You cannot review your own proposal. Escalation does not count as approval.
- Each decision is bound to the exact version you saw. If the item changes afterwards, it needs a new review.

## 10. Audit, snapshots and evidence packs *(MVP)*

- **Legal → Audit:** a filtered timeline of who did what, when, and on which source/version.
- **Snapshot (as of a date):** see what was recorded and in effect at that time.
- **Evidence pack:** a frozen, integrity-hashed bundle of sources, versions, evidence and decisions for a chosen scope. Items you can't access are excluded automatically.

## 11. When something is unavailable

| You see | Meaning | What to do |
|---|---|---|
| Quarantined | The file failed a safety check or couldn't be scanned | Check the reason; contact an administrator |
| Job failed / dead letter | Processing failed after retries | Retry, or report the safe error code |
| Degraded / AI unavailable | The model service is down | Accepted records, rules and timers still work; try AI features later |
| Needs verification / needs review | Unknown date, low OCR quality, conflict or change | Verify the source, or send it for review |
| Unavailable | You don't have access, or the item doesn't exist | Ask the owner for a grant |

## 12. Good practice

- Always open the cited source before relying on a summary or answer.
- Confirm deadline timezones and trigger events carefully.
- Keep evidence current, so that you see an expiry warning before an auditor does.
- Use comments for discussion. Use decisions for anything material.

## 13. Current limitations (development MVP)

- Enterprise single sign-on/MFA, approved legal rule packs, live private-model quality evaluation, independent security testing, and production backup/recovery are pending pilot approval.
- OCR is English-only and bounded; handwriting and complex tables need manual verification.
- Regulatory monitoring uses manual imports; there are no automatic feeds yet.
- External email/ticket delivery and connectors are not configured; in-app notifications are authoritative.

## 14. Help

In-app: **Trust → Help & Resources**. Support: [CONTACT EMAIL].

---

### Integration notes (later)
Export this guide to `frontend/public/resources/legal-platform-user-guide-v1.0.pdf`. Add it to `ResourcesView.jsx` as the current legal guide, and keep the legacy industrial guide labelled as legacy. Remove the *(MVP)* labels only after the corresponding acceptance evidence exists.
