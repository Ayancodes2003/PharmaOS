"""Feature matrix preparation utilities for model training."""

from __future__ import annotations

import pandas as pd

from pharma_os.ml.contracts import FeatureMatrixBuildResult

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

LEAKAGE_TOKEN_GUARDS = (
    "target_",
    "label",
    "ground_truth",
    "proxy",
    "outcome",
)


def build_feature_matrix(
    *,
    df: pd.DataFrame,
    dropped_feature_columns: list[str],
) -> FeatureMatrixBuildResult:
    """Construct a leakage-aware feature matrix from input artifact dataframe."""
    all_columns = [str(column) for column in df.columns]

    identifier_excluded = [column for column in all_columns if column in IDENTIFIER_COLUMNS]
    target_excluded = [column for column in all_columns if column in TARGET_COLUMNS]
    derivation_excluded = [column for column in all_columns if column in set(dropped_feature_columns)]

    guard_excluded = [
        column
        for column in all_columns
        if any(token in column.lower() for token in LEAKAGE_TOKEN_GUARDS)
    ]

    blocked = set(identifier_excluded) | set(target_excluded) | set(derivation_excluded) | set(guard_excluded)
    feature_columns = [column for column in all_columns if column not in blocked]

    excluded_columns = sorted(blocked)
    leakage_notes = [
        "Systematic leakage guard enabled for identifier columns, target columns, explicit target-derivation columns, and leakage-token columns.",
    ]
    if guard_excluded:
        leakage_notes.append(
            "Leakage-token exclusion removed columns matching tokens: "
            + ", ".join(sorted(guard_excluded))
        )

    return FeatureMatrixBuildResult(
        X=df.reindex(columns=feature_columns).copy(),
        used_feature_columns=feature_columns,
        excluded_feature_columns=excluded_columns,
        excluded_identifier_columns=sorted(identifier_excluded),
        excluded_target_columns=sorted(target_excluded),
        excluded_derivation_columns=sorted(derivation_excluded),
        leakage_guard_notes=leakage_notes,
    )
