"""Factory for creating agent instances based on task type."""

from __future__ import annotations

import logging
from typing import Type

from pharma_os.agents.base import AgentBase


logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating agent instances dynamically."""

    _agents: dict[str, Type[AgentBase]] = {}
    _instances: dict[str, AgentBase] = {}

    @classmethod
    def register_agent(cls, agent_type: str, agent_class: Type[AgentBase]) -> None:
        """Register an agent class.

        Args:
            agent_type: Type identifier for the agent
            agent_class: Agent class to register
        """
        cls._agents[agent_type] = agent_class
        logger.debug(f"Registered agent: {agent_type}")

    @classmethod
    def create_agent(cls, agent_type: str, **kwargs) -> AgentBase:
        """Create an agent instance.

        Args:
            agent_type: Type of agent to create
            **kwargs: Arguments to pass to agent constructor

        Returns:
            Agent instance

        Raises:
            ValueError: If agent type is not registered
        """
        if agent_type not in cls._agents:
            raise ValueError(f"Unknown agent type: {agent_type}")

        agent_class = cls._agents[agent_type]
        return agent_class(**kwargs)

    @classmethod
    def get_agent_instance(cls, agent_type: str, **kwargs) -> AgentBase:
        """Get or create a singleton agent instance.

        Args:
            agent_type: Type of agent
            **kwargs: Arguments for creation if needed

        Returns:
            Agent instance (singleton)
        """
        if agent_type not in cls._instances:
            cls._instances[agent_type] = cls.create_agent(agent_type, **kwargs)

        return cls._instances[agent_type]

    @classmethod
    def list_registered_agents(cls) -> list[str]:
        """List all registered agent types.

        Returns:
            List of agent type identifiers
        """
        return list(cls._agents.keys())

    @classmethod
    def is_agent_registered(cls, agent_type: str) -> bool:
        """Check if an agent type is registered.

        Args:
            agent_type: Type identifier

        Returns:
            True if registered, False otherwise
        """
        return agent_type in cls._agents

    @classmethod
    def reset_instances(cls) -> None:
        """Reset all singleton instances."""
        cls._instances.clear()
        logger.debug("Reset all agent instances")
