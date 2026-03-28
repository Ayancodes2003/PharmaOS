"""Audit log DTO contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from pharma_os.db.models.enums import ActorType
from pharma_os.db.schemas.common import DTOBase, TimestampedReadDTO


class AuditLogCreateDTO(DTOBase):
    actor_type: ActorType
    actor_id: str | None = Field(default=None, max_length=128)
    action_type: str = Field(min_length=1, max_length=128)
    entity_type: str = Field(min_length=1, max_length=128)
    entity_id: str | None = Field(default=None, max_length=128)
    payload_summary: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)
    trace_id: str | None = Field(default=None, max_length=128)
    occurred_at: datetime


class AuditLogReadDTO(TimestampedReadDTO):
    actor_type: ActorType
    actor_id: str | None
    action_type: str
    entity_type: str
    entity_id: str | None
    payload_summary: str | None
    metadata_json: dict[str, object]
    trace_id: str | None
    occurred_at: datetime


class AuditLogFilterDTO(DTOBase):
    actor_type: ActorType | None = None
    action_type: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    trace_id: str | None = None
    occurred_from: datetime | None = None
    occurred_to: datetime | None = None
