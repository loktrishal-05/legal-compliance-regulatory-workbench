# Evidence — fresh ZIP-style local run with the bundled help model (2026-10-10, agent A)

Goal: a teammate downloads the branch ZIP, runs `Copy-Item .env.example .env` and
`docker compose --env-file .env -f deploy/local/docker-compose.yml up --build`, and everything works, including the
in-app Help chatbot on a local model. Only Docker Desktop is required.

## Root causes found
1. Help answered "No matching guide section": the running `lrw-local` image was built at 01:13, before the guide
   Markdown was copied into the runtime image (7d94767, 01:57). Inside it `/app/docs/product-resources` did not exist → 0 help sections. A fresh build includes them.
2. A truly fresh build failed: `frontend/src/features/resources/LegalHelpPage.jsx` imports `docs/product-resources/*.md?raw`, which the Docker web stage never copied. Fixed in `deploy/local/Dockerfile` (3903818).
3. No help model was packaged (B's downloader/Dockerfile were never committed). Added `deploy/local/fetch_help_model.py` + a `help-model` build stage: `onnx-community/Qwen3-0.6B-ONNX` @ `1e0a4a196ecabdf9a879664110574563d3f372d3`, CPU int4 subdirectory, base `Qwen/Qwen3-0.6B` @ `c1899de2…` LICENSE, `provenance.json` matching the adapter allow-list; runtime `onnxruntime-genai==0.17.1`; compose `LEGAL_HELP_MODEL_ENABLED=true`; `DOWNLOAD_HELP_MODEL=false` build arg keeps the guide-excerpt fallback.

## Verification (clean copy, isolated project `lrw-zip`, port 8001)
`git archive HEAD` (3903818) → temp folder → `.env` from `.env.example` → override file (port 8001 + CORS for 8001, temp only) →
`docker compose -p lrw-zip --env-file .env -f deploy/local/docker-compose.yml -f override.yml up --build -d`: build OK, model stage printed
`help model ready: [LICENSE, chat_template.jinja, config.json, genai_config.json, model.onnx, provenance.json, tokenizer.json, tokenizer_config.json]`.
- `/health` 200; first start log `{'status': 'seeded', ... 'contracts': 2, assessment_states satisfied/insufficient_evidence/unsatisfied ...}`; `Uvicorn running`.
- `POST /api/auth/login` demo-counsel → 200; `GET /api/v1/workspaces` → demo workspace; `GET .../dashboard` → assessments {satisfied 1, unsatisfied 1, insufficient_evidence 1}, stale 3, tasks open 3.
- `POST /api/v1/help/chat` "How do I upload a document?" → `answered`, reason `onnx_selected_verified_guide_sections`, model `Qwen/Qwen3-0.6B`, citations include "4.1 Upload". "How does independent review work?" → `answered`, same model.
- `GET /` and `/app/legal/dashboard` → 200.
- Torn down with `docker compose -p lrw-zip down -v`; temp folder removed. `lrw-local`, `lrw-a/b/c` untouched.

## Limits
- Model section choice is advisory; the server returns exact guide text only (no generated prose). Ranking quality is a small-model selection, not evaluated beyond these smoke checks.
- Document Q&A, contract analysis, summaries and compliance stay deterministic by design (no LLM).
- Existing `lrw-local` stack must be rebuilt (`up --build`) to pick these changes up.
- Nothing pushed: the branch must be pushed before the GitHub ZIP contains these commits.
