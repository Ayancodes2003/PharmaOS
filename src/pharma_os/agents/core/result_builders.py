"""Result builders for structured agent output construction."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pharma_os.agents.base import (
    EligibilityAnalysisResult,
    SafetyInvestigationResult,
    ResearchSummaryResult,
)
from pharma_os.agents.core.context import AgentExecutionContext


class ResultBuilder:
    """Base class for building agent results."""

    def __init__(self, context: AgentExecutionContext):
        """Initialize result builder.

        Args:
            context: Execution context
        """
        self.context = context
        self.start_time = datetime.utcnow()

    def get_execution_time_ms(self) -> float:
        """Get execution time in milliseconds.

        Returns:
            Execution time
        """
        return (datetime.utcnow() - self.start_time).total_seconds() * 1000


class EligibilityResultBuilder(ResultBuilder):
    """Builds eligibility analysis results."""

    def build_result(
        self,
        success: bool,
        error: str | None = None,
        patient_summary: str = "",
        trial_summary: str = "",
        assessment: str = "",
        inclusion_reasoning: str = "",
        exclusion_reasoning: str = "",
        recommendation: str = "",
        risk_factors: list[str] | None = None,
        evidence: list[str] | None = None,
        prediction_context: dict[str, Any] | None = None,
    ) -> EligibilityAnalysisResult:
        """Build eligibility analysis result.

        Args:
            success: Whether analysis succeeded
            error: Error message if failed
            patient_summary: Patient summary text
            trial_summary: Trial summary text
            assessment: Eligibility assessment
            inclusion_reasoning: Inclusion reasoning
            exclusion_reasoning: Exclusion reasoning
            recommendation: Analyst recommendation
            risk_factors: List of risk factors
            evidence: Evidence snippets
            prediction_context: Prediction data if available

        Returns:
            EligibilityAnalysisResult
        """
        return EligibilityAnalysisResult(
            trace_id=self.context.trace_id,
            execution_time_ms=self.get_execution_time_ms(),
            success=success,
            error=error,
            patient_summary=patient_summary,
            trial_summary=trial_summary,
            eligibility_assessment=assessment,
            inclusion_reasoning=inclusion_reasoning,
            exclusion_reasoning=exclusion_reasoning,
            recommendation=recommendation,
            risk_factors=risk_factors or [],
            evidence_snippets=evidence or [],
            prediction_context=prediction_context or {},
            tool_calls_used=self.context.get_successful_tool_calls(),
        )


class SafetyResultBuilder(ResultBuilder):
    """Builds safety investigation results."""

    def build_result(
        self,
        success: bool,
        error: str | None = None,
        patient_summary: str = "",
        safety_context: str = "",
        risk_assessment: str = "",
        recommendation: str = "",
        suspicious_patterns: list[str] | None = None,
        recent_events: list[dict[str, Any]] | None = None,
        drug_interactions: list[str] | None = None,
        prediction_context: dict[str, Any] | None = None,
    ) -> SafetyInvestigationResult:
        """Build safety investigation result.

        Args:
            success: Whether investigation succeeded
            error: Error message if failed
            patient_summary: Patient summary
            safety_context: Safety context description
            risk_assessment: Risk assessment
            recommendation: Safety recommendation
            suspicious_patterns: Identified patterns
            recent_events: Recent adverse events
            drug_interactions: Drug interaction concerns
            prediction_context: Prediction data if available

        Returns:
            SafetyInvestigationResult
        """
        return SafetyInvestigationResult(
            trace_id=self.context.trace_id,
            execution_time_ms=self.get_execution_time_ms(),
            success=success,
            error=error,
            patient_summary=patient_summary,
            safety_context=safety_context,
            risk_assessment=risk_assessment,
            recommendation=recommendation,
            suspicious_patterns=suspicious_patterns or [],
            recent_events=recent_events or [],
            drug_interaction_concerns=drug_interactions or [],
            prediction_context=prediction_context or {},
            tool_calls_used=self.context.get_successful_tool_calls(),
        )


class ResearchResultBuilder(ResultBuilder):
    """Builds research summarization results."""

    def build_result(
        self,
        success: bool,
        error: str | None = None,
        context_summary: str = "",
        key_points: list[str] | None = None,
        research_question: str | None = None,
        answer: str | None = None,
        document_references: list[str] | None = None,
        extensibility_note: str | None = None,
    ) -> ResearchSummaryResult:
        """Build research summary result.

        Args:
            success: Whether summarization succeeded
            error: Error message if failed
            context_summary: Context summary text
            key_points: List of key points
            research_question: Original research question
            answer: Answer to question
            document_references: Document references
            extensibility_note: Note on future extensibility

        Returns:
            ResearchSummaryResult
        """
        return ResearchSummaryResult(
            trace_id=self.context.trace_id,
            execution_time_ms=self.get_execution_time_ms(),
            success=success,
            error=error,
            context_summary=context_summary,
            key_points=key_points or [],
            research_question=research_question,
            answer=answer,
            document_references=document_references or [],
            extensibility_note=extensibility_note,
            tool_calls_used=self.context.get_successful_tool_calls(),
        )
