"""API-facing schemas for agent execution endpoints."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class AgentExecutionMetadata(BaseModel):
    """Execution metadata returned by agent APIs."""

    trace_id: str
    agent_type: str
    success: bool
    execution_time_ms: float | None = None
    tool_calls: int | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    stub_mode: bool = False
    error: str | None = None


class AgentExecutionPayload(BaseModel, Generic[T]):
    """Wrapped result payload for agent endpoints."""

    result: T
    execution: AgentExecutionMetadata
