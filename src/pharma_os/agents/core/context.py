"""Agent context and context builder for cleaner tool gathering."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentExecutionMetadata:
    """Metadata about agent execution environment."""

    llm_provider: str
    llm_model: str | None
    is_stub_mode: bool
    execution_mode: str = "sync"  # sync or async


@dataclass
class ToolInvocationRecord:
    """Record of a tool call during execution."""

    tool_name: str
    success: bool
    result_summary: str | None = None
    error: str | None = None
    execution_time_ms: float = 0.0


@dataclass
class AgentExecutionContext:
    """Rich context for agent execution with tracked tool calls."""

    trace_id: str
    metadata: AgentExecutionMetadata
    session: Any
    settings: Any
    tool_calls: list[ToolInvocationRecord] = field(default_factory=list)
    error_log: list[str] = field(default_factory=list)

    def record_tool_call(
        self,
        tool_name: str,
        success: bool,
        result_summary: str | None = None,
        error: str | None = None,
        execution_time_ms: float = 0.0,
    ) -> None:
        """Record a tool invocation.

        Args:
            tool_name: Name of tool
            success: Whether call succeeded
            result_summary: Brief summary of result
            error: Error message if failed
            execution_time_ms: Execution time
        """
        self.tool_calls.append(
            ToolInvocationRecord(
                tool_name=tool_name,
                success=success,
                result_summary=result_summary,
                error=error,
                execution_time_ms=execution_time_ms,
            )
        )

    def record_error(self, error_msg: str) -> None:
        """Record an error in execution log.

        Args:
            error_msg: Error message
        """
        self.error_log.append(error_msg)

    def get_successful_tool_calls(self) -> list[str]:
        """Get names of tools that executed successfully.

        Returns:
            List of tool names that succeeded
        """
        return [tc.tool_name for tc in self.tool_calls if tc.success]

    def has_errors(self) -> bool:
        """Check if any errors occurred.

        Returns:
            True if any errors recorded
        """
        return len(self.error_log) > 0 or any(not tc.success for tc in self.tool_calls)
