"""Recruitment ranking repository implementation."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, select

from pharma_os.db.models.recruitment_ranking import RecruitmentRanking
from pharma_os.db.repositories.base import BaseRepository


class RecruitmentRepository(BaseRepository[RecruitmentRanking]):
    """Repository for persisted recruitment ranking outputs."""

    model = RecruitmentRanking

    def list_for_trial(self, trial_id: UUID, *, limit: int = 100, offset: int = 0) -> list[RecruitmentRanking]:
        statement: Select[tuple[RecruitmentRanking]] = (
            select(RecruitmentRanking)
            .where(RecruitmentRanking.trial_id == trial_id)
            .order_by(RecruitmentRanking.rank_position.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def list_for_trial_run(
        self,
        trial_id: UUID,
        ranking_run_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RecruitmentRanking]:
        statement: Select[tuple[RecruitmentRanking]] = (
            select(RecruitmentRanking)
            .where(
                RecruitmentRanking.trial_id == trial_id,
                RecruitmentRanking.ranking_run_id == ranking_run_id,
            )
            .order_by(RecruitmentRanking.rank_position.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def top_candidates(self, trial_id: UUID, *, top_n: int = 20) -> list[RecruitmentRanking]:
        statement = (
            select(RecruitmentRanking)
            .where(RecruitmentRanking.trial_id == trial_id)
            .order_by(RecruitmentRanking.rank_position.asc())
            .limit(top_n)
        )
        return list(self.session.scalars(statement).all())

    def top_candidates_for_trial_run(
        self,
        trial_id: UUID,
        ranking_run_id: UUID,
        *,
        top_n: int = 20,
    ) -> list[RecruitmentRanking]:
        statement = (
            select(RecruitmentRanking)
            .where(
                RecruitmentRanking.trial_id == trial_id,
                RecruitmentRanking.ranking_run_id == ranking_run_id,
            )
            .order_by(RecruitmentRanking.rank_position.asc())
            .limit(top_n)
        )
        return list(self.session.scalars(statement).all())

    def latest_generation_for_trial(self, trial_id: UUID) -> datetime | None:
        statement = (
            select(RecruitmentRanking.generated_at)
            .where(RecruitmentRanking.trial_id == trial_id)
            .order_by(RecruitmentRanking.generated_at.desc())
            .limit(1)
        )
        return self.session.scalar(statement)

    def latest_run_id_for_trial(self, trial_id: UUID) -> UUID | None:
        statement = (
            select(RecruitmentRanking.ranking_run_id)
            .where(RecruitmentRanking.trial_id == trial_id)
            .order_by(RecruitmentRanking.generated_at.desc())
            .limit(1)
        )
        return self.session.scalar(statement)
