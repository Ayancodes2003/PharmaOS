"""Recruitment ranking DTO contracts."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from pharma_os.db.schemas.common import DTOBase, TimestampedReadDTO


class RecruitmentRankingCreateDTO(DTOBase):
    patient_id: UUID
    trial_id: UUID
    ranking_run_id: UUID | None = None
    ranking_score: float = Field(ge=0, le=1)
    urgency_score: float = Field(ge=0, le=1)
    fit_score: float = Field(ge=0, le=1)
    exclusion_risk_score: float = Field(ge=0, le=1)
    rank_position: int = Field(ge=1)
    model_version: str = Field(min_length=1, max_length=64)
    generated_at: datetime


class RecruitmentRankingReadDTO(TimestampedReadDTO):
    patient_id: UUID
    trial_id: UUID
    ranking_run_id: UUID
    ranking_score: float
    urgency_score: float
    fit_score: float
    exclusion_risk_score: float
    rank_position: int
    model_version: str
    generated_at: datetime


class RecruitmentRankingFilterDTO(DTOBase):
    patient_id: UUID | None = None
    trial_id: UUID | None = None
    ranking_run_id: UUID | None = None
    generated_from: datetime | None = None
    generated_to: datetime | None = None
