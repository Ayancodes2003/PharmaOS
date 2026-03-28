"""Domain validation specifications for structured ingestion pipelines."""

from __future__ import annotations

from pharma_os.pipelines.common.contracts import PipelineDomain
from pharma_os.pipelines.validation.base import ValidationSpec

PATIENTS_VALIDATION_SPEC = ValidationSpec(
    domain=PipelineDomain.PATIENTS,
    required_columns=[
        "external_patient_id",
        "age",
        "sex",
        "primary_condition",
        "enrollment_status",
        "is_active",
    ],
    optional_columns=[
        "race_ethnicity",
        "diagnosis_code",
        "comorbidity_summary",
        "vitals_reference_id",
        "labs_reference_id",
    ],
    critical_columns=["external_patient_id", "age", "sex", "primary_condition"],
    duplicate_key_columns=["external_patient_id"],
    numeric_columns=["age"],
    datetime_columns=[],
    categorical_columns={
        "sex": {"female", "male", "intersex", "other", "unknown"},
        "enrollment_status": {
            "candidate",
            "enrolled",
            "screen_failed",
            "withdrawn",
            "completed",
        },
    },
)

TRIALS_VALIDATION_SPEC = ValidationSpec(
    domain=PipelineDomain.TRIALS,
    required_columns=[
        "trial_code",
        "title",
        "indication",
        "phase",
        "sponsor",
        "status",
    ],
    optional_columns=[
        "inclusion_criteria_ref",
        "exclusion_criteria_ref",
        "recruitment_target",
        "enrolled_count",
        "study_summary",
        "start_date",
        "end_date",
    ],
    critical_columns=["trial_code", "indication", "phase", "status"],
    duplicate_key_columns=["trial_code"],
    numeric_columns=["recruitment_target", "enrolled_count"],
    datetime_columns=["start_date", "end_date"],
    categorical_columns={
        "phase": {
            "phase_1",
            "phase_2",
            "phase_3",
            "phase_4",
            "early_phase",
            "not_applicable",
        },
        "status": {
            "planning",
            "recruiting",
            "active_not_recruiting",
            "completed",
            "terminated",
            "suspended",
        },
    },
)

ADVERSE_EVENTS_VALIDATION_SPEC = ValidationSpec(
    domain=PipelineDomain.ADVERSE_EVENTS,
    required_columns=[
        "patient_external_id",
        "event_type",
        "severity",
        "is_serious",
        "outcome",
        "event_date",
    ],
    optional_columns=["trial_code", "drug_name", "reporter_type", "description"],
    critical_columns=["patient_external_id", "event_type", "severity", "event_date"],
    duplicate_key_columns=["patient_external_id", "event_type", "event_date"],
    numeric_columns=[],
    datetime_columns=["event_date"],
    categorical_columns={
        "severity": {"mild", "moderate", "severe", "life_threatening", "death"},
        "outcome": {"resolved", "resolving", "ongoing", "fatal", "unknown"},
    },
)

DRUG_EXPOSURES_VALIDATION_SPEC = ValidationSpec(
    domain=PipelineDomain.DRUG_EXPOSURES,
    required_columns=["patient_external_id", "drug_name", "start_date", "is_active"],
    optional_columns=[
        "trial_code",
        "drug_class",
        "dose_value",
        "dose_unit",
        "route",
        "frequency",
        "end_date",
        "indication",
    ],
    critical_columns=["patient_external_id", "drug_name", "start_date"],
    duplicate_key_columns=["patient_external_id", "drug_name", "start_date"],
    numeric_columns=["dose_value"],
    datetime_columns=["start_date", "end_date"],
    categorical_columns={},
)
