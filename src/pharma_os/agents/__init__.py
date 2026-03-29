"""Phase 8: Agent orchestration layer for PHARMA-OS.

Provides multi-agent AI subsystem for trial eligibility analysis, safety investigation,
and research summarization without hallucination or generic chatbot patterns.
"""

from pharma_os.agents.base import (
    AgentRequest,
    AgentResult,
    AgentType,
    BaseAgent,
    EligibilityAnalysisResult,
    EligibilityAnalystRequest,
    ExecutionContext,
    ResearchSummarizerRequest,
    ResearchSummaryResult,
    SafetyInvestigationResult,
    SafetyInvestigatorRequest,
    ToolRegistry,
)
from pharma_os.agents.eligibility_analyst import EligibilityAnalystAgent
from pharma_os.agents.llm import LLMProvider, create_llm_provider
from pharma_os.agents.orchestration import AgentDispatcher, AgentExecutor
from pharma_os.agents.prompts import PromptRegistry, create_default_registry
from pharma_os.agents.research_summarizer import ResearchSummarizerAgent
from pharma_os.agents.safety_investigator import SafetyInvestigatorAgent
from pharma_os.agents.tools import create_default_tool_registry

# Lazy import for MongoDB-dependent modules
def get_trace_store():
    """Lazily import TraceStore to avoid motor dependency at module load."""
    from pharma_os.agents.persistence import TraceStore
    return TraceStore

__all__ = [
    # Core abstractions
    "BaseAgent",
    "ExecutionContext",
    "AgentRequest",
    "AgentResult",
    "AgentType",
    # Specific agents
    "EligibilityAnalystAgent",
    "SafetyInvestigatorAgent",
    "ResearchSummarizerAgent",
    # Requests and results
    "EligibilityAnalystRequest",
    "EligibilityAnalysisResult",
    "SafetyInvestigatorRequest",
    "SafetyInvestigationResult",
    "ResearchSummarizerRequest",
    "ResearchSummaryResult",
    # Orchestration
    "AgentDispatcher",
    "AgentExecutor",
    # Lazy-loaded persistence
    "get_trace_store",
    # LLM providers
    "LLMProvider",
    "create_llm_provider",
    # Prompts and tools
    "PromptRegistry",
    "create_default_registry",
    "ToolRegistry",
    "create_default_tool_registry",
]
