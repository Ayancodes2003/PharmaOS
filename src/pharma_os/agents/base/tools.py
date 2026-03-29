"""Tool abstraction layer for agent use."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pharma_os.agents.base.contracts import ToolCall, ToolResult


class Tool(ABC):
    """Abstract base class for agent-callable tools."""

    @abstractmethod
    def get_name(self) -> str:
        """Get tool name."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get tool description."""
        pass

    @abstractmethod
    async def execute(self, args: dict[str, Any]) -> ToolResult:
        """Execute tool with given arguments.

        Args:
            args: Dictionary of tool arguments

        Returns:
            ToolResult with success flag and data
        """
        pass

    def to_dict(self) -> dict[str, Any]:
        """Convert tool to dictionary for LLM context."""
        return {
            "name": self.get_name(),
            "description": self.get_description(),
        }

    async def call_and_record(
        self,
        args: dict[str, Any],
    ) -> tuple[ToolResult, ToolCall]:
        """Execute tool and return both result and call record.

        Args:
            args: Tool arguments

        Returns:
            Tuple of (ToolResult, ToolCall record)
        """
        start_time = datetime.utcnow()
        try:
            result = await self.execute(args)
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            call_record = ToolCall(
                tool_name=self.get_name(),
                args=args,
                result_summary=str(result.message or result.data)[:200],
                error=result.error,
                execution_time_ms=elapsed_ms,
            )
            return result, call_record
        except Exception as e:
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            error_msg = str(e)
            call_record = ToolCall(
                tool_name=self.get_name(),
                args=args,
                error=error_msg,
                execution_time_ms=elapsed_ms,
            )
            return (
                ToolResult(success=False, error=error_msg),
                call_record,
            )


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        """Initialize empty tool registry."""
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool.

        Args:
            tool: Tool instance to register
        """
        self._tools[tool.get_name()] = tool

    def get(self, name: str) -> Tool | None:
        """Get tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)

    def list_all(self) -> list[Tool]:
        """List all registered tools.

        Returns:
            List of Tool instances
        """
        return list(self._tools.values())

    def to_dict(self) -> list[dict[str, Any]]:
        """Convert all tools to dictionary for LLM context.

        Returns:
            List of tool dictionaries
        """
        return [tool.to_dict() for tool in self._tools.values()]
