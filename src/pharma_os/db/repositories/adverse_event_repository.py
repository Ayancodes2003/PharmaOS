"""Adverse event repository implementation."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, select

from pharma_os.db.models.adverse_event import AdverseEvent
from pharma_os.db.models.enums import AdverseEventSeverity
from pharma_os.db.repositories.base import BaseRepository


class AdverseEventRepository(BaseRepository[AdverseEvent]):
    """Repository for pharmacovigilance adverse event persistence/query operations."""

    model = AdverseEvent

    def list_by_patient(self, patient_id: UUID, *, limit: int = 100, offset: int = 0) -> list[AdverseEvent]:
        statement: Select[tuple[AdverseEvent]] = (
            select(AdverseEvent)
            .where(AdverseEvent.patient_id == patient_id)
            .order_by(AdverseEvent.event_date.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def list_serious(self, *, limit: int = 100, offset: int = 0) -> list[AdverseEvent]:
        statement: Select[tuple[AdverseEvent]] = (
            select(AdverseEvent)
            .where(AdverseEvent.is_serious.is_(True))
            .order_by(AdverseEvent.event_date.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def list_by_date_window(
        self,
        *,
        start: datetime,
        end: datetime,
        severity: AdverseEventSeverity | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AdverseEvent]:
        statement: Select[tuple[AdverseEvent]] = (
            select(AdverseEvent)
            .where(AdverseEvent.event_date >= start, AdverseEvent.event_date <= end)
            .order_by(AdverseEvent.event_date.desc())
            .offset(offset)
            .limit(limit)
        )
        if severity is not None:
            statement = statement.where(AdverseEvent.severity == severity)
        return list(self.session.scalars(statement).all())
