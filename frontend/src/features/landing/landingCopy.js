// All landing copy (i18n source). Honest by construction: development build, nothing marketed as accepted.
export const COPY = {
  en: {
    nav: [['story', 'Story'], ['reveal', 'Product'], ['workflow', 'How it works'], ['pillars', 'Pillars'], ['sovereignty', 'Runtime']],
    signIn: 'Sign in',
    openWorkbench: 'Open workbench',
    kicker: 'Legal & Regulatory Assurance · development build',
    headline: ['Every conclusion', 'cites its source.'],
    lede: 'Contracts, regulations and evidence become reviewable proposals bound to the exact line they came from. A different person decides. The record keeps the thread.',
    ctaPrimary: 'Open the workbench',
    ctaSecondary: 'See how it works',
    scrollHint: 'Scroll to pull the thread',
    beats: [
      { id: 'scattered', n: '01', title: 'Evidence arrives scattered.', body: 'Contracts, regulations, policies and proof live in different files, versions and inboxes. Nothing says which line supports which decision.' },
      { id: 'unify', n: '02', title: 'One thread through every claim.', body: 'Each clause, obligation and finding is a proposal that cites stored source spans — exact quote, locator and file hash — never an unsupported answer.' },
      { id: 'voice', n: '03', title: 'Source text before interpretation.', body: 'An independent reviewer approves the exact revision. Only then does an obligation, deadline or remediation become part of the record.' },
    ],
    statement: 'Every conclusion cites its source. Every decision has a different reviewer. Every deadline is confirmed by a person, not guessed.',
    revealKicker: 'The review queue',
    revealTitle: 'Decisions bound to an exact revision.',
    revealNote: 'Illustrative layout with synthetic example data — not live records.',
    flowTitle: 'How it works',
    flow: [
      ['Intake', 'Bytes are inspected, scanned and hashed; risky files stay quarantined.'],
      ['Extract', 'Durable jobs produce immutable text spans with page, paragraph or line locators.'],
      ['Propose', 'Deterministic analysis proposes clauses, obligations, findings and assessments with citations.'],
      ['Review', 'A different, currently authorized reviewer approves, rejects, requests changes or escalates.'],
      ['Record', 'Accepted work becomes owned obligations, tasks, remediation and an integrity-checked audit trail.'],
    ],
    pillarsTitle: 'Three pillars, one evidence model',
    pillars: [
      { id: 'pid', title: 'Contract intelligence', body: 'Clauses, parties, deviations, obligation proposals and exact redlines — each citing stored text.' },
      { id: 'compliance', title: 'Compliance assurance', body: 'Requirements mapped to controls and evidence, with six explainable states and visible staleness.' },
      { id: 'maintenance', title: 'Obligations & evidence freshness', body: 'Human-confirmed deadlines, exactly-once reminders and escalations, remediation with retest.' },
    ],
    proofTitle: 'Measured, not claimed',
    proof: [
      { value: 376, label: 'backend legal-core tests passing' },
      { value: 6, label: 'end-to-end journeys tested' },
      { value: 66, label: 'functional requirements tracked' },
      { value: 0, label: 'live AI model calls in tests' },
    ],
    proofNote: 'Measured on the development branch on 9 October 2026 with synthetic fixtures on disposable PostgreSQL. Development evidence is not production acceptance; enterprise identity, penetration testing and pilot approvals remain open.',
    sovereigntyTitle: 'Private runtime policy',
    sovereigntyBody: 'Analysis profiles are deterministic and run without a hosted model. A private-model path exists only behind a setting and is tested with a fake gateway. The deployment is private by configuration — it is not automatically air-gapped, and its audit chain is tamper-evident, not tamper-proof.',
    ecosystemTitle: 'Integration boundaries',
    ecosystem: [
      ['Built and tested in development', 'Scoped workspaces, durable jobs, cited analysis, independent review, obligations, audit exports.'],
      ['Open gates', 'Enterprise SSO/MFA, connectors and webhooks, archive, live model evaluation, real-infrastructure recovery.'],
    ],
    closingTitle: 'Bind the record.',
    closingBody: 'Open the development workbench with a provisioned account. Legal workflows are development features, not accepted production capability.',
    footer: 'Synthetic data only in this development build.',
  },
}

export const copy = (lang = 'en') => COPY[lang] || COPY.en
