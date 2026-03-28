"""Prediction DTO contracts for eligibility and safety model persistence."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from pharma_os.db.models.enums import SafetyRiskClass
from pharma_os.db.schemas.common import DTOBase, TimestampedReadDTO


class EligibilityPredictionCreateDTO(DTOBase):
    patient_id: UUID
    trial_id: UUID
    model_name: str = Field(min_length=1, max_length=128)
    model_version: str = Field(min_length=1, max_length=64)
    predicted_eligible: bool
    eligibility_probability: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    rationale_summary: str | None = None
    feature_snapshot: dict[str, object] = Field(default_factory=dict)
    inference_timestamp: datetime


class EligibilityPredictionReadDTO(TimestampedReadDTO):
    patient_id: UUID
    trial_id: UUID
    model_name: str
    model_version: str
    predicted_eligible: bool
    eligibility_probability: float
    confidence: float
    rationale_summary: str | None
    feature_snapshot: dict[str, object]
    inference_timestamp: datetime


class SafetyPredictionCreateDTO(DTOBase):
    patient_id: UUID
    drug_exposure_id: UUID | None = None
    model_name: str = Field(min_length=1, max_length=128)
    model_version: str = Field(min_length=1, max_length=64)
    risk_class: SafetyRiskClass
    risk_score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    explanation_summary: str | None = None
    feature_snapshot: dict[str, object] = Field(default_factory=dict)
    inference_timestamp: datetime


class SafetyPredictionReadDTO(TimestampedReadDTO):
    patient_id: UUID
    drug_exposure_id: UUID | None
    model_name: str
    model_version: str
    risk_class: SafetyRiskClass
    risk_score: float
    confidence: float
    explanation_summary: str | None
    feature_snapshot: dict[str, object]
    inference_timestamp: datetime


class PredictionFilterDTO(DTOBase):
    patient_id: UUID | None = None
    trial_id: UUID | None = None
    drug_exposure_id: UUID | None = None
    model_name: str | None = None
    model_version: str | None = None
    inferred_from: datetime | None = None
    inferred_to: datetime | None = None
