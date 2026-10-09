# Legal & Regulatory Assurance Platform — Terms and Conditions of Use

**Version:** legal-2.0 (DRAFT — not in force)
**Draft date:** 9 October 2026
**Status:** Prepared for owner and legal-counsel review. These terms apply only after (1) counsel approval, (2) bracketed placeholders are completed, and (3) the application publishes version `legal-2.0` and every user accepts it through the in-app terms gate. Until then, the existing legacy terms v1.0 remain enforced and unchanged.

> Placeholders to complete before approval: [OPERATOR LEGAL NAME], [REGISTERED ADDRESS], [CONTACT EMAIL], [GOVERNING LAW / JURISDICTION], [COURTS / ARBITRATION SEAT], [DATA PROTECTION CONTACT], [RETENTION PERIODS], [LIABILITY CAP].

---

## 1. Who we are and what these terms cover

1.1 The Legal & Regulatory Assurance Platform ("the Platform") is operated by [OPERATOR LEGAL NAME], [REGISTERED ADDRESS] ("the Operator", "we", "us").

1.2 These terms govern every use of the Platform: the web application, its APIs, exports, notifications, and any locally deployed model or worker that runs as part of it. By accepting them in the terms gate, you ("User") agree to them for as long as you use the Platform.

1.3 Your organization may also have a separate written agreement with the Operator. Where that agreement conflicts with these terms, the organization agreement prevails for that organization's workspaces.

## 2. What the Platform does — and what it does not do

2.1 The Platform helps legal, compliance, business and audit users to:
- import permitted documents, preserve their original bytes, versions and hashes;
- extract text and exact source locations, including OCR where enabled;
- receive **proposals** (clauses, parties, dates, obligations, deviations, summaries, regulatory changes, compliance assessments);
- record **independent human decisions** on those proposals;
- track accepted obligations, deadlines, controls, evidence, findings, tasks and remediation; and
- review an audit history of these activities.

2.2 **The Platform does not provide legal advice.** Nothing produced by the Platform — including AI-generated or rule-generated proposals, summaries, answers, scores or compliance states — is legal advice, a legal opinion, an audit opinion, or a certification of compliance. Users remain responsible for obtaining qualified professional advice.

2.3 **The Platform does not act autonomously on your behalf.** It does not sign, file, submit, send notices to counterparties or regulators, or take destructive remediation actions. Any such action is taken by a human outside the Platform.

2.4 **Proposals are not decisions.** An AI or rule output becomes an accepted record only when an authorized, independent human reviewer approves the exact revision. A reviewer cannot approve their own proposal. Approval of a transcription correction confirms the text only, not its legal meaning.

2.5 **Compliance states are evidence-bound, not guarantees.** The six assessment states (satisfied, partially satisfied, unsatisfied, insufficient evidence, not applicable, needs review) reflect the evidence, rules and decisions recorded at a point in time. A "satisfied" state is not a guarantee that a regulator, court or counterparty will agree.

## 3. Accounts, roles and access

3.1 Accounts are personal. Do not share credentials or sessions. You are responsible for activity under your account until you report a suspected compromise to [CONTACT EMAIL].

3.2 Access is limited to the organization, workspaces, matters and documents you are granted. Being a workspace administrator does not by itself grant access to confidential documents or authority to approve legal conclusions.

3.3 You must not attempt to access, infer or enumerate documents, records or users you are not authorized to see, including through search, exports, the assistant, error messages or timing.

3.4 We may suspend or revoke access to protect the Platform, other users or data, or where required by law. Revocation takes effect for queued and in-progress work as well as new requests.

## 4. Your content and permitted use

4.1 "Customer Content" means the documents, evidence, notes, comments, decisions and other material you or your organization upload or create. Between you and the Operator, your organization retains its rights in Customer Content.

4.2 You confirm that you have the right to upload each document and that uploading it does not breach confidentiality, privilege, copyright, data-protection law or any contract. Do not upload material you are not permitted to process.

4.3 You must not upload malware, deliberately malformed files, or content intended to manipulate the Platform's AI (for example hidden instructions). Files may be scanned and quarantined. A quarantined file is not processed until it passes the required checks.

4.4 Originals are preserved immutably. A replacement creates a new version; earlier versions, decisions and audit records are kept as history, subject to section 8.

## 5. AI and model use

5.1 AI features run on private or locally hosted models configured by the Operator or your organization. Confidential Customer Content is not sent to a hosted third-party AI service unless your organization explicitly approves that provider in writing and it is configured for your workspace.

5.2 Customer Content is **not used to train or fine-tune** models unless your organization gives separate written consent.

5.3 AI outputs can be incomplete or wrong. Every material statement is linked to a cited source location so that a human can verify it. Where support is weak or conflicting, the Platform labels the output as uncertain, needing review, or declines to answer. You must check the cited source before relying on any output.

5.4 Prompts and model traces are not logged by default. Where logging is enabled for troubleshooting, it is limited, access-controlled and retained per section 8.

## 6. Deadlines, notifications and reminders

6.1 Deadlines extracted from documents remain **proposed** until a human confirms the date, timezone, calendar rules and trigger. The Platform does not guess business-day conventions.

6.2 In-app notifications are the authoritative record of reminders. Email or other external delivery is provided only where configured, and a delivery failure does not remove the in-app record.

6.3 Reminders support, but do not replace, your own diligence. The Operator is not responsible for missed deadlines that were never confirmed, assigned or acted on in the Platform.

## 7. Security

7.1 The Operator maintains reasonable technical and organizational measures, including server-side sessions, role- and object-level access control, malware scanning, immutable source hashes, and an append-only, hash-linked audit trail.

7.2 The audit trail is tamper-evident, not tamper-proof. Report any suspected security incident immediately to [CONTACT EMAIL].

7.3 You must not probe, scan, load-test or attempt to bypass security controls without the Operator's written authorization.

## 8. Retention, legal hold and deletion

8.1 Customer Content, versions, decisions and audit records are retained for [RETENTION PERIODS] or as configured by your organization's approved retention policy.

8.2 Material under legal hold is not deleted while the hold is active, even if a deletion is requested.

8.3 Conversation history with the assistant is scoped to the workspace or matter, can be revoked or deleted by authorized users, and is never treated as legal truth.

8.4 Backups follow the same retention rules within the backup cycle.

## 9. Privacy and personal data

9.1 Personal data is processed only to provide the Platform, under your organization's instructions and applicable data-protection law. Contact: [DATA PROTECTION CONTACT].

9.2 Users and organizations are responsible for having a lawful basis to upload personal data contained in documents.

9.3 Data-subject requests are handled through your organization and the Operator according to the approved privacy workflow.

## 10. Availability and changes

10.1 Service targets, if any, are set in your organization's agreement. Without one, the Platform is provided on a reasonable-efforts basis. During model, scanner, search or storage outages, the Platform shows a degraded or queued state instead of fabricating results. Stored, accepted records stay available where possible.

10.2 We may change features. Material changes to these terms create a new terms version that you must accept before you continue using the Platform. Earlier acceptances remain on record.

## 11. Acceptable use

You must not use the Platform to: break any law; infringe others' rights; process data you are not authorized to process; misrepresent Platform outputs as legal advice or certified compliance; reverse-engineer it except as law permits; overload it; or extract other tenants' data.

## 12. Intellectual property

The Platform software, design and documentation belong to the Operator and its licensors. Your organization keeps its rights in Customer Content. Outputs generated from Customer Content may be used by your organization for its internal purposes, subject to this agreement.

## 13. Disclaimers and limitation of liability

13.1 To the extent permitted by law, the Platform is provided "as is". The Operator does not warrant that outputs are complete, accurate or fit for a particular legal purpose.

13.2 To the extent permitted by law, the Operator is not liable for indirect or consequential loss, or for decisions made or deadlines missed in reliance on unreviewed outputs. Total liability is limited to [LIABILITY CAP], except where the law does not allow such a limit.

## 14. Termination

You may stop using the Platform at any time. On termination, access ends. Customer Content is returned or deleted according to section 8 and your organization's agreement, except where a legal hold or legal obligation requires retention.

## 15. Governing law and disputes

These terms are governed by [GOVERNING LAW / JURISDICTION]. Disputes are resolved by [COURTS / ARBITRATION SEAT].

## 16. Contact

[OPERATOR LEGAL NAME] — [CONTACT EMAIL] — [REGISTERED ADDRESS]

---

## Acknowledgements shown in the terms gate (for integration)

Each item is a separate checkbox. The server lists them, and every one must be accepted for version `legal-2.0`.

| id | text |
|---|---|
| `legal2_not_legal_advice` | I understand that Platform outputs are proposals and information, not legal advice, audit opinions or compliance certification. |
| `legal2_human_review` | I will verify cited sources before relying on any output, and I understand that only an independent authorized reviewer can accept a proposal. |
| `legal2_permitted_content` | I will upload only content I am authorized to process, and I will not upload malicious or manipulative content. |
| `legal2_access_scope` | I will not attempt to access or infer documents, records or users outside my granted scope. |
| `legal2_deadlines` | I understand that extracted deadlines must be confirmed by a person, and that reminders do not replace my own diligence. |
| `legal2_data_handling` | I have read how AI processing, retention, legal hold and personal data are handled in these terms. |

## Integration notes (later)

1. Counsel approves the text and completes the placeholders. Generate `frontend/public/resources/legal-platform-terms-legal-2.0.docx` (and optionally a PDF) from this file.
2. Add `frontend/src/features/resources/termsV2.js`, following the `termsV1.js` pattern, and pin the DOCX SHA-256 in `termsModel.test.js`.
3. Backend: set `CURRENT_TERMS_VERSION=legal-2.0` and register the acknowledgement IDs above in the terms service (`docs/terms_acceptance.md`). All users re-accept. v1.0 acceptance records stay unchanged.
4. Update `LEGACY_TERMS_NOTICE` in `frontend/src/product.js` and the Help page.
