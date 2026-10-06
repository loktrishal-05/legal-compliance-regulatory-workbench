# Resume entry point — Claude / any incoming assistant

Updated: 2026-10-06. **Read [CLAUDE_HANDOFF.md](CLAUDE_HANDOFF.md) next.** It consolidates the conversation decisions, approvals, exact root/repository/branches, current build and validation, remaining work, three teammate assignments, commit/PR/review rules and the prompt to continue.

## Current facts

- Root: `C:\Users\Lohith k\Desktop\OLD hard work\legal-compliance-regulatory-workbench`.
- Only repository: `https://github.com/loktrishal-05/legal-compliance-regulatory-workbench.git`.
- Shared development branch: `feat/legal-regulatory-platform-migration`, published at `496f903` when verified.
- Local branch: `team/handoff-review-evidence`; PR [#4](https://github.com/loktrishal-05/legal-compliance-regulatory-workbench/pull/4) targets the shared development branch. Its pre-handoff HEAD `9cd84af` has passing push/PR checks and awaits independent approval. Reverify HEAD/checks because this documentation update advances the PR.
- Remote `main`: `d95dfc3`, protected, unchanged; it has unrelated history/no merge base with the migration branch. Reconciliation/promotion is separately reviewed.
- A/B complete at source/design level; C backend identity verified, frontend acceptance owner-managed; D initial scope/API/migrations tested but incomplete; E-J/L-M still assigned/planned; K belongs to the user.
- Three human workstreams: Part 1 D/E/F/search, issue #1; Part 2 G/H, issue #3; Part 3 I/J/L/M/assurance, issue #2. Handles: Part 1 Harsha-code-per, Part 2 Sanjjith27, Part 3 Cholan-kinnera (invitations pending acceptance).
- No new frontend/landing implementation. No requirements or tests waived by the user's half-hour target.

## Reading order and next action

1. Read root `AGENTS.md` and `CLAUDE_HANDOFF.md`.
2. Read the living plan, progress, validation, team allocation, domain contracts and FR registry linked there.
3. Verify Git/remote/PR state and preserve unrelated benchmark/nested/private/local work.
4. Set assignees after invitation acceptance; review PR #4 without self-approval/bypass; inspect new teammate PRs and coordinate remaining D gates before legal intake.
5. Continue backend implementation only on an explicitly assigned scope/branch; do not duplicate teammates' work or infer permission for private services/models/deployment/main reconciliation.

Historical pause/resume notes are preserved in [SESSION_RESUME_HISTORY_2026-10-06.md](SESSION_RESUME_HISTORY_2026-10-06.md). Historical progress/validation sections record what was true then; current handoff and verified Git state resolve stale status, while AGENTS/master requirements remain binding.
