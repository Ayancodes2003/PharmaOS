"""Agent request/response contracts and shared types."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Agent role classification."""

    ELIGIBILITY_ANALYST = "eligibility_analyst"
    SAFETY_INVESTIGATOR = "safety_investigator"
    RESEARCH_SUMMARIZER = "research_summarizer"


class AgentRequest(BaseModel):
    """Base agent request contract."""

    agent_type: AgentType
    trace_id: str | None = Field(default=None, description="Optional trace ID for correlation")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata")


class EligibilityAnalystRequest(AgentRequest):
    """Request for trial eligibility analysis."""

    agent_type: AgentType = Field(default=AgentType.ELIGIBILITY_ANALYST)
    patient_id: str = Field(description="Patient UUID or external ID")
    trial_id: str = Field(description="Trial UUID or trial_code")
    include_prediction: bool = Field(
        default=True,
        description="Include eligibility prediction if available",
    )


class SafetyInvestigatorRequest(AgentRequest):
    """Request for safety investigation and adverse event analysis."""

    agent_type: AgentType = Field(default=AgentType.SAFETY_INVESTIGATOR)
    patient_id: str = Field(description="Patient UUID or external ID")
    drug_name: str | None = Field(
        default=None,
        description="Optional specific drug to investigate",
    )
    include_prediction: bool = Field(
        default=True,
        description="Include safety prediction if available",
    )


class ResearchSummarizerRequest(AgentRequest):
    """Request for research summarization."""

    agent_type: AgentType = Field(default=AgentType.RESEARCH_SUMMARIZER)
    trial_id: str | None = Field(default=None, description="Trial UUID or trial_code")
    query: str | None = Field(default=None, description="Free-form research query")
    context_type: str = Field(
        default="trial",
        description="Context type: trial, literature, disease, drug",
    )


class AgentResult(BaseModel):
    """Base agent result contract."""

    agent_type: AgentType
    trace_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    execution_time_ms: float = Field(description="Execution time in milliseconds")
    tool_calls_used: list[str] = Field(default_factory=list, description="List of tool names called")
    success: bool = True
    error: str | None = None


class EligibilityAnalysisResult(AgentResult):
    """Result of eligibility analysis."""

    agent_type: AgentType = Field(default=AgentType.ELIGIBILITY_ANALYST)
    patient_summary: str = Field(description="Brief patient profile summary")
    trial_summary: str = Field(description="Brief trial profile summary")
    eligibility_assessment: str = Field(
        description="Eligibility analysis: likely fit, blockers, caution areas",
    )
    inclusion_reasoning: str = Field(description="Reasoning for probable inclusion")
    exclusion_reasoning: str = Field(description="Reasoning for probable exclusion")
    recommendation: str = Field(description="Analyst recommendation")
    prediction_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Eligibility prediction output if available",
    )
    risk_factors: list[str] = Field(
        default_factory=list,
        description="Identified risk factors or blockers",
    )
    evidence_snippets: list[str] = Field(
        default_factory=list,
        description="Relevant data points supporting analysis",
    )


class SafetyInvestigationResult(AgentResult):
    """Result of safety investigation."""

    agent_type: AgentType = Field(default=AgentType.SAFETY_INVESTIGATOR)
    patient_summary: str = Field(description="Brief patient profile summary")
    safety_context: str = Field(
        description="Critical adverse events, patterns, and exposures",
    )
    risk_assessment: str = Field(
        description="Safety risk assessment and concern summary",
    )
    suspicious_patterns: list[str] = Field(
        default_factory=list,
        description="Identified suspicious patterns or red flags",
    )
    recommendation: str = Field(description="Safety operational recommendation")
    prediction_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Safety prediction output if available",
    )
    recent_events: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Recent adverse events with dates and severity",
    )
    drug_interaction_concerns: list[str] = Field(
        default_factory=list,
        description="Potential drug interaction or cumulative toxicity concerns",
    )


class ResearchSummaryResult(AgentResult):
    """Result of research summarization."""

    agent_type: AgentType = Field(default=AgentType.RESEARCH_SUMMARIZER)
    context_summary: str = Field(description="Summary of trial criteria, study design, or research")
    key_points: list[str] = Field(default_factory=list, description="Key takeaways")
    research_question: str | None = Field(default=None, description="Original research question if provided")
    answer: str | None = Field(default=None, description="Answer to research question if provided")
    document_references: list[str] = Field(
        default_factory=list,
        description="References to source documents or data points",
    )
    extensibility_note: str | None = Field(
        default=None,
        description="Note on future RAG/retrieval extensibility",
    )


class ToolCall(BaseModel):
    """Record of a tool invocation during agent execution."""

    tool_name: str
    args: dict[str, Any] = Field(default_factory=dict)
    result_summary: str | None = None
    error: str | None = None
    execution_time_ms: float = 0.0


class ToolResult(BaseModel):
    """Result returned from a tool call."""

    success: bool = True
    data: Any = None
    error: str | None = None
    message: str | None = None
