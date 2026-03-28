"""Model monitoring support mart builders."""

from __future__ import annotations

import pandas as pd


def build_model_monitoring_support_mart(
    *,
    eligibility_features: pd.DataFrame,
    safety_features: pd.DataFrame,
    recruitment_features: pd.DataFrame,
) -> pd.DataFrame:
    """Build dataset readiness and target-availability support metrics."""
    rows: list[dict[str, object]] = []

    rows.append(
        _dataset_monitor_row(
            dataset_name="eligibility_features",
            df=eligibility_features,
            target_column="target_eligibility_label",
        )
    )
    rows.append(
        _dataset_monitor_row(
            dataset_name="safety_features",
            df=safety_features,
            target_column="target_safety_label",
        )
    )
    rows.append(
        _dataset_monitor_row(
            dataset_name="recruitment_features",
            df=recruitment_features,
            target_column=None,
        )
    )

    return pd.DataFrame(rows)


def _dataset_monitor_row(
    *,
    dataset_name: str,
    df: pd.DataFrame,
    target_column: str | None,
) -> dict[str, object]:
    row_count = int(len(df.index))
    column_count = int(len(df.columns))
    null_ratio = float(df.isna().mean().mean()) if row_count > 0 and column_count > 0 else 0.0

    target_available = 0
    target_positive_ratio = 0.0
    if target_column and target_column in df.columns:
        target_series = df[target_column]
        target_available = int(target_series.notna().sum())
        if target_available > 0:
            target_positive_ratio = float((target_series.fillna(0).astype(str) == "1").mean())

    readiness = "ready" if row_count > 0 and null_ratio < 0.35 else "not_ready"

    return {
        "dataset_name": dataset_name,
        "row_count": row_count,
        "column_count": column_count,
        "target_available_rows": target_available,
        "target_positive_ratio": target_positive_ratio,
        "avg_null_ratio": null_ratio,
        "training_readiness": readiness,
    }
