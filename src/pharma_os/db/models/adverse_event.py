"""Adverse event domain model."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pharma_os.db.models.base import DomainBase, MetadataMixin
from pharma_os.db.models.enums import AdverseEventOutcome, AdverseEventSeverity


class AdverseEvent(DomainBase, MetadataMixin):
    """Adverse event records for pharmacovigilance and safety analytics."""

    __tablename__ = "adverse_events"
    __table_args__ = (
        Index("ix_adverse_events_patient_event_date", "patient_id", "event_date"),
        Index("ix_adverse_events_severity_serious", "severity", "is_serious"),
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
    drug_exposure_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("drug_exposures.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    severity: Mapped[AdverseEventSeverity] = mapped_column(
        Enum(AdverseEventSeverity, name="adverse_event_severity"),
        nullable=False,
    )
    is_serious: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    outcome: Mapped[AdverseEventOutcome] = mapped_column(
        Enum(AdverseEventOutcome, name="adverse_event_outcome"),
        nullable=False,
    )
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reporter_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    patient = relationship("Patient", back_populates="adverse_events", lazy="joined")
    trial = relationship("Trial", back_populates="adverse_events", lazy="joined")
    drug_exposure = relationship("DrugExposure", back_populates="adverse_events", lazy="joined")
