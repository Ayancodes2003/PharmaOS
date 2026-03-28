"""Trial repository implementation."""

from __future__ import annotations

from sqlalchemy import Select, select

from pharma_os.db.models.enums import TrialStatus
from pharma_os.db.models.trial import Trial
from pharma_os.db.repositories.base import BaseRepository


class TrialRepository(BaseRepository[Trial]):
    """Repository for trial persistence and retrieval patterns."""

    model = Trial

    def get_by_trial_code(self, trial_code: str) -> Trial | None:
        statement = select(Trial).where(Trial.trial_code == trial_code)
        return self.session.scalar(statement)

    def list_recruiting(self, *, limit: int = 100, offset: int = 0) -> list[Trial]:
        statement: Select[tuple[Trial]] = (
            select(Trial)
            .where(Trial.status == TrialStatus.RECRUITING)
            .order_by(Trial.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def list_by_indication(self, indication: str, *, limit: int = 100, offset: int = 0) -> list[Trial]:
        statement: Select[tuple[Trial]] = (
            select(Trial)
            .where(Trial.indication.ilike(f"%{indication}%"))
            .order_by(Trial.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())
