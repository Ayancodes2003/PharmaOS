"""Feature matrix preparation utilities for model training."""

from __future__ import annotations

import pandas as pd

IDENTIFIER_COLUMNS = {
    "external_patient_id",
    "patient_external_id",
    "trial_code",
    "drug_name",
}

TARGET_COLUMNS = {
    "target_eligibility_label",
    "target_safety_label",
    "target_recruitment_label",
    "target_eligibility_available",
    "target_safety_available",
}


def build_feature_matrix(
    *,
    df: pd.DataFrame,
    dropped_feature_columns: list[str],
) -> pd.DataFrame:
    """Construct a leakage-aware feature matrix from input artifact dataframe."""
    blocked = set(dropped_feature_columns) | IDENTIFIER_COLUMNS | TARGET_COLUMNS
    feature_columns = [column for column in df.columns if column not in blocked]
    return df.reindex(columns=feature_columns).copy()
