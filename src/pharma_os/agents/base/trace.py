"""Agent trace models for persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AgentTraceMetadata(BaseModel):
    """Metadata for agent trace persistence."""

    agent_type: str
    agent_name: str
    execution_time_ms: float
    success: bool
    error: str | None = None
    tool_calls_count: int = 0
    model_name: str | None = None
    provider: str | None = None
    stub_mode: bool | None = None


class AgentTraceRecord(BaseModel):
    """Complete agent trace record for MongoDB persistence."""

    trace_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: AgentTraceMetadata
    request_summary: str | None = None
    request_type: str | None = None
    result_summary: str | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    context_metadata: dict[str, Any] = Field(default_factory=dict)
    full_request: dict[str, Any] | None = None
    full_result: dict[str, Any] | None = None

    class Config:
        """Pydantic config."""

        extra = "allow"


class AgentMemoryRecord(BaseModel):
    """Agent memory record for MongoDB persistence."""

    memory_id: str = Field(description="Unique memory identifier")
    agent_type: str = Field(description="Type/role of agent")
    memory_type: str = Field(
        description="Memory type: context, session, pattern, observation",
    )
    content: str = Field(description="Memory content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    ttl_seconds: int | None = Field(
        default=None,
        description="Optional TTL for automatic expiration",
    )

    class Config:
        """Pydantic config."""

        extra = "allow"
