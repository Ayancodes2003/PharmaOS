"""Prediction repository implementations for eligibility and safety outputs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, select

from pharma_os.db.models.eligibility_prediction import EligibilityPrediction
from pharma_os.db.models.safety_prediction import SafetyPrediction
from pharma_os.db.models.enums import SafetyRiskClass
from pharma_os.db.repositories.base import BaseRepository


class EligibilityPredictionRepository(BaseRepository[EligibilityPrediction]):
    """Repository for trial eligibility model outputs."""

    model = EligibilityPrediction

    def list_by_patient(self, patient_id: UUID, *, limit: int = 100, offset: int = 0) -> list[EligibilityPrediction]:
        statement: Select[tuple[EligibilityPrediction]] = (
            select(EligibilityPrediction)
            .where(EligibilityPrediction.patient_id == patient_id)
            .order_by(EligibilityPrediction.inference_timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def latest_for_patient_trial(self, patient_id: UUID, trial_id: UUID) -> EligibilityPrediction | None:
        statement = (
            select(EligibilityPrediction)
            .where(
                EligibilityPrediction.patient_id == patient_id,
                EligibilityPrediction.trial_id == trial_id,
            )
            .order_by(EligibilityPrediction.inference_timestamp.desc())
            .limit(1)
        )
        return self.session.scalar(statement)


class SafetyPredictionRepository(BaseRepository[SafetyPrediction]):
    """Repository for safety risk model outputs."""

    model = SafetyPrediction

    def list_by_patient(self, patient_id: UUID, *, limit: int = 100, offset: int = 0) -> list[SafetyPrediction]:
        statement: Select[tuple[SafetyPrediction]] = (
            select(SafetyPrediction)
            .where(SafetyPrediction.patient_id == patient_id)
            .order_by(SafetyPrediction.inference_timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def latest_for_patient_exposure(
        self,
        patient_id: UUID,
        drug_exposure_id: UUID | None,
    ) -> SafetyPrediction | None:
        statement = (
            select(SafetyPrediction)
            .where(
                SafetyPrediction.patient_id == patient_id,
                SafetyPrediction.drug_exposure_id == drug_exposure_id,
            )
            .order_by(SafetyPrediction.inference_timestamp.desc())
            .limit(1)
        )
        return self.session.scalar(statement)

    def list_by_risk_class(
        self,
        risk_class: SafetyRiskClass,
        *,
        inferred_from: datetime | None = None,
        inferred_to: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SafetyPrediction]:
        statement: Select[tuple[SafetyPrediction]] = (
            select(SafetyPrediction)
            .where(SafetyPrediction.risk_class == risk_class)
            .order_by(SafetyPrediction.inference_timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        if inferred_from is not None:
            statement = statement.where(SafetyPrediction.inference_timestamp >= inferred_from)
        if inferred_to is not None:
            statement = statement.where(SafetyPrediction.inference_timestamp <= inferred_to)
        return list(self.session.scalars(statement).all())
