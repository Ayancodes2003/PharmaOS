"""Domain-aware preprocessing routines for structured datasets."""

from __future__ import annotations

import pandas as pd

from pharma_os.pipelines.common.normalization import (
    coerce_date_string,
    coerce_datetime,
    normalize_boolean_series,
    normalize_enum_values,
    strip_text_columns,
)


def _series(df: pd.DataFrame, column: str, *, default: object = pd.NA) -> pd.Series:
    """Return an existing column as Series, or a typed default series when missing."""
    if column in df.columns:
        return df[column]
    return pd.Series([default] * len(df), index=df.index)


def preprocess_patients(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize patient dataset into canonical contract."""
    df = df.rename(columns={"patient_id": "external_patient_id", "condition": "primary_condition"}).copy()
    text_columns = [
        "external_patient_id",
        "primary_condition",
        "diagnosis_code",
        "race_ethnicity",
        "comorbidity_summary",
        "vitals_reference_id",
        "labs_reference_id",
    ]
    df = strip_text_columns(df, text_columns)

    df["age"] = pd.to_numeric(_series(df, "age"), errors="coerce").clip(lower=0, upper=120)
    df["age"] = df["age"].round(0).astype("Int64")

    sex_map = {
        "f": "female",
        "female": "female",
        "m": "male",
        "male": "male",
        "intersex": "intersex",
        "other": "other",
        "unknown": "unknown",
    }
    df["sex"] = normalize_enum_values(_series(df, "sex"), sex_map, default="unknown")

    enrollment_map = {
        "candidate": "candidate",
        "screening": "candidate",
        "enrolled": "enrolled",
        "screen_failed": "screen_failed",
        "withdrawn": "withdrawn",
        "completed": "completed",
    }
    df["enrollment_status"] = normalize_enum_values(
        _series(df, "enrollment_status"),
        enrollment_map,
        default="candidate",
    )

    df["is_active"] = normalize_boolean_series(_series(df, "is_active", default=True))
    df["is_active"] = df["is_active"].fillna(True)

    df = df.drop_duplicates(subset=["external_patient_id"], keep="last")

    canonical_columns = [
        "external_patient_id",
        "age",
        "sex",
        "race_ethnicity",
        "primary_condition",
        "diagnosis_code",
        "comorbidity_summary",
        "vitals_reference_id",
        "labs_reference_id",
        "enrollment_status",
        "is_active",
    ]
    return df.reindex(columns=canonical_columns)


def preprocess_trials(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize trial dataset into canonical contract."""
    df = df.rename(columns={"condition": "indication", "trial_status": "status"}).copy()

    text_columns = [
        "trial_code",
        "title",
        "indication",
        "phase",
        "sponsor",
        "status",
        "inclusion_criteria_ref",
        "exclusion_criteria_ref",
        "study_summary",
    ]
    df = strip_text_columns(df, text_columns)

    phase_map = {
        "1": "phase_1",
        "phase_1": "phase_1",
        "phase i": "phase_1",
        "2": "phase_2",
        "phase_2": "phase_2",
        "phase ii": "phase_2",
        "3": "phase_3",
        "phase_3": "phase_3",
        "phase iii": "phase_3",
        "4": "phase_4",
        "phase_4": "phase_4",
        "phase iv": "phase_4",
        "early_phase": "early_phase",
        "not_applicable": "not_applicable",
    }
    df["phase"] = normalize_enum_values(_series(df, "phase"), phase_map, default="not_applicable")

    status_map = {
        "planning": "planning",
        "recruiting": "recruiting",
        "active_not_recruiting": "active_not_recruiting",
        "completed": "completed",
        "terminated": "terminated",
        "suspended": "suspended",
    }
    df["status"] = normalize_enum_values(_series(df, "status"), status_map, default="planning")

    df["recruitment_target"] = pd.to_numeric(_series(df, "recruitment_target"), errors="coerce").astype("Int64")
    df["enrolled_count"] = (
        pd.to_numeric(_series(df, "enrolled_count"), errors="coerce").fillna(0).clip(lower=0).astype("Int64")
    )

    df["start_date"] = coerce_date_string(_series(df, "start_date"))
    df["end_date"] = coerce_date_string(_series(df, "end_date"))

    df = df.drop_duplicates(subset=["trial_code"], keep="last")

    canonical_columns = [
        "trial_code",
        "title",
        "indication",
        "phase",
        "sponsor",
        "status",
        "inclusion_criteria_ref",
        "exclusion_criteria_ref",
        "recruitment_target",
        "enrolled_count",
        "study_summary",
        "start_date",
        "end_date",
    ]
    return df.reindex(columns=canonical_columns)


def preprocess_adverse_events(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize adverse event dataset."""
    df = df.rename(columns={"patient_id": "patient_external_id", "type": "event_type"}).copy()

    text_columns = [
        "patient_external_id",
        "trial_code",
        "drug_name",
        "event_type",
        "severity",
        "outcome",
        "reporter_type",
        "description",
    ]
    df = strip_text_columns(df, text_columns)

    severity_map = {
        "mild": "mild",
        "moderate": "moderate",
        "severe": "severe",
        "life threatening": "life_threatening",
        "life_threatening": "life_threatening",
        "death": "death",
    }
    df["severity"] = normalize_enum_values(_series(df, "severity"), severity_map, default="moderate")

    outcome_map = {
        "resolved": "resolved",
        "resolving": "resolving",
        "ongoing": "ongoing",
        "fatal": "fatal",
        "unknown": "unknown",
    }
    df["outcome"] = normalize_enum_values(_series(df, "outcome"), outcome_map, default="unknown")

    df["is_serious"] = normalize_boolean_series(_series(df, "is_serious", default=False))
    df["is_serious"] = df["is_serious"].fillna(False)

    parsed_event_date = coerce_datetime(_series(df, "event_date"), utc=True)
    df["event_date"] = parsed_event_date.dt.strftime("%Y-%m-%dT%H:%M:%SZ").astype("string")

    df = df.drop_duplicates(subset=["patient_external_id", "event_type", "event_date"], keep="last")

    canonical_columns = [
        "patient_external_id",
        "trial_code",
        "drug_name",
        "event_type",
        "severity",
        "is_serious",
        "outcome",
        "event_date",
        "reporter_type",
        "description",
    ]
    return df.reindex(columns=canonical_columns)


def preprocess_drug_exposures(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize drug exposure dataset."""
    df = df.rename(columns={"patient_id": "patient_external_id", "drug": "drug_name"}).copy()

    text_columns = [
        "patient_external_id",
        "trial_code",
        "drug_name",
        "drug_class",
        "dose_unit",
        "route",
        "frequency",
        "indication",
    ]
    df = strip_text_columns(df, text_columns)

    df["dose_value"] = pd.to_numeric(_series(df, "dose_value"), errors="coerce")
    df["dose_value"] = df["dose_value"].where(df["dose_value"].isna() | (df["dose_value"] >= 0), pd.NA)

    df["start_date"] = coerce_date_string(_series(df, "start_date"))
    df["end_date"] = coerce_date_string(_series(df, "end_date"))

    df["is_active"] = normalize_boolean_series(_series(df, "is_active", default=True))
    df["is_active"] = df["is_active"].fillna(True)

    df = df.drop_duplicates(subset=["patient_external_id", "drug_name", "start_date"], keep="last")

    canonical_columns = [
        "patient_external_id",
        "trial_code",
        "drug_name",
        "drug_class",
        "dose_value",
        "dose_unit",
        "route",
        "frequency",
        "start_date",
        "end_date",
        "indication",
        "is_active",
    ]
    return df.reindex(columns=canonical_columns)
