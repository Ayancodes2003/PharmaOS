# PHARMA-OS

PHARMA-OS is an end-to-end clinical intelligence backend that connects data pipelines, machine learning, agent workflows, API delivery, and BI exports in one coherent system.

It is built as a practical portfolio project for teams working on trial operations, safety monitoring, and AI-assisted clinical workflows.

## What Problem This Solves

Clinical and pharma workflows are often fragmented across disconnected tooling:

- ingestion jobs in one stack
- model development in another
- operational APIs elsewhere
- analyst reporting as a separate manual process

PHARMA-OS demonstrates a single platform where these concerns connect cleanly:

- source-to-feature-to-model pipeline continuity
- reproducible inference and model artifact tracking
- grounded agent orchestration with operational traces
- BI-ready exports for recruiter/reviewer-visible business usability

## Why It Is Relevant

For pharma and clinical intelligence use cases, value is not only in model performance. It is also in:

- operationalizing predictions and rankings
- making workflows observable and auditable
- enabling analysts to consume outputs without reverse-engineering data science artifacts

PHARMA-OS focuses on that full lifecycle.

## Core Capabilities

- Structured data ingestion and preprocessing pipelines
- Feature engineering and analytics mart generation
- ML training flows for eligibility, safety, and recruitment ranking use cases
- Inference services with persistence and artifact resolution
- Agent workflows for eligibility analysis, safety investigation, and research summarization
- FastAPI v1 route layer for system, domain, predictions, agents, and operations
- Power BI-friendly export layer with grouped datasets and manifests
- Docker-based runtime for local reproducibility

## Architecture Overview

High-level system flow:

1. Ingest and standardize source datasets into processed and load-ready outputs.
2. Build feature-ready datasets and analytics marts.
3. Train and register ML artifacts for core prediction domains.
4. Serve inference flows and persist outputs for operations.
5. Run grounded agent workflows with trace persistence.
6. Expose capabilities through API routes.
7. Publish BI export groups and manifests for analyst/reporting consumption.

Detailed architecture docs:

- docs/architecture/phase-1-bootstrap.md
- docs/architecture/phase-2-runtime-foundation.md
- docs/architecture/phase-5-feature-engineering-analytics.md
- docs/architecture/phase-6-ml-training-pipelines.md
- docs/architecture/phase-7-inference-serving-layer.md
- docs/architecture/phase-8-agentic-ai-orchestration.md
- docs/architecture/system-overview.md

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy + Alembic
- PostgreSQL
- MongoDB (Motor / PyMongo)
- Pydantic + pydantic-settings
- Pandas / Polars
- Scikit-learn + XGBoost
- LangGraph
- Docker / Docker Compose

## Project Structure

```text
PharmaOS/
  src/pharma_os/
    api/                # FastAPI route groups and schemas
    core/               # Settings, lifecycle, shared exceptions
    db/                 # Models, repositories, DB bootstrap
    pipelines/          # Ingestion and preprocessing orchestration
    features/           # Feature engineering
    ml/                 # Training, registry, inference
    agents/             # Agent orchestration and tools
    analytics/          # Analytics marts and BI exports
    observability/      # Logging and operational instrumentation
  scripts/              # CLI operational entrypoints
  data/                 # Raw/processed/feature/mart data artifacts
  artifacts/            # Models, metrics, reports, export outputs
  docs/                 # Architecture and reviewer-facing documentation
```

## Quick Start

Prerequisites:

- Python 3.11+
- Docker Desktop (or Docker Engine + Compose)

Setup:

1. Install dependencies.

```bash
pip install -e .[dev]
```

2. Create environment file.

Linux/macOS:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

3. Start dependencies.

```bash
make up-deps
```

4. Run API locally.

```bash
make run-api
```

5. Run runtime smoke checks.

```bash
make smoke
```

6. Or run the full containerized stack.

```bash
make up
```

Health endpoints:

- GET /api/v1/system/health
- GET /api/v1/system/readiness

## Example Workflows

1. Run structured data pipelines.

```bash
python scripts/run_data_pipeline.py
```

2. Generate feature outputs and analytics marts.

```bash
python scripts/run_feature_analytics.py --run-id <pipeline_run_id>
```

3. Train ML models.

```bash
python scripts/run_ml_training.py --feature-run-id <feature_run_id> --use-case all
```

4. Run inference flows.

```bash
python scripts/run_inference.py --use-case eligibility --input <path_to_request_json> --persist
```

5. Generate BI exports.

```bash
python scripts/run_analytics_exports.py --phase5-run-id <feature_run_id>
```

## Key Outputs

- Data pipeline artifacts in data/processed and data/load_ready
- Feature and mart outputs in data/feature_store and data/analytics_marts
- Training reports and model artifacts in artifacts/reports/phase6 and artifacts/models
- Inference summaries in artifacts/reports/phase7
- BI export tables and manifests in artifacts/exports and artifacts/reports/phase10

## What Makes This End-to-End

- Multi-stage lifecycle from ingestion to analyst-facing exports
- API layer over operational and model workflows
- Dual persistence model for structured domain data and flexible agent traces
- Explicit runtime checks and smoke validation for reproducibility

## Honest Limitations

- No production auth/authorization layer yet
- No cloud deployment stack in-repo (intentionally out of scope)
- Limited automated integration/E2E coverage compared to unit-level coverage
- Synthetic/sample data assumptions may need adaptation for real clinical datasets

## Future Improvements

- Add role-based access and API key/OIDC security model
- Expand CI validation with integration smoke in containerized pipelines
- Add richer model monitoring metrics and drift alerts
- Add API contract examples for common reviewer evaluation paths

## Reviewer Navigation

- System overview: docs/architecture/system-overview.md
- Demo/evaluation path: docs/reviewer-demo-flow.md
- Resume/interview translation: docs/portfolio-positioning.md