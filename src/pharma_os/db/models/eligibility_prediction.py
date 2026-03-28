"""Eligibility prediction persistence model."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pharma_os.db.models.base import DomainBase


class EligibilityPrediction(DomainBase):
    """Model inference output for patient-trial eligibility."""

    __tablename__ = "eligibility_predictions"
    __table_args__ = (
        UniqueConstraint(
            "patient_id",
            "trial_id",
            "model_name",
            "model_version",
            "inference_timestamp",
            name="uq_eligibility_prediction_dedup",
        ),
        CheckConstraint(
            "eligibility_probability >= 0 AND eligibility_probability <= 1",
            name="eligibility_probability_range",
        ),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="eligibility_confidence_range"),
        Index("ix_eligibility_predictions_patient_trial", "patient_id", "trial_id"),
        Index("ix_eligibility_predictions_inference_timestamp", "inference_timestamp"),
        Index(
            "ix_eligibility_predictions_model_version_time",
            "model_name",
            "model_version",
            "inference_timestamp",
        ),
    )

    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    trial_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("trials.id", ondelete="CASCADE"),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    predicted_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    eligibility_probability: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    rationale_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    feature_snapshot: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    inference_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    patient = relationship("Patient", back_populates="eligibility_predictions", lazy="joined")
    trial = relationship("Trial", back_populates="eligibility_predictions", lazy="joined")
