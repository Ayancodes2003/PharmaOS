"""Agent orchestration and request routing."""

from __future__ import annotations

import logging
from typing import Any

from pharma_os.agents.base import (
    AgentRequest,
    AgentResult,
    AgentType,
    BaseAgent,
    EligibilityAnalysisResult,
    EligibilityAnalystRequest,
    ExecutionContext,
    ResearchSummaryResult,
    ResearchSummarizerRequest,
    SafetyInvestigationResult,
    SafetyInvestigatorRequest,
)
from pharma_os.agents.eligibility_analyst import EligibilityAnalystAgent
from pharma_os.agents.llm import create_llm_provider
from pharma_os.agents.prompts import create_default_registry
from pharma_os.agents.research_summarizer import ResearchSummarizerAgent
from pharma_os.agents.safety_investigator import SafetyInvestigatorAgent
from pharma_os.agents.tools import create_default_tool_registry

# Lazy import for trace_store to avoid motor dependency
def _get_trace_store_class():
    """Lazily import TraceStore."""
    try:
        from pharma_os.agents.persistence import TraceStore
        return TraceStore
    except ImportError:
        logger.warning("MongoDB/motor not available; trace persistence disabled")
        return None

logger = logging.getLogger(__name__)


class AgentDispatcher:
    """Routes requests to appropriate agents and manages agent initialization."""

    def __init__(self, settings: Any):
        """Initialize dispatcher.

        Args:
            settings: Application settings with LLM configuration
        """
        self.settings = settings

        # Initialize LLM provider
        self.llm_provider = create_llm_provider(
            provider=settings.llm_provider,
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )

        # Initialize prompt registry
        self.prompt_registry = create_default_registry()

        # Initialize tool registry
        self.tool_registry = create_default_tool_registry()

        # Initialize agents
        self._agents: dict[AgentType, BaseAgent] = {}
        self._initialize_agents()

    def _initialize_agents(self) -> None:
        """Initialize all agents."""
        self._agents[AgentType.ELIGIBILITY_ANALYST] = EligibilityAnalystAgent(
            self.llm_provider,
            self.prompt_registry,
        )

        self._agents[AgentType.SAFETY_INVESTIGATOR] = SafetyInvestigatorAgent(
            self.llm_provider,
            self.prompt_registry,
        )

        self._agents[AgentType.RESEARCH_SUMMARIZER] = ResearchSummarizerAgent(
            self.llm_provider,
            self.prompt_registry,
        )

        logger.info(f"Initialized {len(self._agents)} agents")

    def get_agent(self, agent_type: AgentType) -> BaseAgent | None:
        """Get agent by type.

        Args:
            agent_type: AgentType enum value

        Returns:
            BaseAgent instance or None if not found
        """
        return self._agents.get(agent_type)

    async def dispatch(
        self,
        request: AgentRequest,
        session: Any,
    ) -> AgentResult:
        """Dispatch request to appropriate agent.

        Args:
            request: Agent request
            session: Database session

        Returns:
            Agent result
        """
        # Create execution context
        context = ExecutionContext(
            session=session,
            settings=self.settings,
            tool_registry=self.tool_registry,
            trace_id=request.trace_id,
            metadata=request.metadata,
        )

        # Get appropriate agent
        agent = self.get_agent(request.agent_type)
        if not agent:
            raise ValueError(f"No agent found for type: {request.agent_type}")

        # Execute agent
        logger.info(f"Dispatching request to {request.agent_type.value} agent")
        result = await agent.execute(request, context)

        # Record tool calls in result
        result.tool_calls_used = [tc.tool_name for tc in context.tool_calls]

        return result

    def list_available_agents(self) -> list[dict[str, Any]]:
        """List available agents with metadata.

        Returns:
            List of agent metadata dictionaries
        """
        agents = []
        for agent_type, agent in self._agents.items():
            stub_mode = self.llm_provider.get_provider_name() == "stub"
            agents.append({
                "agent_type": agent_type.value,
                "agent_name": agent.get_agent_name(),
                "agent_description": agent.get_agent_description(),
                "llm_available": self.llm_provider.is_available(),
                "llm_provider": self.llm_provider.get_provider_name(),
                "llm_model": self.llm_provider.get_model_name(),
                "stub_mode": stub_mode,
            })
        return agents

    def get_tools_info(self) -> list[dict[str, Any]]:
        """Get information about available tools.

        Returns:
            List of tool dictionaries
        """
        return self.tool_registry.to_dict()


class AgentExecutor:
    """Executes agent requests with trace persistence."""

    def __init__(
        self,
        dispatcher: AgentDispatcher,
        trace_store: Any | None = None,
    ):
        """Initialize executor.

        Args:
            dispatcher: AgentDispatcher instance
            trace_store: Optional trace store for persistence (MongoDB)
        """
        self.dispatcher = dispatcher
        self.trace_store = trace_store

    async def execute(
        self,
        request: AgentRequest,
        session: Any,
    ) -> tuple[AgentResult, dict[str, Any]]:
        """Execute agent request with tracing.

        Args:
            request: Agent request
            session: Database session

        Returns:
            Tuple of (result, execution_metadata)
        """
        try:
            # Dispatch to agent
            result = await self.dispatcher.dispatch(request, session)

            # Persist trace if store available
            if self.trace_store:
                await self.trace_store.persist_trace(
                    result,
                    provider_metadata={
                        "provider": self.dispatcher.llm_provider.get_provider_name(),
                        "model_name": self.dispatcher.llm_provider.get_model_name(),
                        "stub_mode": self.dispatcher.llm_provider.get_provider_name() == "stub",
                    },
                )

            metadata = {
                "trace_id": result.trace_id,
                "agent_type": result.agent_type.value,
                "success": result.success,
                "execution_time_ms": result.execution_time_ms,
                "tool_calls": len(result.tool_calls_used),
                "llm_provider": self.dispatcher.llm_provider.get_provider_name(),
                "llm_model": self.dispatcher.llm_provider.get_model_name(),
                "stub_mode": self.dispatcher.llm_provider.get_provider_name() == "stub",
            }

            return result, metadata

        except Exception as e:
            logger.error(f"Error executing agent: {e}")
            metadata = {
                "trace_id": request.trace_id or "unknown",
                "agent_type": request.agent_type.value if hasattr(request, "agent_type") else "unknown",
                "success": False,
                "error": str(e),
            }

            # Create error result
            error_result: AgentResult
            if request.agent_type == AgentType.ELIGIBILITY_ANALYST:
                error_result = EligibilityAnalysisResult(
                    trace_id=request.trace_id,
                    success=False,
                    error=str(e),
                    execution_time_ms=0,
                )
            elif request.agent_type == AgentType.SAFETY_INVESTIGATOR:
                error_result = SafetyInvestigationResult(
                    trace_id=request.trace_id,
                    success=False,
                    error=str(e),
                    execution_time_ms=0,
                )
            elif request.agent_type == AgentType.RESEARCH_SUMMARIZER:
                error_result = ResearchSummaryResult(
                    trace_id=request.trace_id,
                    success=False,
                    error=str(e),
                    execution_time_ms=0,
                )
            else:
                raise

            return error_result, metadata
