"""Safety prediction persistence model."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pharma_os.db.models.base import DomainBase
from pharma_os.db.models.enums import SafetyRiskClass


class SafetyPrediction(DomainBase):
    """Model inference output for patient safety risk."""

    __tablename__ = "safety_predictions"
    __table_args__ = (
        CheckConstraint("risk_score >= 0 AND risk_score <= 1", name="safety_risk_score_range"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="safety_confidence_range"),
        Index("ix_safety_predictions_patient", "patient_id"),
        Index("ix_safety_predictions_inference_timestamp", "inference_timestamp"),
        Index(
            "ix_safety_predictions_model_version_time",
            "model_name",
            "model_version",
            "inference_timestamp",
        ),
        Index(
            "uq_safety_prediction_with_exposure",
            "patient_id",
            "drug_exposure_id",
            "model_name",
            "model_version",
            "inference_timestamp",
            unique=True,
            postgresql_where=text("drug_exposure_id IS NOT NULL"),
        ),
        Index(
            "uq_safety_prediction_without_exposure",
            "patient_id",
            "model_name",
            "model_version",
            "inference_timestamp",
            unique=True,
            postgresql_where=text("drug_exposure_id IS NULL"),
        ),
    )

    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    drug_exposure_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("drug_exposures.id", ondelete="SET NULL"),
        nullable=True,
    )
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_class: Mapped[SafetyRiskClass] = mapped_column(
        Enum(SafetyRiskClass, name="safety_risk_class"),
        nullable=False,
    )
    risk_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    explanation_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    patient = relationship("Patient", back_populates="safety_predictions", lazy="joined")
    drug_exposure = relationship("DrugExposure", back_populates="safety_predictions", lazy="joined")
