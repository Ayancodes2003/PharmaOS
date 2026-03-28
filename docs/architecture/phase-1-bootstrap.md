# PHARMA-OS Phase 1: Repository Bootstrap

## Architecture Decisions

1. Monorepo, modular Python package under `src/pharma_os` to keep all platform capabilities cohesive while maintaining clear boundaries.
2. Layered backend architecture:
   - API layer (`api`)
   - Service orchestration layer (`services`)
   - Data access layer (`db/repositories`)
   - Persistence models and contracts (`db/models`, `db/schemas`)
3. Pipeline domains are separated by lifecycle stage to enforce deterministic execution:
   - ingestion
   - preprocessing
   - features
   - ml training/inference
4. Agentic AI components are isolated under `agents` with workflow and tool boundaries for future RAG and traceability integrations.
5. Analytics mart and BI export responsibilities are isolated under `analytics/marts` and `analytics/exports`.
6. Infrastructure artifacts are separated from application code under `infra` and runtime orchestration (`docker-compose.yml`).
7. All runtime and dependency controls are centralized in `pyproject.toml` and `.env`-based configuration.

## Bootstrap Scope

This phase intentionally focuses on structure and enforceable conventions, not business implementation.

- Repository topology
- Build/dependency metadata
- Environment template
- Local infra runtime services
- Testing/quality toolchain defaults

## Phase Exit Criteria

- Project installs as a Python package.
- Baseline module paths are stable for later implementation.
- Local PostgreSQL and MongoDB can be started via Docker Compose.
- Development tooling (pytest/ruff/mypy) is pre-configured.
