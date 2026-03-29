"""Inference-safe feature preparation utilities aligned to Phase 5 engineering logic."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd

from pharma_os.features.engineering import (
    build_eligibility_features,
    build_recruitment_features,
    build_safety_features,
)
from pharma_os.ml.inference.contracts import (
    AdverseEventInferenceInput,
    DrugExposureInferenceInput,
    EligibilityInferenceRequest,
    RecruitmentInferenceRequest,
    SafetyInferenceRequest,
)
from pharma_os.ml.registry import LoadedModelBundle


def prepare_eligibility_features_for_inference(
    *,
    request: EligibilityInferenceRequest,
    bundle: LoadedModelBundle,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Prepare single-row eligibility features in training-schema order."""
    patients_df = _patients_frame([request.patient.model_dump()])
    trials_df = _trials_frame([request.trial.model_dump()])

    adverse_df = _adverse_events_frame(
        [item.model_dump() for item in request.adverse_events],
        default_patient_external_id=request.patient.external_patient_id,
        default_trial_code=request.trial.trial_code,
    )
    exposure_df = _drug_exposures_frame(
        [item.model_dump() for item in request.drug_exposures],
        default_patient_external_id=request.patient.external_patient_id,
        default_trial_code=request.trial.trial_code,
    )

    engineered = build_eligibility_features(
        patients_df=patients_df,
        trials_df=trials_df,
        adverse_events_df=adverse_df,
        drug_exposures_df=exposure_df,
    )

    row = engineered.iloc[[0]].copy()
    feature_df = _align_to_bundle_columns(row, bundle.feature_columns)

    snapshot = {
        "engineered_feature_row": row.iloc[0].to_dict(),
        "used_feature_columns": bundle.feature_columns,
    }
    return feature_df, snapshot


def prepare_safety_features_for_inference(
    *,
    request: SafetyInferenceRequest,
    bundle: LoadedModelBundle,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Prepare single-row safety features in training-schema order."""
    patients_df = _patients_frame([request.patient.model_dump()])

    adverse_df = _adverse_events_frame(
        [item.model_dump() for item in request.adverse_events],
        default_patient_external_id=request.patient.external_patient_id,
        default_trial_code=None,
    )

    exposure_payloads = [item.model_dump() for item in request.drug_exposures]
    if request.drug_name and not any(item["drug_name"] == request.drug_name for item in exposure_payloads):
        exposure_payloads.append(
            DrugExposureInferenceInput(
                id=request.drug_exposure_id,
                patient_external_id=request.patient.external_patient_id,
                drug_name=request.drug_name,
                start_date=datetime.now(UTC),
                is_active=True,
            ).model_dump()
        )

    exposure_df = _drug_exposures_frame(
        exposure_payloads,
        default_patient_external_id=request.patient.external_patient_id,
        default_trial_code=None,
    )

    engineered = build_safety_features(
        patients_df=patients_df,
        adverse_events_df=adverse_df,
        drug_exposures_df=exposure_df,
    )

    filtered = engineered[engineered["drug_name"].astype("string") == request.drug_name]
    row = filtered.iloc[[0]] if not filtered.empty else engineered.iloc[[0]]

    feature_df = _align_to_bundle_columns(row, bundle.feature_columns)
    snapshot = {
        "engineered_feature_row": row.iloc[0].to_dict(),
        "used_feature_columns": bundle.feature_columns,
    }
    return feature_df, snapshot


def prepare_recruitment_features_for_inference(
    *,
    request: RecruitmentInferenceRequest,
    bundle: LoadedModelBundle,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Prepare recruitment ranking feature rows for all candidate patients."""
    patients_df = _patients_frame([item.patient.model_dump() for item in request.candidates])
    trials_df = _trials_frame([request.trial.model_dump()])

    adverse_payloads: list[dict[str, Any]] = []
    exposure_payloads: list[dict[str, Any]] = []
    for candidate in request.candidates:
        adverse_payloads.extend(item.model_dump() for item in candidate.adverse_events)
        exposure_payloads.extend(item.model_dump() for item in candidate.drug_exposures)

    adverse_df = _adverse_events_frame(
        adverse_payloads,
        default_patient_external_id=None,
        default_trial_code=request.trial.trial_code,
    )
    exposure_df = _drug_exposures_frame(
        exposure_payloads,
        default_patient_external_id=None,
        default_trial_code=request.trial.trial_code,
    )

    engineered = build_recruitment_features(
        patients_df=patients_df,
        trials_df=trials_df,
        adverse_events_df=adverse_df,
        drug_exposures_df=exposure_df,
    )

    feature_df = _align_to_bundle_columns(engineered, bundle.feature_columns)
    snapshots = [row for row in engineered.to_dict(orient="records")]
    return feature_df, snapshots


def _align_to_bundle_columns(df: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    """Align inference features to trained model schema with safe defaults."""
    aligned = df.copy()
    for column in feature_columns:
        if column not in aligned.columns:
            aligned[column] = pd.NA
    return aligned.reindex(columns=feature_columns)


def _patients_frame(payloads: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for payload in payloads:
        rows.append(
            {
                "external_patient_id": payload["external_patient_id"],
                "age": payload["age"],
                "sex": str(payload["sex"]).lower(),
                "primary_condition": payload["primary_condition"],
                "diagnosis_code": payload.get("diagnosis_code"),
                "comorbidity_summary": payload.get("comorbidity_summary"),
                "enrollment_status": payload.get("enrollment_status", "candidate"),
                "is_active": payload.get("is_active", True),
            }
        )
    return pd.DataFrame(rows)


def _trials_frame(payloads: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for payload in payloads:
        rows.append(
            {
                "trial_code": payload["trial_code"],
                "indication": payload["indication"],
                "phase": payload["phase"],
                "status": payload["status"],
                "recruitment_target": payload.get("recruitment_target", 0),
                "enrolled_count": payload.get("enrolled_count", 0),
            }
        )
    return pd.DataFrame(rows)


def _adverse_events_frame(
    payloads: list[dict[str, Any]],
    *,
    default_patient_external_id: str | None,
    default_trial_code: str | None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for payload in payloads:
        rows.append(
            {
                "patient_external_id": payload.get("patient_external_id") or default_patient_external_id,
                "trial_code": payload.get("trial_code") or default_trial_code,
                "drug_name": payload.get("drug_name"),
                "event_type": payload.get("event_type", "unknown_event"),
                "severity": str(payload.get("severity", "moderate")).lower(),
                "is_serious": bool(payload.get("is_serious", False)),
                "outcome": str(payload.get("outcome", "unknown")).lower(),
                "event_date": _to_iso_timestamp(payload.get("event_date")),
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=[
                "patient_external_id",
                "trial_code",
                "drug_name",
                "event_type",
                "severity",
                "is_serious",
                "outcome",
                "event_date",
            ]
        )
    return pd.DataFrame(rows)


def _drug_exposures_frame(
    payloads: list[dict[str, Any]],
    *,
    default_patient_external_id: str | None,
    default_trial_code: str | None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for payload in payloads:
        rows.append(
            {
                "patient_external_id": payload.get("patient_external_id") or default_patient_external_id,
                "trial_code": payload.get("trial_code") or default_trial_code,
                "drug_name": payload["drug_name"],
                "drug_class": payload.get("drug_class"),
                "dose_value": payload.get("dose_value"),
                "route": payload.get("route"),
                "frequency": payload.get("frequency"),
                "start_date": _to_date_string(payload.get("start_date")),
                "end_date": _to_date_string(payload.get("end_date")),
                "is_active": bool(payload.get("is_active", True)),
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=[
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
            ]
        )
    return pd.DataFrame(rows)


def _to_iso_timestamp(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    if value is None:
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")


def _to_date_string(value: Any) -> str | None:
    if value is None:
        return None
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return None
    return parsed.strftime("%Y-%m-%d")
