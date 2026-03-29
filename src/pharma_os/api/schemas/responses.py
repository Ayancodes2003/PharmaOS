"""Standard API response envelopes and operational status schemas."""

from datetime import UTC, datetime
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard successful response envelope."""

    status: Literal["success"] = "success"
    message: str = "ok"
    data: T


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""

    limit: int
    offset: int
    count: int


class PaginatedPayload(BaseModel, Generic[T]):
    """Reusable paginated payload contract."""

    items: list[T]
    pagination: PaginationMeta


class ErrorDetail(BaseModel):
    """Detailed error payload."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    status: Literal["error"] = "error"
    error: ErrorDetail
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HealthPayload(BaseModel):
    """Liveness payload for health checks."""

    status: Literal["healthy"] = "healthy"
    app_name: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DependencyStatus(BaseModel):
    """Dependency readiness status payload."""

    status: Literal["ready", "not_ready"]
    detail: str | None = None


class ReadinessPayload(BaseModel):
    """Readiness payload with dependency-level statuses."""

    status: Literal["ready", "degraded"]
    app_name: str
    version: str
    environment: str
    dependencies: dict[str, DependencyStatus]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
