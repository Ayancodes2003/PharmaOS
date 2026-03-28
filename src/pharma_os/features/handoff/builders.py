"""Feature-ready handoff builders for downstream analytics and ML workflows."""

from __future__ import annotations

import pandas as pd

from pharma_os.pipelines.common.contracts import PipelineDomain

FEATURE_READY_COLUMNS: dict[PipelineDomain, list[str]] = {
    PipelineDomain.PATIENTS: [
        "external_patient_id",
        "age",
        "sex",
        "primary_condition",
        "diagnosis_code",
        "enrollment_status",
        "is_active",
    ],
    PipelineDomain.TRIALS: [
        "trial_code",
        "indication",
        "phase",
        "status",
        "recruitment_target",
        "enrolled_count",
    ],
    PipelineDomain.ADVERSE_EVENTS: [
        "patient_external_id",
        "trial_code",
        "drug_name",
        "event_type",
        "severity",
        "is_serious",
        "outcome",
        "event_date",
    ],
    PipelineDomain.DRUG_EXPOSURES: [
        "patient_external_id",
        "trial_code",
        "drug_name",
        "drug_class",
        "dose_value",
        "route",
        "frequency",
        "start_date",
        "end_date",
        "is_active",
    ],
}


def build_feature_ready_dataset(domain: PipelineDomain, df: pd.DataFrame) -> pd.DataFrame:
    """Build feature-ready handoff table without full feature engineering."""
    if domain not in FEATURE_READY_COLUMNS:
        raise ValueError(f"Feature handoff unsupported for domain: {domain.value}")

    selected = FEATURE_READY_COLUMNS[domain]
    available = [column for column in selected if column in df.columns]
    feature_df = df.reindex(columns=available).copy()
    return feature_df
