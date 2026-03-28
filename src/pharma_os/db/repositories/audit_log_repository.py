"""Audit log repository implementation."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, select

from pharma_os.db.models.audit_log import AuditLog
from pharma_os.db.models.enums import ActorType
from pharma_os.db.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for immutable audit log persistence and retrieval."""

    model = AuditLog

    def list_by_entity(
        self,
        entity_type: str,
        entity_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        statement: Select[tuple[AuditLog]] = (
            select(AuditLog)
            .where(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
            .order_by(AuditLog.occurred_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def list_by_trace_id(self, trace_id: str, *, limit: int = 200, offset: int = 0) -> list[AuditLog]:
        statement: Select[tuple[AuditLog]] = (
            select(AuditLog)
            .where(AuditLog.trace_id == trace_id)
            .order_by(AuditLog.occurred_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def list_by_actor(
        self,
        actor_type: ActorType,
        actor_id: str | None = None,
        *,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        statement: Select[tuple[AuditLog]] = (
            select(AuditLog)
            .where(AuditLog.actor_type == actor_type)
            .order_by(AuditLog.occurred_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if actor_id is not None:
            statement = statement.where(AuditLog.actor_id == actor_id)
        if from_ts is not None:
            statement = statement.where(AuditLog.occurred_at >= from_ts)
        if to_ts is not None:
            statement = statement.where(AuditLog.occurred_at <= to_ts)
        return list(self.session.scalars(statement).all())
