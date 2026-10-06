# Legal & Regulatory Assurance Platform

Application repository: [legal-compliance-regulatory-workbench](https://github.com/loktrishal-05/legal-compliance-regulatory-workbench).
Use this repository for all application changes and pushes. See [repository instructions](AGENTS.md).

Current workspace setup: [isolated legal runtime guide](docs/LEGAL_RUNTIME_SETUP.md).
Build status and required phase checks: [living migration plan](docs/LEGAL_DOMAIN_MIGRATION_PLAN.md).
**Development migration:** contract intelligence, legal compliance monitoring and legal summaries are not yet available. Phases A/B established custody and build contracts; Phase C migrates identity. Existing industrial views are retained as clearly labelled platform regressions until their legal replacements are validated.

## Specification and build guide

The unchanged [master report](docs/Legal_Regulatory_Assurance_Platform_Master_Report.pdf) is the product authority. Read the [build contracts](docs/LEGAL_DOMAIN_BUILD_CONTRACTS.md), [requirement registry](docs/LEGAL_REQUIREMENT_TRACEABILITY.md), [progress](docs/MIGRATION_PROGRESS.md) and [validation evidence](docs/VALIDATION_REPORT.md) before each phase. Planning does not establish legal accuracy or implemented requirements.

## Reusable foundation

React/Vite → FastAPI → scoped workflows and local/private model gateway → evidence validation → immutable advisory revision → independent human review.

Source-level infrastructure includes PostgreSQL/SQLAlchemy/Alembic, Qdrant hybrid retrieval and reranking, PDF/OCR provenance, opaque cookie sessions, durable LangGraph recovery, evidence integrity and deterministic tamper-evident audit. Tenant/matter ACLs and legal bounded modules are still planned. Ollama is implemented; vLLM remains a placeholder.

## Historical platform records

Earlier industrial implementation and validation documents are preserved as provenance, not current setup instructions or legal acceptance:
See [Phase 3A guide](docs/phase3a.md) for ingestion and retrieval setup.
See [Phase 3B1 guide](docs/phase3b1.md) for local P&ID/image OCR preparation.
See [Phase 3B2 guide](docs/phase3b2.md) for hybrid retrieval, the explicit Qdrant
migration, local reranking, OCR text indexing, and retrieval evaluation.
See [Phase 3C guide](docs/phase3c.md) for maintenance/sensor CSV ingestion,
deterministic feature extraction, and anomaly observations.
See [Phase 4A guide](docs/phase4a.md) for the local model gateway: structured
output, tool-call parsing, and the Ollama/vLLM runtime abstraction.
See [Phase 4R repair record](docs/phase4-repair.md) for current specialist
agent safety and evidence-handling status.
See [Phase 5A governance boundary](docs/phase5a.md) and its
[validation record](docs/phase5a-validation.md) for immutable pending proposals.
See [Phase 5B approval workflow](docs/phase5b.md) and its
[validation record](docs/phase5b-validation.md) for local authentication and
the authenticated approve/reject/revoke/release workflow.

## Runtime and authority boundary

Use [current runtime instructions](docs/LEGAL_RUNTIME_SETUP.md), not old ports/worktree commands. Preserve and privately review any existing `.env`; never overwrite it or point to another application's services. No database, volume or existing index is renamed by the identity phase.

Deploy the backend and frontend identity change together. `/health` retains its process-liveness shape but now identifies this legal backend; the frontend deliberately rejects the old industrial identity rather than connecting to an unrelated application. Health is not database/model readiness or legal acceptance.

Health endpoint after approved startup: `GET http://127.0.0.1:18000/health`

```json
{"status":"ok","service":"legal-compliance-regulatory-workbench-backend"}
```

AI remains advisory. No contract signing/filing, legal advice, compliance certification or live regulatory connector is claimed. Legacy v1.0 terms and receipts stay unchanged and labelled during development; a new legal-platform terms version requires approval. Qualified owners must approve deployment-specific legal packs, identity, retention/hold and recovery policies before operational pilot readiness. Local checkpoint commits are authorized; pushes remain separately gated.
