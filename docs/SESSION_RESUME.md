# Resume entry point — Claude / any incoming assistant

Updated: 2026-10-06. **Read [CLAUDE_HANDOFF.md](CLAUDE_HANDOFF.md) next.** It consolidates the conversation decisions, approvals, exact root/repository/branches, current build and validation, remaining work, three teammate assignments, commit/PR/review rules and the prompt to continue.

## Current facts

- Root: `C:\Users\Lohith k\Desktop\OLD hard work\legal-compliance-regulatory-workbench`. Only repository: `https://github.com/loktrishal-05/legal-compliance-regulatory-workbench.git`.
- Development branch `feat/legal-regulatory-platform-migration` at `5ff7ed8` (PRs #4, #6, #7, #8 merged); migration head `0022_legal_version_scope`.
- `main` at `a85494d` (history joined by #5). Development -> main promotion PR still to be created by the owner (session permission blocked it).
- Owner: all teammates unavailable; integrator builds all backend work. Approvals set to 0; `legal-core` CI, strict, conversations, admin enforcement, no force/delete remain.
- A/B complete; C backend identity verified (frontend owner-managed); **D complete for development exit checks**; G/H deterministic core merged; E, F, G/H persistence, I, J, L, M remain; K belongs to the owner.
- No new frontend/landing implementation. No requirements or tests waived.

## Reading order and next action

1. Read root `AGENTS.md` and `CLAUDE_HANDOFF.md`.
2. Read the living plan, progress, validation, team allocation, domain contracts and FR registry linked there.
3. Verify Git/remote/PR state and preserve unrelated benchmark/nested/private/local work.
4. Set assignees after invitation acceptance; review PR #4 without self-approval/bypass; inspect new teammate PRs and coordinate remaining D gates before legal intake.
5. Continue backend implementation only on an explicitly assigned scope/branch; do not duplicate teammates' work or infer permission for private services/models/deployment/main reconciliation.

Historical pause/resume notes are preserved in [SESSION_RESUME_HISTORY_2026-10-06.md](SESSION_RESUME_HISTORY_2026-10-06.md). Historical progress/validation sections record what was true then; current handoff and verified Git state resolve stale status, while AGENTS/master requirements remain binding.
