"""Agent framework base abstractions and contracts."""

from pharma_os.agents.base.agent import BaseAgent, ExecutionContext
from pharma_os.agents.base.contracts import (
    AgentRequest,
    AgentResult,
    AgentType,
    EligibilityAnalysisResult,
    EligibilityAnalystRequest,
    ResearchSummarizerRequest,
    ResearchSummaryResult,
    SafetyInvestigationResult,
    SafetyInvestigatorRequest,
    ToolCall,
    ToolResult,
)
from pharma_os.agents.base.tools import Tool, ToolRegistry
from pharma_os.agents.base.trace import AgentMemoryRecord, AgentTraceMetadata, AgentTraceRecord

__all__ = [
    "BaseAgent",
    "ExecutionContext",
    "AgentRequest",
    "AgentResult",
    "AgentType",
    "EligibilityAnalystRequest",
    "EligibilityAnalysisResult",
    "SafetyInvestigatorRequest",
    "SafetyInvestigationResult",
    "ResearchSummarizerRequest",
    "ResearchSummaryResult",
    "ToolCall",
    "ToolResult",
    "Tool",
    "ToolRegistry",
    "AgentTraceRecord",
    "AgentTraceMetadata",
    "AgentMemoryRecord",
]
