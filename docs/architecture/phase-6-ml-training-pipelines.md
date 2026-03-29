# Phase 6: Machine Learning Training Pipelines

## Goal

Train and evaluate reproducible models using Phase 5 feature artifacts with explicit target strategy, artifact traceability, and future serving compatibility.

## Scope

- Use-case-specific dataset loading
- Explicit target loading and conservative target derivation
- Binary classification pipelines for eligibility and safety
- Score-based recruitment ranking artifact when supervised labels are unavailable
- Evaluation metrics and confusion-matrix-friendly outputs
- Artifact persistence for models, metrics, feature manifests, and run manifests
- Operational CLI orchestration

## Use Cases

1. Trial Eligibility Prediction
2. Adverse Drug Safety Risk Prediction
3. Recruitment Ranking / Prioritization

## Design

- `ml/data/`: load and validate feature datasets by run id.
- `ml/targets/`: target preparation with explicit-vs-derived mode tracking.
- `ml/training/`: leakage-aware feature matrix prep and model training.
- `ml/evaluation/`: classification metrics and feature-importance extraction.
- `ml/persistence/`: model + metrics + metadata artifact writing.
- `ml/orchestration/`: per-use-case and all-use-case training runners.

## Artifacts

- Model artifacts under `MODEL_REGISTRY_PATH/{use_case}/{training_run_id}/`
- Metrics under `METRICS_PATH/{use_case}/{training_run_id}/`
- Metadata and manifests under `PHASE6_REPORTS_PATH`

## Target Strategy Notes

- Eligibility and safety: use explicit labels when available; otherwise derive conservative proxy labels from present-time clinical suitability/risk criteria.
- Recruitment: if no explicit supervised label is available, persist deterministic score-based ranking config instead of fabricating labels.

## Phase 6.5 Integrity Hardening

- Target provenance is explicit in all metadata (`observed_ground_truth`, `derived_proxy`, `deterministic_score`).
- Weak-label runs are flagged with warnings and context-specific performance-claim guidance.
- Leakage guards now persist:
	- identifier exclusions
	- target column exclusions
	- proxy derivation-column exclusions
	- token-based leakage exclusions
- Training metadata persists split sizes and model-selection rationale for reproducibility and reviewability.
- Recruitment score-only path is explicitly labeled as non-supervised prioritization (not a trained ranking model).
