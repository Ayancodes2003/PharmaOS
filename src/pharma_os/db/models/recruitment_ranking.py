"""Recruitment ranking persistence model."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pharma_os.db.models.base import DomainBase


class RecruitmentRanking(DomainBase):
    """Patient ranking output per trial recruitment cycle."""

    __tablename__ = "recruitment_rankings"
    __table_args__ = (
        UniqueConstraint("trial_id", "ranking_run_id", "rank_position", name="uq_trial_run_rank_position"),
        UniqueConstraint("trial_id", "ranking_run_id", "patient_id", name="uq_trial_run_patient"),
        CheckConstraint("ranking_score >= 0 AND ranking_score <= 1", name="ranking_score_range"),
        CheckConstraint("urgency_score >= 0 AND urgency_score <= 1", name="urgency_score_range"),
        CheckConstraint("fit_score >= 0 AND fit_score <= 1", name="fit_score_range"),
        CheckConstraint(
            "exclusion_risk_score >= 0 AND exclusion_risk_score <= 1",
            name="exclusion_risk_score_range",
        ),
        CheckConstraint("rank_position >= 1", name="rank_position_positive"),
        Index("ix_recruitment_rankings_trial_score", "trial_id", "ranking_score"),
        Index("ix_recruitment_rankings_trial_run", "trial_id", "ranking_run_id"),
        Index("ix_recruitment_rankings_trial_generated_rank", "trial_id", "generated_at", "rank_position"),
        Index("ix_recruitment_rankings_trial_patient", "trial_id", "patient_id"),
        Index("ix_recruitment_rankings_generated_at", "generated_at"),
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
    ranking_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        default=uuid4,
    )
    ranking_score: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    urgency_score: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    fit_score: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    exclusion_risk_score: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    rank_position: Mapped[int] = mapped_column(Integer, nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    patient = relationship("Patient", back_populates="recruitment_rankings", lazy="joined")
    trial = relationship("Trial", back_populates="recruitment_rankings", lazy="joined")
