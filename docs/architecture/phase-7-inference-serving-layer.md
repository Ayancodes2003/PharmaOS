# Phase 7: Model Loading, Inference Services, and Persistence-Ready Serving Layer

## Goal

Make Phase 6 model artifacts operational for backend inference workflows with deterministic feature preparation, structured outputs, model provenance, and persistence support.

## Scope

- Local artifact/metadata-driven model loading abstraction
- Inference input contracts for eligibility, safety, recruitment workflows
- Inference-safe feature preparation aligned with Phase 5 engineering logic
- Prediction services with optional persistence into PostgreSQL
- Audit logging support for inference traceability
- Operational CLI runners for single and all-use-case inference

## Design

- `ml/registry/`: model bundle loading and provenance contracts.
- `ml/inference/contracts.py`: request/response schemas.
- `ml/inference/feature_prep.py`: deterministic train-serve aligned transformations.
- `services/prediction_services.py`: use-case prediction services and persistence logic.
- `ml/inference/orchestration.py`: single/all-use-case orchestration helpers.
- `scripts/run_inference.py`: operational CLI entrypoint.

## Persistence

Prediction outputs can be persisted through repository abstractions:

- EligibilityPrediction
- SafetyPrediction
- RecruitmentRanking

Audit entries are written to `audit_logs` with model provenance and trace ids.

## Traceability

Inference payloads include model provenance:

- model_name
- model_version
- training_run_id
- label_source_type
- target_mode
- weak_supervision
- feature schema columns

Operational run summaries are persisted to `PHASE7_REPORTS_PATH`.
