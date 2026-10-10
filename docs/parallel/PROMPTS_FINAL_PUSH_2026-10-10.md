# Final push prompts — 2026-10-10 00:40 (v2: Netlify + Hugging Face Space + Neon, ONNX help chatbot)

Verified state at 00:21:
- Backend for all three pillars is committed: 0026-0031, compliance API included, legal-core suite and journeys green at the last checkpoint.
- Landing page rebuilt (6015627).
- **The legal frontend is only partly built.** Done: documents, source viewer, contracts, review queue. Still placeholders: **dashboard, compliance, regulatory, summaries, assistant, obligations/tasks, audit** (`frontend/src/features/legal/shared/Placeholders.jsx`).

## Split (Claude credit is limited)

| Agent | Work |
|---|---|
| **Claude** (small, now) | Part 1: demo seed + demo-login button + dashboard aggregate API. Part 2 when the owner says "final": verify, push to GitHub, PRs |
| **OpenCode** (now) | Deployment (Netlify + HF Docker Space + Neon), ONNX help chatbot + voice, then deploy after the owner logs in |
| **Codex** (from ~00:40) | Branding/media, the remaining pages, interactive dashboard charts, size optimization |

## Deployment target (binding)

Vercel/Netlify functions can't host this backend: ~250 MB limit, no worker, no disk, 4.5 MB bodies, and Netlify has no Python functions. Chosen topology:

- **Frontend → Netlify** (CLI already installed): Vite static build. `netlify.toml` proxies `/v1/*`, `/auth/*`, `/health*` and `/internal/*` to the backend with `status = 200` rewrites. The browser sees ONE origin, so the HttpOnly session cookies and CSRF/origin checks keep working.
- **Backend → Hugging Face Docker Space** (free CPU: 2 vCPU / 16 GB RAM, long-running container, port 7860; sleeps after inactivity). One container runs FastAPI (legal-only slim app) + an in-process worker/scheduler loop + the ONNX model.
  - The Space must be PUBLIC so Netlify can proxy without auth headers, which means its files are public. Ship only code; put secrets ONLY in Space secrets. Synthetic demo data only, never real confidential documents.
  - Fallback if HF fails: **Railway** (`railway` CLI, Docker, small paid usage), with the same image.
- **Database → Neon Postgres**: pooled `DATABASE_URL` with `sslmode=require`. Migrations + demo seed run from the owner's PC against Neon.
- **Originals:** the container disk is ephemeral, so add an opt-in Postgres original store (bytea, content-addressed, create-only, hash re-verified on read).
- **Malware scan:** optionally install clamav-daemon in the image (16 GB RAM allows it; freshclam at startup). If it's not done or not healthy, uploads stay QUARANTINED (fail closed). Never bypass.
- **Model:** a small Qwen instruct model (~0.6-0.8B; verify the exact model id, Apache-2.0 license and an existing ONNX int4 export on Hugging Face, e.g. onnx-community, and never guess an id) via `onnxruntime-genai` (or optimum+onnxruntime if genai fails). Downloaded at image build time. Used ONLY for the in-app help chatbot, which answers questions about using the application, grounded on the user guide/terms docs. It never sees tenant documents. The legal document assistant stays deterministic and cited.

---

## 1. Claude Code — paste NOW (keep it small)
```
Owner update (00:40). Claude credit is limited: be economical, no broad re-reading, targeted tests only. Read docs/parallel/PROMPTS_FINAL_PUSH_2026-10-10.md (the "Deployment target" section is binding). OpenCode and Codex are working in the same tree. Commit only your paths, with "[A]" and explicit paths. No push yet.

Part 1 — do now:
1) Demo seed: backend/scripts/legal_demo_seed.py. It is idempotent and refuses to run unless LEGAL_DEMO_MODE=true. It uses the existing provisioning service (audited) to create one demo organization + workspace + matter and four demo users with roles: demo-admin (workspace admin + reviewer), demo-counsel (reviewer), demo-owner (business owner) and demo-auditor (read-only). Passwords come from env vars (DEMO_*_PASSWORD) with no hardcoded secret. Then load synthetic fixtures through the real services: 2 contracts from backend/tests/fixtures/legal_contracts with analysis + one approved obligation (approved by a different demo user), the regulatory fixture with an applicability decision, compliance requirement/control/evidence with assessments in several of the six states (one evidence item expired -> stale), tasks, a notification, and audit events. Provenance: "synthetic fixture, operator-seeded, not malware-scanned". One test: seed twice = idempotent; refuses without the flag.
2) Dashboard aggregates: GET /v1/workspaces/{id}/dashboard returns permission-filtered counts. Include: documents by job state; reviews pending by target type; assessments by six-state + stale; obligations due per week (next 8 weeks) + overdue; tasks by status; findings by status; evidence expiring 30/60/90 days; regulatory sources by freshness. Only objects the caller may read (no count leakage); test with two tenants and an auditor. Publish the JSON shape in docs/parallel/EVIDENCE_A.md.
3) Demo login button on the sign-in page, only when import.meta.env.VITE_DEMO_MODE === 'true': "Use demo account" + a role select (admin/counsel/owner/auditor). It FILLS the identifier/password fields from VITE_DEMO_* env values and does not auto-submit. Add the visible note "Demo data only — synthetic". Add an env-gating test. Off by default.
4) Targeted tests + the full legal-core suite once, commit, and a short note in EVIDENCE_A. Then STOP and wait for the owner to say "final".

Part 2 — only when the owner says "final":
- Run the full legal-core suite, the migration validator (fresh + 0018->head), and cd frontend; npm test; npm run lint; npm run build (report the bundle sizes).
- Verify the root, origin = https://github.com/loktrishal-05/legal-compliance-regulatory-workbench.git and the branch. Confirm nothing private is staged: .env, models/, data/, claudex-loop/, docs/.phase11_*, .impeccable/, .playwright-mcp/, benchmark/reports changes, *.log.
- Commit the intended docs (docs/parallel/*.md, docs/product-resources/), and fold the evidence into the living docs/SESSION_RESUME.
- Show the owner the final report. Then (the push is owner-authorized): `git push origin integration/backend-continuation-20261007` (no force), update PR #13, and open the development and main PRs per AGENTS.md through normal CI/review. Never force or bypass protection.
```

## 2. OpenCode — paste NOW
```
Resume as Agent B. Read AGENTS.md, docs/parallel/PROMPTS_FINAL_PUSH_2026-10-10.md (the "Deployment target" section is binding), EVIDENCE_A/B/C/C8.md and `git log --oneline -25`. Claude and Codex work in the same tree. Commit "[B]" with explicit paths only. Never push to GitHub (Claude does that). Deploy to Netlify/Hugging Face only in Task 4, after the owner confirms the logins. Docker Desktop must be running for the backend tests.

Task 1 — Slim deployable backend (test first):
- backend/app/main_deploy.py: the same middleware/session/terms/CSRF behavior, and ONLY the auth/health/terms + legal_* routers. No import of torch/sentence-transformers/qdrant/paddle/langgraph; prove it with a test that imports the app with those modules blocked.
- backend/requirements-deploy.txt (pinned, minimal + onnxruntime-genai or onnxruntime).
- An opt-in Postgres original store (LEGAL_ORIGINAL_STORE=postgres) via a NEW migration 0032_legal_original_blobs (append after 0031): content-addressed, create-only, hash re-verified on every read. The default filesystem store is unchanged. Tests for both.
- An in-process worker: when LEGAL_EMBEDDED_WORKER=true, a startup background loop calls the existing legal worker run_once() every N seconds (claims, leases and retries unchanged). Plus a protected POST /internal/legal/run-once (constant-time CRON_SECRET compare, 403 otherwise).
- Uploads without a healthy scanner stay quarantined. Optional: clamav-daemon in the image with freshclam at startup, configured through the existing legal_malware settings. If it isn't healthy, it stays fail-closed.

Task 2 — ONNX help chatbot (application help only):
- Find on Hugging Face the smallest official Qwen instruct model (~0.6-0.8B) with an existing ONNX int4 export and an Apache-2.0 license. Record the exact repo id + revision + license in EVIDENCE_B. Never invent an id.
- Add an "onnx" runtime behind the existing model gateway (local, allow-listed, temperature 0, bounded tokens, timeout) using onnxruntime-genai.
- New endpoint POST /v1/help/chat: retrieves from a small in-repo help corpus (docs/product-resources/LEGAL_PLATFORM_USER_GUIDE.md + the terms draft, chunked at startup, keyword/BM25 in Python), answers ONLY questions about using the application, cites the guide sections, refuses off-topic or legal-advice questions, and never touches tenant data. Session-protected and rate-limited per user.
- If the model is unavailable, return the best-matching guide sections (degraded, honest).
- Tests use a fake runtime: off-topic refusal, prompt-injection in the question, no tenant data access, outage fallback. Add one optional real-model smoke test that skips unless the model files exist.

Task 3 — Chatbot + voice UI (frontend/src/features/legal/assistant/ + a floating launcher in the app shell):
- Two tabs: "Help" (the /v1/help/chat ONNX bot) and "Ask my documents" (the existing deterministic cited /assistant/questions + /conversations, with citations opening the source viewer, fact/observation/interpretation/recommendation labels, refusal/degraded states, history with delete).
- Voice: speech OUTPUT via window.speechSynthesis (local). Speech INPUT via the Web Speech API only after an opt-in toggle stating "Voice input may be processed by your browser vendor's speech service; do not dictate confidential content". Off by default, hidden if unsupported.
- Esc closes, focus trap, aria-live answers. No new npm dependencies. Tests for the pure helpers. Then cd frontend; npm test; npm run lint; npm run build.

Task 4 — Packaging and deployment:
- deploy/hf-space/: Dockerfile (python:3.11-slim, non-root user, port 7860, model downloaded at build with a pinned revision, uvicorn app.main_deploy:app) + README.md with the Space front-matter (sdk: docker, app_port: 7860).
- Root netlify.toml: build `cd frontend && npm ci && npm run build`, publish frontend/dist, rewrites with status 200 for /v1/*, /auth/*, /health* and /internal/* to the Space URL (placeholder BACKEND_URL until it is known), plus the SPA fallback /* -> /index.html.
- docs/DEPLOY_NETLIFY_HF_NEON.md: every env var (DATABASE_URL, session/secret keys, CRON_SECRET, CURRENT_TERMS_VERSION, LEGAL_DEMO_MODE, DEMO_*_PASSWORD, LEGAL_ORIGINAL_STORE, LEGAL_EMBEDDED_WORKER, model settings, the cookie Secure/SameSite settings behind the proxy, allowed origins; frontend VITE_DEMO_MODE, VITE_DEMO_*), the exact CLI steps, what is disabled, and the security notes (public Space = synthetic data only).
- Then STOP and ask the owner to run: `netlify login`, `huggingface-cli login` (pip install -U huggingface_hub), and to create the Neon project and give you DATABASE_URL through an env var (never paste it into files or commits).
- After confirmation:
  (a) alembic upgrade head against Neon, then the demo seed
  (b) create a PUBLIC Docker Space, upload deploy/hf-space + the backend code (never .env/data/models/tests' private files), set Space secrets with `huggingface_hub` HfApi.add_space_secret, and wait until /health is green
  (c) put the Space URL into netlify.toml, then `netlify deploy --build` (preview) and, after the owner checks it, `netlify deploy --build --prod`
  (d) smoke-test: sign-in with the demo account, dashboard, contract page, help chatbot, upload -> quarantined (if no scanner)
- Record the URLs and results in EVIDENCE_B.
```

## 3. Codex — paste at ~00:40 (or give it to OpenCode after its tasks)
```
Resume as Agent C. Read AGENTS.md, PRODUCT.md, DESIGN.md, docs/parallel/PROMPTS_FINAL_PUSH_2026-10-10.md, EVIDENCE_A/B/C/C8.md, frontend/src/features/legal/shared/* and `git log --oneline -25`. Claude and OpenCode work in the same tree. Commit "[C]" with explicit paths only. No push. No new npm dependencies. OpenCode builds the assistant/chatbot; don't touch frontend/src/features/legal/assistant/.

Task 1 — Branding and media (ffmpeg is installed; <Downloads> = C:\Users\Lohith k\Downloads):
a) Logo: from "<Downloads>/Triptych Security Document Logo Variations.png" use the MIDDLE third (logo on navy) and the RIGHT third (app icon). The left third has defects.
   ffmpeg -i "<Downloads>/Triptych Security Document Logo Variations.png" -vf "crop=iw/3:ih:iw/3:0" frontend/public/assets/branding/legal-logo-mark.png
   ffmpeg -i "<same>" -vf "crop=iw/3:ih:2*iw/3:0" frontend/public/assets/branding/legal-app-icon.png
   From the app icon make favicon-32.png, icon-192.png, icon-512.png, apple-touch-icon.png (180) and favicon.ico. Update the manifest and BRAND_MARK in frontend/src/product.js; the wordmark text stays in the existing font.
b) Agent icons from "<Downloads>/Glossy Compliance AI Icon Set.png": a 4x2 grid (crop=iw/4:ih/2:col*iw/4:row*ih/2), 256 px WebP, saved to frontend/public/assets/branding/agents/. Row 1: contract-analyst, summary-writer, regulatory-watch, compliance-assessor. Row 2: obligation-keeper, evidence-audit, research-assistant, human-review-gate. Use them in the legal nav/page headers with alt text. human-review-gate marks HUMAN decisions, never AI.
c) Auth background videos (same slot names, so check authModel.js; the 0.9 crop removes the Gemini watermark):
   login  auth-bg-01: ffmpeg -y -ss 8 -t 8 -i "<Downloads>/gemini_generated_video_fed08d06.mp4" -an -vf "crop=iw*0.9:ih*0.9,scale=1280:720,fade=t=in:st=0:d=0.6,fade=t=out:st=7.4:d=0.6" -c:v libx264 -crf 27 -preset slow -pix_fmt yuv420p -movflags +faststart frontend/public/assets/auth/auth-bg-01.mp4
   signup auth-bg-03: the same with -ss 24
   recovery auth-bg-02: the same filters on "<Downloads>/Generated Video October 09, 2026 - 8_47PM (1).mp4" with -ss 0
   mobile: replace the crop/scale with "crop=ih*0.9*9/16:ih*0.9,scale=720:1280" -> auth-bg-0N-mobile.mp4
   posters: ffmpeg -y -ss 1 -i auth-bg-0N.mp4 -frames:v 1 -c:v libwebp -quality 80 auth-bg-0N-poster.webp
   Check a frame of each clip. Keep the form readable (dark gradient overlay if contrast < 4.5:1); prefers-reduced-motion shows the poster only. Polish the sign-in/sign-up layout to match the landing, without changing the auth logic.
d) Guide video: ffmpeg -i "<Downloads>/Legal_Assurance_Platform.mp4" -vf scale=1280:720 -c:v libx264 -crf 30 -preset slow -c:a aac -b:a 96k -movflags +faststart frontend/public/resources/legal-guidance-video.mp4 (< 30 MB) + a poster. Put it on the Help page as the current legal guide (the legacy video stays labelled legacy). Add the docs/product-resources/LEGAL_PLATFORM_USER_GUIDE.md content as an in-app guide page, and the Terms v2 draft as "draft — pending counsel approval" (do NOT switch the enforced terms version).

Task 2 — Remaining legal pages under frontend/src/features/legal/<area>/, replacing the placeholder routes: compliance, regulatory, summaries, obligations (tasks/notifications/exceptions) and audit (timeline/snapshot/evidence pack/export). Use the shared API client/WorkspaceContext/state components/CitationLink. Spec: the Step 8 section of docs/parallel/PROMPT_C_CODEX_REGULATORY_COMPLIANCE_FRONTEND.md. Real APIs only, with honest states.

Task 3 — Interactive dashboard (frontend/src/features/legal/dashboard/) on Claude's GET /dashboard:
- hand-written SVG charts, no library: a six-state donut, an 8-week obligations-due bar chart with an overdue marker, reviews by type, evidence expiry 30/60/90, documents by job state
- tooltips on hover AND focus, click-through to the filtered page, a data-table toggle per chart, DESIGN.md palette with states distinguished by label/pattern too
- an empty state when there is no data, never fake numbers

Task 4 — Size: npm run build and list the chunks; keep legal pages lazy-loaded; media only in public/; remove unused frontend code/assets only after grepping for references; record before/after sizes in EVIDENCE_C8.md.

After each task: cd frontend; npm test; npm run lint; npm run build; commit.
```

## Order
1. Now: Claude #1 Part 1 and OpenCode #2. At ~00:40: Codex #3.
2. When OpenCode asks: run `netlify login`, `pip install -U huggingface_hub` then `huggingface-cli login`, and create a Neon project. Give OpenCode the DATABASE_URL as an environment variable in its terminal (`$env:DATABASE_URL="..."`), never in chat or files.
3. When everything is done: tell Claude **"final"**, and it pushes to GitHub and opens the PRs.
