"""Drug exposure repository implementation."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Select, select

from pharma_os.db.models.drug_exposure import DrugExposure
from pharma_os.db.repositories.base import BaseRepository


class DrugExposureRepository(BaseRepository[DrugExposure]):
    """Repository for patient medication exposure records."""

    model = DrugExposure

    def list_by_patient(self, patient_id: UUID, *, limit: int = 100, offset: int = 0) -> list[DrugExposure]:
        statement: Select[tuple[DrugExposure]] = (
            select(DrugExposure)
            .where(DrugExposure.patient_id == patient_id)
            .order_by(DrugExposure.start_date.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def list_active_by_patient(self, patient_id: UUID, *, as_of: date | None = None) -> list[DrugExposure]:
        statement: Select[tuple[DrugExposure]] = (
            select(DrugExposure)
            .where(DrugExposure.patient_id == patient_id, DrugExposure.is_active.is_(True))
            .order_by(DrugExposure.start_date.desc())
        )
        if as_of is not None:
            statement = statement.where(
                DrugExposure.start_date <= as_of,
                (DrugExposure.end_date.is_(None)) | (DrugExposure.end_date >= as_of),
            )
        return list(self.session.scalars(statement).all())

    def list_by_drug_name(self, drug_name: str, *, limit: int = 100, offset: int = 0) -> list[DrugExposure]:
        statement: Select[tuple[DrugExposure]] = (
            select(DrugExposure)
            .where(DrugExposure.drug_name.ilike(f"%{drug_name}%"))
            .order_by(DrugExposure.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())
