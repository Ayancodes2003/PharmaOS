"""Drug exposure domain model."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pharma_os.db.models.base import DomainBase, MetadataMixin


class DrugExposure(DomainBase, MetadataMixin):
    """Medication exposure records linked to patient and optional trial context."""

    __tablename__ = "drug_exposures"
    __table_args__ = (
        Index("ix_drug_exposures_patient_active", "patient_id", "is_active"),
        Index("ix_drug_exposures_drug_name", "drug_name"),
    )

    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    trial_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("trials.id", ondelete="SET NULL"),
        nullable=True,
    )
    drug_name: Mapped[str] = mapped_column(String(255), nullable=False)
    drug_class: Mapped[str | None] = mapped_column(String(128), nullable=True)
    dose_value: Mapped[float | None] = mapped_column(Numeric(10, 3), nullable=True)
    dose_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    route: Mapped[str | None] = mapped_column(String(64), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(64), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    indication: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    patient = relationship("Patient", back_populates="drug_exposures", lazy="joined")
    trial = relationship("Trial", back_populates="drug_exposures", lazy="joined")
    adverse_events = relationship("AdverseEvent", back_populates="drug_exposure", lazy="selectin")
    safety_predictions = relationship("SafetyPrediction", back_populates="drug_exposure", lazy="selectin")
