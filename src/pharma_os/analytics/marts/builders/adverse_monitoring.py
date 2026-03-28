"""Adverse event monitoring mart builders."""

from __future__ import annotations

import pandas as pd


def build_adverse_event_monitoring_mart(
    *,
    adverse_events_df: pd.DataFrame,
    safety_features: pd.DataFrame,
) -> pd.DataFrame:
    """Build grouped adverse event and exposure-linked monitoring summaries."""
    if adverse_events_df.empty:
        return pd.DataFrame(
            columns=[
                "drug_name",
                "severity",
                "is_serious",
                "event_count",
                "distinct_patients",
                "avg_safety_risk_component",
            ]
        )

    events = adverse_events_df.copy()
    safety = safety_features[["patient_external_id", "drug_name", "safety_risk_component"]].copy()

    joined = events.merge(
        safety,
        how="left",
        on=["patient_external_id", "drug_name"],
    )

    mart = (
        joined.groupby(["drug_name", "severity", "is_serious"], dropna=False)
        .agg(
            event_count=("event_type", "count"),
            distinct_patients=("patient_external_id", "nunique"),
            avg_safety_risk_component=("safety_risk_component", "mean"),
        )
        .reset_index()
    )

    mart["avg_safety_risk_component"] = mart["avg_safety_risk_component"].fillna(0.0)
    return mart.sort_values(by=["event_count", "distinct_patients"], ascending=[False, False], kind="stable")
