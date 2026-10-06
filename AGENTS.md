# Repository boundary

- This application's only authorized GitHub repository is `https://github.com/loktrishal-05/legal-compliance-regulatory-workbench.git`.
- Before any commit, push, pull request, or remote change, verify that the target repository is the authorized repository above. Stop if it differs.
- Never modify, commit, push, or open pull requests in `https://github.com/loktrishal-05/ertmac-nwis.git`. It is a separate application and must not be used for this workspace.
- The only application root is `C:\Users\Lohith k\Desktop\OLD hard work\legal-compliance-regulatory-workbench`. Historical `sovereign-agentic-workbench` repositories and sibling worktrees are forbidden modification targets.
- Verify the root, origin, worktree/common metadata, hooks and deployment targets before operational commands. If a target points outside this application or at an unrelated repository, stop that operation; correct only authorized configuration in this workspace.
- Do not execute, update, commit or push nested `claudex-loop` repositories or historical `.kilo/worktrees` as application code. Their unrelated/stale metadata requires an approved custody plan, not automatic remote replacement or deletion.
- Preserve staged, unstaged and untracked user work. Do not continue/abort the inherited cherry-pick, prune/repair historical worktrees, reset history, or overwrite user changes without explicit direction.
- The master specification is `docs/Legal_Regulatory_Assurance_Platform_Master_Report.pdf`; keep it byte-for-byte unchanged. Migration audit/planning documents describe proposals, not delivered capabilities.
- Main flow (owner, 2026-10-06): one-time history-preserving join via PR #5, then accepted development work is promoted to `main` through regular reviewed dev→main PRs. Still no force push, rewrite, self-approval or protection bypass.
- Major domain transformation requires approval of the discovery report. No push until the full migration and validation report has been shown to the user and a push is explicitly authorized. No force push, history deletion, or `git reset --hard`.
- The user authorized regular local checkpoint commits on 2026-10-06. Commit coherent, verified phase changes with their documentation; inspect root/origin/status/diff/log before each commit, stage only intended paths, and preserve unrelated user work. Push permission is still separate. An inherited-work preservation commit is a snapshot, not a claim of new test acceptance.

## Mandatory phased build workflow

- Team handoff authorization (2026-10-06): the user approved publishing the reviewed partial checkpoint to `feat/legal-regulatory-platform-migration`, including the already-tested identity snapshot, and enabling PR review protection on that branch and `main`. No new frontend implementation is authorized. Follow `docs/TEAM_WORK_ALLOCATION.md`; all backend requirements remain assigned. Remote `main` has unrelated history; reconciliation/promotion must be reviewed separately, never force-push/overwrite it. AI review is session-bound; baseline CI alone is not feature acceptance.

- When resuming a paused session, read `docs/SESSION_RESUME.md` first if present, then verify its recorded state against Git and the living guide. A pause checkpoint is not phase completion; do not resume implementation until the user asks.
- `docs/CLAUDE_HANDOFF.md` is the consolidated assistant/team continuation context linked from SESSION_RESUME. Follow its reading index and reverify state; historical notes in `docs/SESSION_RESUME_HISTORY_2026-10-06.md` are not current execution instructions. Keep the handoff synchronized with the living guide/progress/validation and actual PR state.

- `docs/LEGAL_DOMAIN_MIGRATION_PLAN.md` is the living step-by-step build guide. Read it before starting or resuming any migration phase, together with `docs/MIGRATION_PROGRESS.md`, `docs/VALIDATION_REPORT.md`, and the relevant master-report requirements.
- Follow the guide's phase dependencies, entry blockers, scope and exit checks. Inspect existing implementation and callers before editing; reuse mature components before replacing them.
- Keep the guide synchronized as part of the same work whenever implementation, requirements, architecture, dependencies, scope or validation changes. Record the reason, affected phases/requirement IDs and approval needs; update related architecture/reuse documents when affected. Do not change the master PDF.
- At each phase start, mark its status and next step in the guide/progress log. Before ending a phase or session, record actual files changed, tests/results, blockers and the next action. Update `docs/VALIDATION_REPORT.md` with verification evidence; do not mark complete until exit checks pass.
- A plan update does not authorize destructive changes, unrelated repository operations, unresolved cherry-pick handling, deployment, live model execution or a push. Keep those existing boundaries in force.
