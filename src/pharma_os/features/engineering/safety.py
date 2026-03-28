"""Feature generation for adverse drug safety risk prediction."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from pharma_os.features.engineering.common import bool_to_int, days_since, safe_to_datetime, severity_to_score


def build_safety_features(
    *,
    patients_df: pd.DataFrame,
    adverse_events_df: pd.DataFrame,
    drug_exposures_df: pd.DataFrame,
) -> pd.DataFrame:
    """Build ML-ready patient-drug safety features."""
    now = pd.Timestamp(datetime.now(UTC))

    patients = patients_df[["external_patient_id", "age", "sex", "primary_condition"]].copy()
    patients["age"] = pd.to_numeric(patients["age"], errors="coerce").fillna(0)

    events = adverse_events_df.copy()
    events["event_days_ago"] = days_since(now, events["event_date"])
    events["severity_score"] = severity_to_score(events["severity"])
    events["serious_flag"] = bool_to_int(events["is_serious"])

    event_summary = (
        events.groupby("patient_external_id", dropna=False)
        .agg(
            prior_event_count=("event_type", "count"),
            severe_event_count=("severity_score", lambda s: int((s >= 3).sum())),
            serious_event_count=("serious_flag", "sum"),
            avg_event_severity=("severity_score", "mean"),
            events_last_30d=("event_days_ago", lambda s: int((s <= 30).sum())),
            events_last_90d=("event_days_ago", lambda s: int((s <= 90).sum())),
        )
        .reset_index()
    )

    exposure = drug_exposures_df.copy()
    exposure["start_dt"] = safe_to_datetime(exposure["start_date"])
    exposure["is_active_exposure"] = bool_to_int(exposure["is_active"])
    exposure["exposure_days"] = (
        (pd.Timestamp(now) - exposure["start_dt"]).dt.days.clip(lower=0).fillna(0).astype("int64")
    )

    patient_drug = (
        exposure.groupby(["patient_external_id", "drug_name", "drug_class"], dropna=False)
        .agg(
            active_exposure_count=("is_active_exposure", "sum"),
            max_exposure_days=("exposure_days", "max"),
            exposure_record_count=("drug_name", "count"),
            avg_dose_value=("dose_value", lambda s: float(pd.to_numeric(s, errors="coerce").mean() or 0.0)),
        )
        .reset_index()
    )

    features = patient_drug.merge(
        patients,
        how="left",
        left_on="patient_external_id",
        right_on="external_patient_id",
    ).drop(columns=["external_patient_id"], errors="ignore")

    features = features.merge(
        event_summary,
        how="left",
        on="patient_external_id",
    )

    for column in [
        "prior_event_count",
        "severe_event_count",
        "serious_event_count",
        "avg_event_severity",
        "events_last_30d",
        "events_last_90d",
    ]:
        features[column] = features[column].fillna(0)

    condition_drug_signal = (
        features["primary_condition"].fillna("").astype("string").str[:4]
        == features["drug_class"].fillna("").astype("string").str[:4]
    )
    features["condition_drug_interaction_signal"] = bool_to_int(condition_drug_signal)

    features["temporal_safety_burden"] = (
        2 * features["events_last_30d"]
        + 1 * features["events_last_90d"]
        + 2 * features["serious_event_count"]
        + 2 * features["severe_event_count"]
    )

    features["safety_risk_component"] = (
        features["temporal_safety_burden"]
        + features["active_exposure_count"]
        + (features["max_exposure_days"] >= 90).astype("int64")
        + features["condition_drug_interaction_signal"]
    )

    features["target_safety_available"] = 0
    features["target_safety_label"] = pd.NA

    selected_columns = [
        "patient_external_id",
        "drug_name",
        "drug_class",
        "age",
        "sex",
        "primary_condition",
        "active_exposure_count",
        "max_exposure_days",
        "exposure_record_count",
        "avg_dose_value",
        "prior_event_count",
        "severe_event_count",
        "serious_event_count",
        "avg_event_severity",
        "events_last_30d",
        "events_last_90d",
        "condition_drug_interaction_signal",
        "temporal_safety_burden",
        "safety_risk_component",
        "target_safety_available",
        "target_safety_label",
    ]

    return features.reindex(columns=selected_columns).sort_values(
        by=["patient_external_id", "drug_name"], kind="stable"
    ).reset_index(drop=True)
