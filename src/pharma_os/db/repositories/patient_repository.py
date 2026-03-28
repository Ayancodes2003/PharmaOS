"""Patient repository implementation."""

from __future__ import annotations

from sqlalchemy import Select, select

from pharma_os.db.models.patient import Patient
from pharma_os.db.repositories.base import BaseRepository


class PatientRepository(BaseRepository[Patient]):
    """Repository for patient persistence and query operations."""

    model = Patient

    def get_by_external_patient_id(self, external_patient_id: str) -> Patient | None:
        statement = select(Patient).where(Patient.external_patient_id == external_patient_id)
        return self.session.scalar(statement)

    def list_active(self, *, limit: int = 100, offset: int = 0) -> list[Patient]:
        statement: Select[tuple[Patient]] = (
            select(Patient)
            .where(Patient.is_active.is_(True))
            .order_by(Patient.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def list_by_condition(self, condition: str, *, limit: int = 100, offset: int = 0) -> list[Patient]:
        statement: Select[tuple[Patient]] = (
            select(Patient)
            .where(Patient.primary_condition.ilike(f"%{condition}%"))
            .order_by(Patient.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())
