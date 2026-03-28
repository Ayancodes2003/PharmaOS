"""Adverse event DTO contracts."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from pharma_os.db.models.enums import AdverseEventOutcome, AdverseEventSeverity
from pharma_os.db.schemas.common import DTOBase, TimestampedReadDTO


class AdverseEventCreateDTO(DTOBase):
    patient_id: UUID
    trial_id: UUID | None = None
    drug_exposure_id: UUID | None = None
    event_type: str = Field(min_length=1, max_length=128)
    severity: AdverseEventSeverity
    is_serious: bool = False
    outcome: AdverseEventOutcome
    event_date: datetime
    reporter_type: str | None = Field(default=None, max_length=64)
    description: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class AdverseEventUpdateDTO(DTOBase):
    severity: AdverseEventSeverity | None = None
    is_serious: bool | None = None
    outcome: AdverseEventOutcome | None = None
    reporter_type: str | None = Field(default=None, max_length=64)
    description: str | None = None
    metadata_json: dict[str, object] | None = None


class AdverseEventReadDTO(TimestampedReadDTO):
    patient_id: UUID
    trial_id: UUID | None
    drug_exposure_id: UUID | None
    event_type: str
    severity: AdverseEventSeverity
    is_serious: bool
    outcome: AdverseEventOutcome
    event_date: datetime
    reporter_type: str | None
    description: str | None
    metadata_json: dict[str, object]


class AdverseEventFilterDTO(DTOBase):
    patient_id: UUID | None = None
    trial_id: UUID | None = None
    is_serious: bool | None = None
    severity: AdverseEventSeverity | None = None
    event_date_from: datetime | None = None
    event_date_to: datetime | None = None
