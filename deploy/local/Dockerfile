# Teammate local run: built SPA + lean legal backend (no torch/paddle/qdrant). Development only.
FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
# Synthetic demo login values are baked into this LOCAL bundle on purpose (demo build only).
ARG VITE_DEMO_MODE=true
ARG VITE_DEMO_ADMIN_PASSWORD VITE_DEMO_COUNSEL_PASSWORD VITE_DEMO_COMPLIANCE_PASSWORD
ARG VITE_DEMO_ANALYST_PASSWORD VITE_DEMO_OWNER_PASSWORD VITE_DEMO_AUDITOR_PASSWORD
ENV VITE_API_BASE_URL=/api
RUN npm run build

FROM python:3.11-slim
RUN pip install --no-cache-dir fastapi==0.141.1 starlette==1.7.0 pydantic==2.13.5 pydantic-settings==2.15.0 \
    SQLAlchemy==2.0.54 alembic==1.20.0 "psycopg[binary]==3.3.6" httpx==0.28.1 argon2-cffi==23.1.0 \
    pymupdf==1.28.2 uvicorn==0.54.0 email-validator==2.3.0 dnspython==2.8.0 Authlib==1.8.0
WORKDIR /app
COPY backend /app/backend
COPY deploy/local /app/deploy/local
COPY --from=web /web/dist /srv/frontend
RUN useradd --uid 10001 --create-home workbench && mkdir -p /data && chown workbench /data \
    && sed -i 's/\r$//' /app/deploy/local/entrypoint.sh
USER workbench
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/app/backend WORKBENCH_DATA_ROOT=/data
EXPOSE 8000
CMD ["sh", "/app/deploy/local/entrypoint.sh"]
