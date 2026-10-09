#!/bin/sh
# Local start: migrate, seed synthetic demo data once (idempotent), start the legal worker, then serve on :8000.
set -e
cd /app/backend
alembic upgrade head
if [ "$LEGAL_DEMO_MODE" = "true" ]; then
  python -m scripts.legal_demo_seed || echo "WARNING: demo seed failed; the app still starts (see log above)."
fi
python -m scripts.legal_worker --interval 5 > /tmp/legal-worker.log 2>&1 &
exec python -m uvicorn local_app:app --app-dir /app/deploy/local --host 0.0.0.0 --port 8000 --proxy-headers
