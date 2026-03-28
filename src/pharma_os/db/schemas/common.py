"""Shared Pydantic contracts for persistence-layer DTOs."""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class DTOBase(BaseModel):
    """Base DTO with strict typed parsing for service and API boundaries."""

    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)


class TimestampedReadDTO(DTOBase):
    """Read DTO base including identity and audit timestamps."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QueryPagination(DTOBase):
    """Pagination contract for repository query patterns."""

    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class PaginatedResult(DTOBase, Generic[T]):
    """Generic paginated result contract used by service layer."""

    items: list[T]
    total: int
    limit: int
    offset: int
