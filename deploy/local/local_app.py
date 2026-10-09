"""One-origin local app for teammates: auth + all legal routers + the built SPA, same session/origin rules.

Reuses app/main.py's browser_origin_guard and validation handler verbatim (as the tests do) without importing
the industrial router stack (torch/paddle/qdrant/langgraph). The SPA calls /api/...; that prefix is stripped so
the backend sees its real paths. Development only — synthetic demo data, uploads quarantined without a scanner.
"""
import ast
import importlib
import pkgutil
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse

import app.api.routes as routes
from app.api.routes import auth
from app.core.config import settings

BACKEND = Path(__file__).resolve().parents[2] / "backend"
DIST = Path("/srv/frontend")
API_PREFIXES = ("v1/", "auth/", "health")

web = FastAPI(title="Legal & Regulatory Assurance Platform (local)")
tree = ast.parse((BACKEND / "app/main.py").read_text(encoding="utf-8"))
functions = [node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)
             and node.name in {"browser_origin_guard", "validation_error"}]
for node in functions:
    node.decorator_list = []
namespace = {"settings": settings, "JSONResponse": JSONResponse, "urlsplit": urlsplit}
exec(compile(ast.Module(body=functions, type_ignores=[]), "app/main.py", "exec"), namespace)
web.middleware("http")(namespace["browser_origin_guard"])
web.add_exception_handler(RequestValidationError, namespace["validation_error"])
web.include_router(auth.router)
for module in sorted(m.name for m in pkgutil.iter_modules(routes.__path__) if m.name.startswith("legal_")):
    web.include_router(importlib.import_module(f"app.api.routes.{module}").router)


@web.get("/health")
def health():
    return {"status": "ok", "service": "legal-compliance-regulatory-workbench-backend"}


@web.get("/{path:path}", include_in_schema=False)
def spa(path: str, request: Request):
    # Anything the SPA sent to /api that no router matched (e.g. legacy industrial APIs not served by this
    # lean image) gets an honest JSON 404, never index.html.
    if request.scope.get("lrw_api") or path.startswith(API_PREFIXES):
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    candidate = (DIST / path).resolve()
    if path and candidate.is_file() and DIST.resolve() in candidate.parents:
        return FileResponse(candidate)
    return FileResponse(DIST / "index.html", headers={"Cache-Control": "no-store"})


async def app(scope, receive, send):
    """Strip the SPA's /api prefix (the Vite dev proxy does the same) before routing."""
    if scope["type"] == "http" and (scope["path"] == "/api" or scope["path"].startswith("/api/")):
        stripped = scope["path"][4:] or "/"
        scope = dict(scope, path=stripped, raw_path=stripped.encode(), lrw_api=True)
    await web(scope, receive, send)
