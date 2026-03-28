"""Trial DTO contracts."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import Field

from pharma_os.db.models.enums import TrialPhase, TrialStatus
from pharma_os.db.schemas.common import DTOBase, TimestampedReadDTO


class TrialCreateDTO(DTOBase):
    trial_code: str = Field(min_length=1, max_length=32)
    title: str = Field(min_length=1, max_length=300)
    indication: str = Field(min_length=1, max_length=255)
    phase: TrialPhase
    sponsor: str = Field(min_length=1, max_length=255)
    status: TrialStatus
    inclusion_criteria_ref: str | None = Field(default=None, max_length=128)
    exclusion_criteria_ref: str | None = Field(default=None, max_length=128)
    recruitment_target: int | None = Field(default=None, ge=0)
    enrolled_count: int = Field(default=0, ge=0)
    study_summary: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class TrialUpdateDTO(DTOBase):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    indication: str | None = Field(default=None, min_length=1, max_length=255)
    phase: TrialPhase | None = None
    sponsor: str | None = Field(default=None, min_length=1, max_length=255)
    status: TrialStatus | None = None
    inclusion_criteria_ref: str | None = Field(default=None, max_length=128)
    exclusion_criteria_ref: str | None = Field(default=None, max_length=128)
    recruitment_target: int | None = Field(default=None, ge=0)
    enrolled_count: int | None = Field(default=None, ge=0)
    study_summary: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    metadata_json: dict[str, object] | None = None


class TrialReadDTO(TimestampedReadDTO):
    trial_code: str
    title: str
    indication: str
    phase: TrialPhase
    sponsor: str
    status: TrialStatus
    inclusion_criteria_ref: str | None
    exclusion_criteria_ref: str | None
    recruitment_target: int | None
    enrolled_count: int
    study_summary: str | None
    start_date: date | None
    end_date: date | None
    metadata_json: dict[str, object]


class TrialFilterDTO(DTOBase):
    ids: list[UUID] | None = None
    indication: str | None = None
    sponsor: str | None = None
    phase: TrialPhase | None = None
    status: TrialStatus | None = None
