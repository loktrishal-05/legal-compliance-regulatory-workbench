"""Legal worker: durable document jobs, outbox dispatch and scheduler scans in one loop.

Usage: python -m scripts.legal_worker [--once] [--interval 5]
Importing every app.services.legal_* module registers all agents' review targets, event handlers and scans.
"""
import argparse
import importlib
import os
import pkgutil
import socket
import time

import app.services
from app.core.config import settings
from app.db.session import SessionLocal
from app.services import legal_jobs


def register_all():
    names = sorted(m.name for m in pkgutil.iter_modules(app.services.__path__) if m.name.startswith("legal_"))
    return [importlib.import_module(f"app.services.{name}").__name__ for name in names]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=5.0)
    args = parser.parse_args(argv)
    register_all()
    worker_id = f"{socket.gethostname()}:{os.getpid()}"[:100]
    while True:
        with SessionLocal() as db:
            result = legal_jobs.run_once(db, worker_id=worker_id, data_root=settings.data_root,
                                         current_terms_version=settings.current_terms_version)
        print({"worker": worker_id, **result}, flush=True)  # counts and codes only, never content
        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
