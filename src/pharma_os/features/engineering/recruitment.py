"""Feature generation for recruitment prioritization and ranking."""

from __future__ import annotations

import pandas as pd

from pharma_os.features.engineering.common import bool_to_int, severity_to_score


def build_recruitment_features(
    *,
    patients_df: pd.DataFrame,
    trials_df: pd.DataFrame,
    adverse_events_df: pd.DataFrame,
    drug_exposures_df: pd.DataFrame,
) -> pd.DataFrame:
    """Build explainable patient-trial ranking features for recruitment operations."""
    patients = patients_df.copy()
    trials = trials_df.copy()

    candidate_pairs = patients.assign(_key=1).merge(
        trials.assign(_key=1),
        on="_key",
        suffixes=("_patient", "_trial"),
    ).drop(columns=["_key"])

    candidate_pairs["condition_fit"] = bool_to_int(
        candidate_pairs["primary_condition"].astype("string") == candidate_pairs["indication"].astype("string")
    )
    candidate_pairs["trial_recruiting_flag"] = bool_to_int(candidate_pairs["status"].astype("string") == "recruiting")

    candidate_pairs["remaining_slots"] = (
        pd.to_numeric(candidate_pairs["recruitment_target"], errors="coerce").fillna(0)
        - pd.to_numeric(candidate_pairs["enrolled_count"], errors="coerce").fillna(0)
    ).clip(lower=0)

    candidate_pairs["enrollment_ready_flag"] = bool_to_int(
        candidate_pairs["enrollment_status"].astype("string").isin(["candidate", "enrolled"])
    )

    candidate_pairs["urgency_proxy"] = (
        candidate_pairs["trial_recruiting_flag"]
        + (candidate_pairs["remaining_slots"] <= 5).astype("int64")
        + (candidate_pairs["remaining_slots"] <= 2).astype("int64")
    )

    ae = adverse_events_df.copy()
    ae["severity_score"] = severity_to_score(ae["severity"])
    ae_summary = (
        ae.groupby("patient_external_id", dropna=False)
        .agg(
            serious_event_count=("is_serious", lambda s: int(s.fillna(False).astype(bool).sum())),
            severe_event_count=("severity_score", lambda s: int((s >= 3).sum())),
        )
        .reset_index()
    )

    exposure_summary = (
        drug_exposures_df.groupby("patient_external_id", dropna=False)
        .agg(
            active_exposure_count=("is_active", lambda s: int(s.fillna(False).astype(bool).sum())),
            medication_burden=("drug_name", "nunique"),
        )
        .reset_index()
    )

    features = candidate_pairs.merge(
        ae_summary,
        how="left",
        left_on="external_patient_id",
        right_on="patient_external_id",
    ).drop(columns=["patient_external_id"], errors="ignore")

    features = features.merge(
        exposure_summary,
        how="left",
        left_on="external_patient_id",
        right_on="patient_external_id",
    ).drop(columns=["patient_external_id"], errors="ignore")

    features["serious_event_count"] = features["serious_event_count"].fillna(0)
    features["severe_event_count"] = features["severe_event_count"].fillna(0)
    features["active_exposure_count"] = features["active_exposure_count"].fillna(0)
    features["medication_burden"] = features["medication_burden"].fillna(0)

    features["exclusion_risk_signal"] = (
        (features["serious_event_count"] > 0).astype("int64")
        + (features["severe_event_count"] > 1).astype("int64")
        + (features["medication_burden"] >= 5).astype("int64")
    )

    features["trial_readiness_indicator"] = (
        features["condition_fit"]
        + features["enrollment_ready_flag"]
        + features["trial_recruiting_flag"]
        - features["exclusion_risk_signal"]
    )

    features["ranking_score_component"] = (
        4 * features["condition_fit"]
        + 2 * features["urgency_proxy"]
        + 2 * features["enrollment_ready_flag"]
        - 2 * features["exclusion_risk_signal"]
        - (features["active_exposure_count"] >= 3).astype("int64")
    )

    selected_columns = [
        "external_patient_id",
        "trial_code",
        "status",
        "phase",
        "condition_fit",
        "urgency_proxy",
        "enrollment_ready_flag",
        "remaining_slots",
        "active_exposure_count",
        "medication_burden",
        "serious_event_count",
        "severe_event_count",
        "exclusion_risk_signal",
        "trial_readiness_indicator",
        "ranking_score_component",
    ]

    return features.reindex(columns=selected_columns).sort_values(
        by=["trial_code", "ranking_score_component"],
        ascending=[True, False],
        kind="stable",
    ).reset_index(drop=True)
