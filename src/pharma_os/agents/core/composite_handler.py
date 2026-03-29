"""Composite handler for orchestrating multiple agent executions."""

from __future__ import annotations

import logging
from typing import Any

from pharma_os.agents.base import AgentBase, AgentResult
from pharma_os.agents.core.context import AgentExecutionContext


logger = logging.getLogger(__name__)


class CompositeAgentHandler:
    """Orchestrates execution of multiple agents for complex workflows."""

    def __init__(self, context: AgentExecutionContext):
        """Initialize composite handler.

        Args:
            context: Execution context
        """
        self.context = context
        self.execution_log: list[dict[str, Any]] = []

    def execute_sequential(
        self, agents: list[AgentBase], share_results: bool = True
    ) -> list[AgentResult]:
        """Execute agents sequentially, optionally sharing results.

        Args:
            agents: List of agents to execute
            share_results: Whether to share previous results with next agent

        Returns:
            List of results from each agent
        """
        results: list[AgentResult] = []

        for i, agent in enumerate(agents):
            logger.info(f"Executing agent {i + 1}/{len(agents)}: {agent.__class__.__name__}")

            # Share previous results if enabled
            if share_results and results:
                self.context.set_parent_results(results)

            result = agent.execute(self.context)
            results.append(result)

            # Log execution
            self.execution_log.append(
                {
                    "agent_index": i,
                    "agent_name": agent.__class__.__name__,
                    "success": result.success,
                    "execution_time_ms": result.execution_time_ms,
                }
            )

            if not result.success:
                logger.warning(
                    f"Agent {agent.__class__.__name__} failed: {result.error}"
                )
                if not self._should_continue_on_failure(i, agents):
                    break

        return results

    def execute_parallel(self, agents: list[AgentBase]) -> list[AgentResult]:
        """Execute agents in parallel (simulated).

        Args:
            agents: List of agents to execute

        Returns:
            List of results from each agent
        """
        logger.info(f"Executing {len(agents)} agents in parallel")
        results: list[AgentResult] = []

        for agent in agents:
            result = agent.execute(self.context)
            results.append(result)

            self.execution_log.append(
                {
                    "agent_name": agent.__class__.__name__,
                    "success": result.success,
                    "execution_time_ms": result.execution_time_ms,
                }
            )

        return results

    def execute_fallback(self, agents: list[AgentBase]) -> AgentResult | None:
        """Execute agents with fallback strategy.

        Args:
            agents: List of agents to try in order

        Returns:
            First successful result, or None if all fail
        """
        logger.info(f"Executing {len(agents)} agents with fallback strategy")

        for i, agent in enumerate(agents):
            logger.debug(f"Trying agent {i + 1}/{len(agents)}: {agent.__class__.__name__}")

            result = agent.execute(self.context)

            self.execution_log.append(
                {
                    "agent_name": agent.__class__.__name__,
                    "success": result.success,
                    "fallback_index": i,
                }
            )

            if result.success:
                logger.info(f"Agent {agent.__class__.__name__} succeeded")
                return result

        logger.warning("All fallback agents failed")
        return None

    def get_execution_summary(self) -> str:
        """Get summary of all executions.

        Returns:
            Execution summary string
        """
        lines = ["Composite Execution Summary", "=" * 40]

        for entry in self.execution_log:
            agent_name = entry.get("agent_name", "Unknown")
            success = "✓" if entry.get("success") else "✗"
            exec_time = entry.get("execution_time_ms", 0)
            lines.append(f"{success} {agent_name}: {exec_time:.2f}ms")

        return "\n".join(lines)

    def _should_continue_on_failure(self, index: int, agents: list[AgentBase]) -> bool:
        """Determine if execution should continue after failure.

        Args:
            index: Index of failed agent
            agents: List of all agents

        Returns:
            True if should continue, False if should stop
        """
        # Continue by default for most failures
        # Can be customized based on failure type or configuration
        return index < len(agents) - 1
