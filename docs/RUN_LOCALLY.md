# Run the app locally (one command)

Development build for teammates. **All data is synthetic.** Uploaded files stay **quarantined** because no malware scanner runs in this setup; that is intended (fail closed), not a bug.

## Prerequisites

- Docker Desktop (running), git, about 8 GB free RAM and ~3 GB disk.
- Free port **8000**.

## Start

```bash
git clone https://github.com/loktrishal-05/legal-compliance-regulatory-workbench.git
cd legal-compliance-regulatory-workbench
cp .env.example .env            # Windows PowerShell: Copy-Item .env.example .env
docker compose --env-file .env -f deploy/local/docker-compose.yml up --build
```

The first build takes a few minutes (frontend build + Python packages). When the log shows `Uvicorn running on http://0.0.0.0:8000`, open **http://localhost:8000**.

On first start the app container runs database migrations and seeds a synthetic demo workspace once (contracts with analysis and an approved obligation, a regulatory source with two versions, compliance assessments in several states including a stale one, tasks and notifications). Later starts print `already_seeded`.

## Demo accounts

On the sign-in page, choose a role under **"Demo data only — synthetic"**, press **Use demo account** (it only fills the fields), then **Sign in**.

| Role | Username | What to try |
|---|---|---|
| Legal counsel (reviewer) | `demo-counsel` | Legal → Contracts, Review queue, Source viewer |
| Compliance reviewer | `demo-compliance` | Review queue (compliance items) |
| Analyst | `demo-analyst` | Documents, propose corrections, submit for review |
| Business owner | `demo-owner` | Obligations & tasks assigned to them |
| Auditor (read-only) | `demo-auditor` | Legal audit |
| Workspace admin | `demo-admin` | Membership metadata only (no document access by design) |

Passwords are the `DEMO_*_PASSWORD` values in your `.env` (the defaults are local-only placeholders; change them before the first start if you like). After signing in, use the **Legal** group in the sidebar. The old "Operate / Legacy industrial" pages are not served by this lean local image and show "not available".

## Stop and reset

```bash
docker compose -f deploy/local/docker-compose.yml down        # stop, keep data
docker compose -f deploy/local/docker-compose.yml down -v     # stop and delete all local data (re-seeds on next start)
```

## Troubleshooting

- **Port 8000 busy:** stop the other process, or change `"8000:8000"` to e.g. `"8080:8000"` in `deploy/local/docker-compose.yml` and add `http://localhost:8080` to `WORKBENCH_CORS_ORIGINS` there (the origin check rejects unknown origins).
- **"Cannot connect to the Docker daemon":** start Docker Desktop and wait until it reports it is running.
- **First build slow / npm or pip timeouts:** re-run the same command; finished layers are cached.
- **Changed demo passwords after the first start:** run `down -v` and start again (the seed runs only once).
- **Sign-in says the origin is not allowed:** open the app exactly at `http://localhost:8000` (or `http://127.0.0.1:8000`).

## What this is not

Not a production deployment: no enterprise sign-in, no malware scanner, no AI model (legal analysis is deterministic), local Postgres only. See `docs/parallel/EVIDENCE_A.md` for what is implemented and tested and which gates remain open.
