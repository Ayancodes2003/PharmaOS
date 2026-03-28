# Phase 5: Feature Engineering and Analytics Marts

## Goal

Transform Phase 4 `feature_ready` artifacts into reusable ML feature datasets and BI-ready analytics marts.

## Scope

- Eligibility feature engineering
- Safety risk feature engineering
- Recruitment ranking feature engineering
- Analytics marts for operations, screening, monitoring, and model-readiness support
- Metadata and manifest artifacts for downstream ML/BI consumers

## Data Inputs

Phase 5 reads deterministic Stage 4 artifacts from:

- `data/feature_ready/patients/{run_id}.csv`
- `data/feature_ready/trials/{run_id}.csv`
- `data/feature_ready/adverse_events/{run_id}.csv`
- `data/feature_ready/drug_exposures/{run_id}.csv`

## Data Outputs

Feature datasets:

- `eligibility_features_{run_id}.csv`
- `safety_features_{run_id}.csv`
- `recruitment_features_{run_id}.csv`

Analytics marts:

- `patient_screening_funnel_{run_id}.csv`
- `trial_eligibility_{run_id}.csv`
- `adverse_event_monitoring_{run_id}.csv`
- `recruitment_kpis_{run_id}.csv`
- `model_monitoring_support_{run_id}.csv`

Metadata outputs:

- `artifacts/reports/phase5/feature_summary_{run_id}.json`
- `artifacts/reports/phase5/analytics_summary_{run_id}.json`
- `artifacts/reports/phase5/phase5_manifest_{run_id}.json`

## Design Notes

- Feature builders are modularized by use case under `features/engineering/`.
- Mart builders are modularized under `analytics/marts/builders/`.
- Output and metadata concerns are isolated in `analytics/exports/`.
- No model training, inference serving, dashboard rendering, or agent workflow logic is included in this phase.
