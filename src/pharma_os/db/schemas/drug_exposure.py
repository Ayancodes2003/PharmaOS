"""Drug exposure DTO contracts."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import Field

from pharma_os.db.schemas.common import DTOBase, TimestampedReadDTO


class DrugExposureCreateDTO(DTOBase):
    patient_id: UUID
    trial_id: UUID | None = None
    drug_name: str = Field(min_length=1, max_length=255)
    drug_class: str | None = Field(default=None, max_length=128)
    dose_value: float | None = Field(default=None, ge=0)
    dose_unit: str | None = Field(default=None, max_length=32)
    route: str | None = Field(default=None, max_length=64)
    frequency: str | None = Field(default=None, max_length=64)
    start_date: date
    end_date: date | None = None
    indication: str | None = Field(default=None, max_length=255)
    is_active: bool = True
    metadata_json: dict[str, object] = Field(default_factory=dict)


class DrugExposureUpdateDTO(DTOBase):
    dose_value: float | None = Field(default=None, ge=0)
    dose_unit: str | None = Field(default=None, max_length=32)
    route: str | None = Field(default=None, max_length=64)
    frequency: str | None = Field(default=None, max_length=64)
    end_date: date | None = None
    indication: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    metadata_json: dict[str, object] | None = None


class DrugExposureReadDTO(TimestampedReadDTO):
    patient_id: UUID
    trial_id: UUID | None
    drug_name: str
    drug_class: str | None
    dose_value: float | None
    dose_unit: str | None
    route: str | None
    frequency: str | None
    start_date: date
    end_date: date | None
    indication: str | None
    is_active: bool
    metadata_json: dict[str, object]


class DrugExposureFilterDTO(DTOBase):
    patient_id: UUID | None = None
    trial_id: UUID | None = None
    drug_name: str | None = None
    is_active: bool | None = None
