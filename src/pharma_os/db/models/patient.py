"""Patient domain model."""

from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Enum, Index, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pharma_os.db.models.base import DomainBase, MetadataMixin
from pharma_os.db.models.enums import EnrollmentStatus, PatientSex


class Patient(DomainBase, MetadataMixin):
    """Structured patient profile for eligibility, safety, and analytics workflows."""

    __tablename__ = "patients"
    __table_args__ = (
        CheckConstraint("age >= 0 AND age <= 120", name="age_bounds"),
        Index("ix_patients_condition", "primary_condition"),
        Index("ix_patients_active_enrollment", "is_active", "enrollment_status"),
    )

    external_patient_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    age: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    sex: Mapped[PatientSex] = mapped_column(Enum(PatientSex, name="patient_sex"), nullable=False)
    race_ethnicity: Mapped[str | None] = mapped_column(String(128), nullable=True)
    primary_condition: Mapped[str] = mapped_column(String(255), nullable=False)
    diagnosis_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    comorbidity_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    vitals_reference_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    labs_reference_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    enrollment_status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(EnrollmentStatus, name="patient_enrollment_status"),
        nullable=False,
        default=EnrollmentStatus.CANDIDATE,
        server_default=EnrollmentStatus.CANDIDATE.value,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    adverse_events = relationship("AdverseEvent", back_populates="patient", lazy="selectin")
    drug_exposures = relationship("DrugExposure", back_populates="patient", lazy="selectin")
    eligibility_predictions = relationship(
        "EligibilityPrediction",
        back_populates="patient",
        lazy="selectin",
    )
    safety_predictions = relationship("SafetyPrediction", back_populates="patient", lazy="selectin")
    recruitment_rankings = relationship("RecruitmentRanking", back_populates="patient", lazy="selectin")
