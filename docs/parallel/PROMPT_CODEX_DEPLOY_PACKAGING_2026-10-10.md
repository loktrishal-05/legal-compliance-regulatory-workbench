# Codex handoff — deployment packaging and runbook only

Paste the prompt below into a **separate Codex session**. The existing Agent C session retains its frontend/media work. OpenCode/Agent B retains slim backend, original store, ONNX help, assistant/voice UI, Dockerfile/model-download code, and actual deployment after owner confirmation.

```text
You are Codex — deployment packaging/runbook helper for the Legal & Regulatory Assurance Platform.
Work only in C:\Users\Lohith k\Desktop\OLD hard work\legal-compliance-regulatory-workbench.
Claude (A), OpenCode (B), and the existing Codex frontend agent (C) use the SAME directory and branch concurrently.

Read fully first:
- AGENTS.md
- docs/parallel/PROMPTS_FINAL_PUSH_2026-10-10.md (Deployment target section is binding)
- docs/parallel/EVIDENCE_A.md, EVIDENCE_B.md, EVIDENCE_C.md, EVIDENCE_C8.md
- docs/parallel/PROMPT_CODEX_DEPLOY_PACKAGING_2026-10-10.md
Then inspect git log --oneline -25, status, staged diff, root/origin/common Git directory/hooks.
Only authorized origin: https://github.com/loktrishal-05/legal-compliance-regulatory-workbench.git.
Current intended branch: integration/backend-continuation-20261007. Do not change it.

BOUNDARIES:
- Local work and coherent verified commits authorized. Prefix commits [D]. Explicit owned paths only.
- Never push to GitHub, open PRs, merge, reset, rebase, stash, cherry-pick, switch branches, or modify remotes/config/hooks.
- Never operate nested claudex-loop repositories, historical/sibling worktrees, private models/data, or the immutable master PDF.
- Never stage somebody else's work. If unrelated paths are staged, leave them alone. Commit only your explicit owned paths; do not use git add . or git add -A or commit -a.
- No login, account/Space creation, secret-setting, Neon migration/seed, Netlify/HF/Railway deployment, or live model execution. These belong to B AFTER owner confirms logins/environment.
- Do not print/read/paste real secrets into files, commits, logs or evidence. Documentation uses placeholders and environment-variable names only.
- Docker Desktop must be running. Use your own isolated project lrw-d when testing. Do not stop A/B/C containers or rebuild A's shared core image.

CURRENT IMPLEMENTATION TO INSPECT, NOT MODIFY:
- backend/app/main_deploy.py: slim auth/health/legal app + opt-in embedded worker + secret-protected /internal/legal/run-once.
- backend/requirements-deploy.txt: minimal pinned deployment dependencies.
- backend/app/core/config.py: LEGAL_ORIGINAL_STORE, LEGAL_EMBEDDED_WORKER, worker interval, demo-only Neon/TLS, cookie flags, CRON_SECRET, help model/doc/path settings.
- backend/app/services/legal_originals.py; db/models/legal_original_blob.py; migration 0032_legal_original_blobs.
- backend/app/services/legal_help.py and model_gateway/onnx_runtime.py / onnx_worker.py.
- deploy/hf-space/Dockerfile, Dockerfile.dockerignore, README.md, download_help_model.py, test.compose.yml.
- backend/scripts/legal_demo_seed.py (A's seed requires SIX DEMO_*_PASSWORD values: admin, counsel, compliance, analyst, owner, auditor).
- frontend/src/services/api.js and features/auth/demoLogin.js (or its actual current equivalent) for exact VITE_* names.

OWNED PATHS — CREATE/EDIT ONLY:
1. netlify.toml
2. docs/DEPLOY_NETLIFY_HF_NEON.md
3. deploy/hf-space/publish_space.py
4. backend/tests/test_legal_scope_deploy_packaging.py
5. docs/parallel/EVIDENCE_DEPLOY_PACKAGING.md

Never touch B's Dockerfile/model downloader/test overlay, backend/settings/migrations/services, assistant UI, shared frontend files, A's seed/dashboard/login, or C's pages/media. Requests go in your evidence file under Requests to B/A/C.

TASK 1 — netlify.toml:
- Build exactly: cd frontend && npm ci && npm run build; publish frontend/dist.
- Frontend API_BASE_URL defaults to /api. Preserve it: status-200 proxy /api/* -> https://BACKEND_URL/:splat.
- Also status-200 rewrites /v1/* -> https://BACKEND_URL/v1/:splat, /auth/* -> .../auth/:splat, /health -> .../health, /health/* -> .../health/:splat, /internal/* -> .../internal/:splat.
- API rewrites BEFORE SPA fallback /* -> /index.html (status 200).
- Keep BACKEND_URL placeholder until B has a confirmed Space URL. Do not invent a URL or deploy/link a Netlify site.
- Test TOML parsing and rewrite order/path behavior. Do not change frontend API base to a cross-origin Space URL: cookie/origin protections depend on the single browser origin.

TASK 2 — detailed deployment runbook:
- Describe chosen topology: Netlify static frontend -> public Docker HF Space -> Neon pooled TLS PostgreSQL; only synthetic demo data, code public, credentials only env/Space secrets.
- Document every REQUIRED/relevant env var with actual aliases/defaults from code: DATABASE_URL (postgresql+psycopg or normalized standard Neon URL, sslmode=require), WORKBENCH_DEPLOYMENT_MODE=public, LEGAL_DEMO_MODE=true, LEGAL_ORIGINAL_STORE=postgres, LEGAL_EMBEDDED_WORKER=true, LEGAL_WORKER_INTERVAL_SECONDS, CRON_SECRET >=32 bytes, WORKBENCH_AUTH_SECRET >=32 bytes, CURRENT_TERMS_VERSION=1.0, SESSION_COOKIE_NAME/SECURE/SAMESITE/TTL, WORKBENCH_CORS_ORIGINS explicit JSON list, signup disabled, model settings/path allowlist, LEGAL_HELP_MODEL_ENABLED, LEGAL_HELP_DOCS_ROOT, prompt/query logging off, scanner/OCR behavior.
- Include all six DEMO_<ROLE>_PASSWORD vars, seed semantics, and exact frontend VITE_DEMO_MODE / VITE_DEMO_* names. Demo values baked into frontend are deliberately public synthetic credentials; database/cron/auth/operator secrets MUST NEVER have a VITE_ prefix.
- Active legacy terms remain enforced. legal-2.0 is a draft, not in force; no counsel/pilot/compliance claims.
- Exact CLI setup: netlify login; pip install -U huggingface_hub; current hf auth login (explain legacy huggingface-cli login name if unavailable). STOP gate: owner must confirm login and Neon env before B executes remote actions.
- Explain safe env entry and no secret output. Give Linux-Docker alternatives to Windows native migration if DLL policy blocks it; do not recommend disabling OS protection.
- After explicit confirmation, operator/B runs alembic upgrade head against Neon, then idempotent demo seed, then public Space creation/upload/secrets, /health AND /health/ready checks, Netlify preview, owner preview review, then prod. Do not execute these steps yourself.
- Include proxy Secure + SameSite=Lax cookie explanation (one browser origin); exact trusted Netlify production/preview origins, no wildcard credential origins.
- Include health, demo sign-in, /app/legal/dashboard, contracts, help, upload -> quarantined, original survival after restart, cron denied without correct secret, and evidence checklist. Public Space sleeps: workers pause while asleep, persisted claims/timers catch up on resume; do not promise continuous uptime or completed recovery/SLO acceptance.
- Clearly list disabled/open features: no hosted legal inference; document assistant deterministic; no healthy scanner -> quarantine; private/confidential uploads forbidden; no automatic migrations/deletion/signing/filing; no industrial routes in slim app; no enterprise IdP/real legal packs/pen-test/pilot acceptance.

TASK 3 — publication helper (prepare and TEST, never execute remotely):
- Default is DRY RUN with NO authentication/network/migration/seed side effects.
- Verify exact app root/origin before selecting files. Build an explicit code-only upload manifest: tracked .py files under backend/app and backend/alembic; backend/alembic.ini, backend/requirements-deploy.txt; scripts/__init__.py, legal_worker.py, legal_demo_seed.py; exactly the authored synthetic msa.txt/nda.txt seed inputs; exactly public user guide/terms draft; B's Dockerfile -> Space-root Dockerfile, B's README -> Space-root README.md, download_help_model.py and Dockerfile.dockerignore -> Space-root .dockerignore.
- Reject symlinks, out-of-root paths, .env, data/, models/, benchmark/, claudex-loop/, .git/, private docs/.phase11_*, browser/review/log files and arbitrary test files. Never upload the whole working tree or recursively upload tests.
- An execute flag may exist for B's later use, but Codex must never pass it. Require dedicated application Space slug legal-compliance-regulatory-workbench and authenticated HF namespace; avoid silently reusing/overwriting unrelated Spaces.
- Real execution (only later by B): HfApi.create_repo(repo_type='space', space_sdk='docker', private=False); HfApi.add_space_secret with ALLOW-LISTED env keys whose values come only from the process environment; explicit CommitOperationAdd/create_commit for approved manifest only. Never print secret values, URL credentials, tokens or raw provider errors. No GitHub push operations.
- Existing Space reuse must be explicit, not automatic; secret/config/file failures must be surfaced honestly without copying private fallback content.
- Use installed huggingface_hub + standard library; no dependencies or shell installers. Lazy-import SDK so dry-run/tests work without auth or SDK installed.
- Write tests first (RED), then GREEN with fake HfApi. Prove dry-run makes zero remote calls and upload excludes private/symlink/untracked files; rewrites correct; no private env vars go to frontend; execute remains gated.

TEST/COMMIT:
- Prefer B's slim dependency image via:
  docker compose -p lrw-d -f infra/docker-compose.legal-core-test.yml -f deploy/hf-space/test.compose.yml run --rm tests python -B -m unittest discover -s tests -p 'test_legal_scope_deploy_packaging.py' -v
- If the image is not available yet, ask B; do not rebuild another agent's image. Native pure tests are okay if no private settings/services are imported.
- Cleanup only lrw-d: docker compose -p lrw-d -f infra/docker-compose.legal-core-test.yml -f deploy/hf-space/test.compose.yml down --volumes.
- Record exact files, RED/GREEN commands/results, runbook caveats and Requests to B in EVIDENCE_DEPLOY_PACKAGING.md.
- Inspect root/origin/status/owned diff/staged diff/log before each commit. git add <your five explicit paths> only; prefix [D]; never include other agents' staged/unstaged/untracked changes.
- End with commit IDs and a short handoff. No deployment URLs may be reported as live unless B subsequently verifies them.
```
