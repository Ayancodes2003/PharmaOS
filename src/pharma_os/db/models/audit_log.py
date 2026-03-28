"""Audit log persistence model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from pharma_os.db.models.base import DomainBase
from pharma_os.db.models.enums import ActorType


class AuditLog(DomainBase):
    """Immutable operational audit log entry for traceability."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_entity_lookup", "entity_type", "entity_id"),
        Index("ix_audit_logs_actor_lookup", "actor_type", "actor_id"),
        Index("ix_audit_logs_actor_action_time", "actor_type", "action_type", "occurred_at"),
        Index("ix_audit_logs_occurred_at", "occurred_at"),
        Index("ix_audit_logs_trace_id", "trace_id"),
    )

    actor_type: Mapped[ActorType] = mapped_column(Enum(ActorType, name="audit_actor_type"), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    action_type: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payload_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    trace_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
