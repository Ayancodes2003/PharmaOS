"""Trial domain model."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Enum, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pharma_os.db.models.base import DomainBase, MetadataMixin
from pharma_os.db.models.enums import TrialPhase, TrialStatus


class Trial(DomainBase, MetadataMixin):
    """Clinical trial metadata and recruitment state."""

    __tablename__ = "trials"
    __table_args__ = (
        Index("ix_trials_indication", "indication"),
        Index("ix_trials_status_phase", "status", "phase"),
    )

    trial_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    indication: Mapped[str] = mapped_column(String(255), nullable=False)
    phase: Mapped[TrialPhase] = mapped_column(Enum(TrialPhase, name="trial_phase"), nullable=False)
    sponsor: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[TrialStatus] = mapped_column(Enum(TrialStatus, name="trial_status"), nullable=False)
    inclusion_criteria_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    exclusion_criteria_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    recruitment_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enrolled_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    study_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    adverse_events = relationship("AdverseEvent", back_populates="trial", lazy="selectin")
    drug_exposures = relationship("DrugExposure", back_populates="trial", lazy="selectin")
    eligibility_predictions = relationship(
        "EligibilityPrediction",
        back_populates="trial",
        lazy="selectin",
    )
    recruitment_rankings = relationship("RecruitmentRanking", back_populates="trial", lazy="selectin")
