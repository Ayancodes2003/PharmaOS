"""Dataset loaders for Phase 5 feature artifacts consumed in Phase 6 training."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pharma_os.core.settings import Settings
from pharma_os.pipelines.common.io import read_dataset

FEATURE_DATASET_NAMES: dict[str, str] = {
    "eligibility": "eligibility_features",
    "safety": "safety_features",
    "recruitment": "recruitment_features",
}

REQUIRED_COLUMNS: dict[str, list[str]] = {
    "eligibility": [
        "external_patient_id",
        "trial_code",
        "condition_match",
        "trial_fit_score_component",
    ],
    "safety": [
        "patient_external_id",
        "drug_name",
        "safety_risk_component",
    ],
    "recruitment": [
        "external_patient_id",
        "trial_code",
        "ranking_score_component",
    ],
}


def load_feature_dataset(*, use_case: str, run_id: str, settings: Settings) -> pd.DataFrame:
    """Load a feature dataset by use case and run id with required schema checks."""
    if use_case not in FEATURE_DATASET_NAMES:
        raise ValueError(f"Unsupported use_case: {use_case}")

    dataset_name = FEATURE_DATASET_NAMES[use_case]
    dataset_path = Path(settings.data_feature_store_path) / f"{dataset_name}_{run_id}.csv"
    df = read_dataset(dataset_path)

    missing = [column for column in REQUIRED_COLUMNS[use_case] if column not in df.columns]
    if missing:
        raise ValueError(
            f"Dataset '{dataset_name}' missing required columns for use case '{use_case}': {missing}"
        )

    return df
