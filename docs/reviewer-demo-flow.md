# Reviewer Demo Flow

This is the fastest technical evaluation path for PHARMA-OS without needing to read the full codebase first.

## 1) Bring Up Dependencies

```bash
make up-deps
```

## 2) Configure Environment

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

## 3) Run API

```bash
make run-api
```

## 4) Validate Runtime

```bash
make smoke
```

Optional API-level probe:

```bash
make smoke-api
```

## 5) Inspect Core Service Endpoints

- GET /api/v1/system/health
- GET /api/v1/system/readiness
- GET /api/v1/operations/service-metadata
- GET /api/v1/operations/model-artifacts

## 6) Execute Data and ML Workflow Path

```bash
python scripts/run_data_pipeline.py
python scripts/run_feature_analytics.py --run-id <pipeline_run_id>
python scripts/run_ml_training.py --feature-run-id <feature_run_id> --use-case all
```

## 7) Execute Inference Path

```bash
python scripts/run_inference.py --use-case eligibility --input <request_json_path> --persist
```

## 8) Execute BI Export Path

```bash
python scripts/run_analytics_exports.py --phase5-run-id <feature_run_id>
```

Then inspect:

- artifacts/exports/power_bi/<export_run_id>/
- artifacts/reports/phase10/phase10_export_manifest_<export_run_id>.json

## What Reviewers Should Look For

- Practical end-to-end continuity from ingestion to BI outputs
- Separation of concerns between pipelines, ML, agents, API, and exports
- Reproducible runtime behavior through make targets and smoke checks
- Clear artifact lineage via run ids and manifests
