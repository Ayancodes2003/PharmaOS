"""Patient DTO contracts."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from pharma_os.db.models.enums import EnrollmentStatus, PatientSex
from pharma_os.db.schemas.common import DTOBase, TimestampedReadDTO


class PatientCreateDTO(DTOBase):
    external_patient_id: str = Field(min_length=1, max_length=64)
    age: int = Field(ge=0, le=120)
    sex: PatientSex
    race_ethnicity: str | None = Field(default=None, max_length=128)
    primary_condition: str = Field(min_length=1, max_length=255)
    diagnosis_code: str | None = Field(default=None, max_length=32)
    comorbidity_summary: str | None = None
    vitals_reference_id: str | None = Field(default=None, max_length=128)
    labs_reference_id: str | None = Field(default=None, max_length=128)
    enrollment_status: EnrollmentStatus = EnrollmentStatus.CANDIDATE
    is_active: bool = True
    metadata_json: dict[str, object] = Field(default_factory=dict)


class PatientUpdateDTO(DTOBase):
    age: int | None = Field(default=None, ge=0, le=120)
    race_ethnicity: str | None = Field(default=None, max_length=128)
    primary_condition: str | None = Field(default=None, min_length=1, max_length=255)
    diagnosis_code: str | None = Field(default=None, max_length=32)
    comorbidity_summary: str | None = None
    vitals_reference_id: str | None = Field(default=None, max_length=128)
    labs_reference_id: str | None = Field(default=None, max_length=128)
    enrollment_status: EnrollmentStatus | None = None
    is_active: bool | None = None
    metadata_json: dict[str, object] | None = None


class PatientReadDTO(TimestampedReadDTO):
    external_patient_id: str
    age: int
    sex: PatientSex
    race_ethnicity: str | None
    primary_condition: str
    diagnosis_code: str | None
    comorbidity_summary: str | None
    vitals_reference_id: str | None
    labs_reference_id: str | None
    enrollment_status: EnrollmentStatus
    is_active: bool
    metadata_json: dict[str, object]


class PatientFilterDTO(DTOBase):
    ids: list[UUID] | None = None
    primary_condition: str | None = None
    diagnosis_code: str | None = None
    is_active: bool | None = None
    enrollment_status: EnrollmentStatus | None = None
    min_age: int | None = Field(default=None, ge=0, le=120)
    max_age: int | None = Field(default=None, ge=0, le=120)
