"""Base agent interface and abstract class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pharma_os.agents.base.contracts import AgentRequest, AgentResult, ToolCall


class ExecutionContext:
    """Execution context passed to agent during execution."""

    def __init__(
        self,
        session: Any,
        settings: Any,
        trace_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize execution context.

        Args:
            session: SQLAlchemy database session
            settings: Application settings
            trace_id: Optional trace ID for correlation
            metadata: Optional metadata dictionary
        """
        self.session = session
        self.settings = settings
        self.trace_id = trace_id or f"trace_{datetime.utcnow().timestamp()}"
        self.metadata = metadata or {}
        self.tool_calls: list[ToolCall] = []

    def record_tool_call(self, tool_call: ToolCall) -> None:
        """Record a tool call made during execution."""
        self.tool_calls.append(tool_call)

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "trace_id": self.trace_id,
            "metadata": self.metadata,
            "tool_calls_count": len(self.tool_calls),
        }


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, llm_provider: Any):
        """Initialize agent.

        Args:
            llm_provider: LLM provider instance for language model access
        """
        self.llm_provider = llm_provider

    @abstractmethod
    async def execute(
        self,
        request: AgentRequest,
        context: ExecutionContext,
    ) -> AgentResult:
        """Execute agent logic.

        Args:
            request: Agent request with specific parameters
            context: Execution context with session and settings

        Returns:
            AgentResult with analysis output and metadata
        """
        pass

    def get_agent_name(self) -> str:
        """Get human-readable agent name."""
        return self.__class__.__name__

    def get_agent_description(self) -> str:
        """Get agent description."""
        return self.__doc__ or "Agent for specialized analysis"
