"""Inference input and output contracts for Phase 7 serving workflows."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PatientInferenceInput(BaseModel):
    id: UUID | None = None
    external_patient_id: str = Field(min_length=1)
    age: int = Field(ge=0, le=120)
    sex: str = Field(min_length=1)
    primary_condition: str = Field(min_length=1)
    diagnosis_code: str | None = None
    comorbidity_summary: str | None = None
    enrollment_status: str = Field(default="candidate")
    is_active: bool = True


class TrialInferenceInput(BaseModel):
    id: UUID | None = None
    trial_code: str = Field(min_length=1)
    indication: str = Field(min_length=1)
    phase: str = Field(min_length=1)
    status: str = Field(min_length=1)
    recruitment_target: int | None = Field(default=None, ge=0)
    enrolled_count: int = Field(default=0, ge=0)


class AdverseEventInferenceInput(BaseModel):
    patient_external_id: str = Field(min_length=1)
    trial_code: str | None = None
    drug_name: str | None = None
    event_type: str = Field(min_length=1)
    severity: str = Field(min_length=1)
    is_serious: bool = False
    outcome: str = Field(default="unknown")
    event_date: datetime


class DrugExposureInferenceInput(BaseModel):
    id: UUID | None = None
    patient_external_id: str = Field(min_length=1)
    trial_code: str | None = None
    drug_name: str = Field(min_length=1)
    drug_class: str | None = None
    dose_value: float | None = Field(default=None, ge=0)
    route: str | None = None
    frequency: str | None = None
    start_date: datetime
    end_date: datetime | None = None
    is_active: bool = True


class EligibilityInferenceRequest(BaseModel):
    patient: PatientInferenceInput
    trial: TrialInferenceInput
    adverse_events: list[AdverseEventInferenceInput] = Field(default_factory=list)
    drug_exposures: list[DrugExposureInferenceInput] = Field(default_factory=list)
    persist_prediction: bool = False
    trace_id: str | None = None


class SafetyInferenceRequest(BaseModel):
    patient: PatientInferenceInput
    drug_name: str = Field(min_length=1)
    drug_exposure_id: UUID | None = None
    adverse_events: list[AdverseEventInferenceInput] = Field(default_factory=list)
    drug_exposures: list[DrugExposureInferenceInput] = Field(default_factory=list)
    persist_prediction: bool = False
    trace_id: str | None = None


class RecruitmentCandidateInput(BaseModel):
    patient: PatientInferenceInput
    adverse_events: list[AdverseEventInferenceInput] = Field(default_factory=list)
    drug_exposures: list[DrugExposureInferenceInput] = Field(default_factory=list)


class RecruitmentInferenceRequest(BaseModel):
    trial: TrialInferenceInput
    candidates: list[RecruitmentCandidateInput] = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1)
    persist_prediction: bool = False
    trace_id: str | None = None


class InferenceProvenance(BaseModel):
    use_case: str
    model_name: str
    model_version: str
    training_run_id: str
    label_source_type: str
    target_mode: str
    weak_supervision: bool
    feature_schema_columns: list[str]


class EligibilityInferenceResult(BaseModel):
    patient_external_id: str
    trial_code: str
    predicted_eligible: bool
    eligibility_probability: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    persisted_prediction_id: UUID | None = None
    provenance: InferenceProvenance


class SafetyInferenceResult(BaseModel):
    patient_external_id: str
    drug_name: str
    risk_class: str
    risk_score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    persisted_prediction_id: UUID | None = None
    provenance: InferenceProvenance


class RecruitmentRankingItem(BaseModel):
    patient_external_id: str
    ranking_score: float = Field(ge=0, le=1)
    urgency_score: float = Field(ge=0, le=1)
    fit_score: float = Field(ge=0, le=1)
    exclusion_risk_score: float = Field(ge=0, le=1)
    rank_position: int = Field(ge=1)
    persisted_ranking_id: UUID | None = None


class RecruitmentInferenceResult(BaseModel):
    trial_code: str
    ranking_run_id: UUID | None = None
    items: list[RecruitmentRankingItem]
    provenance: InferenceProvenance


class MultiUseCaseInferenceSummary(BaseModel):
    trace_id: str | None = None
    eligibility: EligibilityInferenceResult | None = None
    safety: SafetyInferenceResult | None = None
    recruitment: RecruitmentInferenceResult | None = None
