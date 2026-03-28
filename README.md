# PHARMA-OS

Multi-Agent Clinical Intelligence, Trial Matching, and Drug Safety Platform.

## Vision

PHARMA-OS is a production-grade backend and AI platform designed for pharmaceutical and health-tech workloads.
The system combines data engineering, machine learning, agentic AI workflows, and analytics-ready outputs for clinical operations.

## Core Capabilities

- Structured and unstructured clinical data ingestion
- Patient-trial eligibility prediction
- Adverse drug safety risk prediction
- Candidate ranking for clinical recruitment
- Multi-agent orchestration for research and operational workflows
- API-driven backend services for model and data operations
- PostgreSQL + MongoDB hybrid persistence
- Power BI-ready analytics exports and marts

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy + Alembic
- PostgreSQL
- MongoDB (Motor/PyMongo)
- Pydantic
- Pandas / Polars
- Scikit-learn + XGBoost
- LangGraph
- Docker / Docker Compose

## Repository Structure

```text
PharmaOS/
	src/pharma_os/
		api/                # Versioned API surfaces
		core/               # Shared config/constants/bootstrap
		db/                 # Models, repositories, schemas
		services/           # Business service layer
		pipelines/          # Ingestion + preprocessing pipelines
		features/           # Feature engineering logic
		ml/                 # Training, inference, registry
		agents/             # Agent workflows and tools
		analytics/          # Marts and BI exports
		observability/      # Logging, metrics, tracing adapters
	alembic/              # DB migrations
	docs/architecture/    # Architecture decisions by phase
	data/                 # Raw, processed, feature store
	artifacts/            # Models, metrics, reports
	infra/                # Container/K8s deployment assets
	scripts/              # Operational scripts
	tests/                # Unit/integration/e2e tests
```

## Delivery Phases

1. Repository and architecture bootstrap
2. Config, environment, logging, shared utilities
3. Database schema and data access layer
4. Data ingestion and preprocessing pipelines
5. Feature engineering and analytics marts
6. Machine learning training pipelines
7. Model registry, loading, inference services
8. Agentic AI orchestration layer
9. FastAPI route layer
10. Power BI export layer
11. Deployment and Dockerization
12. Documentation and production README finalization

## Local Bootstrap

1. Install dependencies:

```bash
pip install -e .[dev]
```

2. Copy environment template:

```bash
cp .env.example .env
```

3. Start local databases:

```bash
docker compose up -d
```

4. Run API (scaffold stage):

```bash
uvicorn pharma_os.main:app --host 0.0.0.0 --port 8000 --reload
```

## Current Status

Phase 1 completed: repository topology, dependency metadata, local data services, and baseline engineering conventions.

Phase 2 completed: production-grade runtime foundation including typed settings, structured logging, exception hierarchy, PostgreSQL/MongoDB connectivity, FastAPI lifecycle wiring, health/readiness endpoints, and dependency injection.