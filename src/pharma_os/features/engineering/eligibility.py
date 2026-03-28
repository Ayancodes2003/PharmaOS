"""Feature generation for patient-trial eligibility prediction."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from pharma_os.features.engineering.common import (
    bool_to_int,
    categorize_age,
    days_since,
    safe_to_datetime,
    severity_to_score,
)


def build_eligibility_features(
    *,
    patients_df: pd.DataFrame,
    trials_df: pd.DataFrame,
    adverse_events_df: pd.DataFrame,
    drug_exposures_df: pd.DataFrame,
) -> pd.DataFrame:
    """Build ML-ready patient-trial eligibility feature rows."""
    now = pd.Timestamp(datetime.now(UTC))

    patients = patients_df.copy()
    patients["age"] = pd.to_numeric(patients["age"], errors="coerce").fillna(0)
    patients["age_bucket"] = categorize_age(patients["age"])
    patients["is_active_patient"] = bool_to_int(patients["is_active"])

    trials = trials_df.copy()
    trials["trial_is_recruiting"] = bool_to_int(trials["status"].astype("string") == "recruiting")
    trials["trial_remaining_slots"] = (
        pd.to_numeric(trials["recruitment_target"], errors="coerce").fillna(0)
        - pd.to_numeric(trials["enrolled_count"], errors="coerce").fillna(0)
    ).clip(lower=0)

    patient_trial = patients.assign(_key=1).merge(trials.assign(_key=1), on="_key", suffixes=("_patient", "_trial")).drop(
        columns=["_key"]
    )

    patient_trial["condition_match"] = bool_to_int(
        patient_trial["primary_condition"].astype("string") == patient_trial["indication"].astype("string")
    )

    patient_trial["diagnosis_indication_match"] = bool_to_int(
        patient_trial["diagnosis_code"].astype("string").str[:3]
        == patient_trial["indication"].astype("string").str[:3]
    )

    patient_trial["comorbidity_count"] = (
        patient_trial["comorbidity_summary"]
        .fillna("")
        .astype("string")
        .str.split("[;,|]", regex=True)
        .map(lambda values: len([value for value in values if value.strip()]))
        .astype("int64")
    )

    ae = adverse_events_df.copy()
    ae["event_dt"] = safe_to_datetime(ae["event_date"])
    ae["severity_score"] = severity_to_score(ae["severity"])
    ae["recent_event_days"] = days_since(now, ae["event_date"])

    ae_patient_summary = (
        ae.groupby("patient_external_id", dropna=False)
        .agg(
            adverse_event_count=("event_type", "count"),
            serious_event_count=("is_serious", lambda s: int(s.fillna(False).astype(bool).sum())),
            avg_event_severity=("severity_score", "mean"),
            recent_30d_event_count=("recent_event_days", lambda s: int((s <= 30).sum())),
        )
        .reset_index()
    )

    exposure = drug_exposures_df.copy()
    exposure["start_dt"] = safe_to_datetime(exposure["start_date"])
    exposure["end_dt"] = safe_to_datetime(exposure["end_date"])
    exposure["active_exposure_flag"] = bool_to_int(exposure["is_active"])

    exposure_patient_summary = (
        exposure.groupby("patient_external_id", dropna=False)
        .agg(
            active_drug_count=("active_exposure_flag", "sum"),
            medication_burden=("drug_name", "nunique"),
            exposure_trial_count=("trial_code", "nunique"),
        )
        .reset_index()
    )

    patient_trial = patient_trial.merge(
        ae_patient_summary,
        how="left",
        left_on="external_patient_id",
        right_on="patient_external_id",
    ).drop(columns=["patient_external_id"], errors="ignore")

    patient_trial = patient_trial.merge(
        exposure_patient_summary,
        how="left",
        left_on="external_patient_id",
        right_on="patient_external_id",
    ).drop(columns=["patient_external_id"], errors="ignore")

    patient_trial["active_exposure_in_trial"] = bool_to_int(
        patient_trial["trial_code"].astype("string").isin(
            exposure.loc[exposure["active_exposure_flag"] == 1, "trial_code"].astype("string")
        )
    )

    fill_defaults: dict[str, object] = {
        "adverse_event_count": 0,
        "serious_event_count": 0,
        "avg_event_severity": 0.0,
        "recent_30d_event_count": 0,
        "active_drug_count": 0,
        "medication_burden": 0,
        "exposure_trial_count": 0,
    }
    for column, value in fill_defaults.items():
        patient_trial[column] = patient_trial[column].fillna(value)

    patient_trial["trial_fit_score_component"] = (
        3 * patient_trial["condition_match"]
        + 2 * patient_trial["diagnosis_indication_match"]
        + 1 * patient_trial["trial_is_recruiting"]
        + 1 * patient_trial["is_active_patient"]
        - 1 * (patient_trial["serious_event_count"] > 0).astype("int64")
        - 1 * (patient_trial["comorbidity_count"] >= 3).astype("int64")
    )

    patient_trial["target_eligibility_available"] = 0
    patient_trial["target_eligibility_label"] = pd.NA

    selected_columns = [
        "external_patient_id",
        "trial_code",
        "age",
        "age_bucket",
        "sex",
        "primary_condition",
        "diagnosis_code",
        "phase",
        "status",
        "condition_match",
        "diagnosis_indication_match",
        "comorbidity_count",
        "medication_burden",
        "active_drug_count",
        "active_exposure_in_trial",
        "adverse_event_count",
        "serious_event_count",
        "avg_event_severity",
        "recent_30d_event_count",
        "trial_is_recruiting",
        "trial_remaining_slots",
        "is_active_patient",
        "trial_fit_score_component",
        "target_eligibility_available",
        "target_eligibility_label",
    ]

    return patient_trial.reindex(columns=selected_columns).sort_values(
        by=["trial_code", "external_patient_id"], kind="stable"
    ).reset_index(drop=True)
