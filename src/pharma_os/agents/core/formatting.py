"""Unified structured output formatting for agent analysis."""

from __future__ import annotations

from typing import Any

from pharma_os.agents.base import (
    EligibilityAnalysisResult,
    SafetyInvestigationResult,
    ResearchSummaryResult,
)


class FormattingEngine:
    """Formats agent analysis results for structured output."""

    @staticmethod
    def format_eligibility_result(result: EligibilityAnalysisResult) -> dict[str, Any]:
        """Format eligibility analysis for output.

        Args:
            result: Eligibility analysis result

        Returns:
            Formatted dictionary
        """
        return {
            "status": "success" if result.success else "failure",
            "trace_id": result.trace_id,
            "execution_time_ms": result.execution_time_ms,
            "error": result.error or "",
            "patient_summary": result.patient_summary,
            "trial_summary": result.trial_summary,
            "assessment": {
                "eligibility": result.eligibility_assessment,
                "inclusion_reasoning": result.inclusion_reasoning,
                "exclusion_reasoning": result.exclusion_reasoning,
                "recommendation": result.recommendation,
            },
            "risk_factors": result.risk_factors,
            "evidence": result.evidence_snippets,
            "prediction": result.prediction_context,
            "tools_used": result.tool_calls_used,
        }

    @staticmethod
    def format_safety_result(result: SafetyInvestigationResult) -> dict[str, Any]:
        """Format safety investigation for output.

        Args:
            result: Safety investigation result

        Returns:
            Formatted dictionary
        """
        return {
            "status": "success" if result.success else "failure",
            "trace_id": result.trace_id,
            "execution_time_ms": result.execution_time_ms,
            "error": result.error or "",
            "patient_summary": result.patient_summary,
            "context": result.safety_context,
            "analysis": {
                "risk_assessment": result.risk_assessment,
                "recommendation": result.recommendation,
            },
            "findings": {
                "suspicious_patterns": result.suspicious_patterns,
                "recent_events": result.recent_events,
                "drug_interactions": result.drug_interaction_concerns,
            },
            "prediction": result.prediction_context,
            "tools_used": result.tool_calls_used,
        }

    @staticmethod
    def format_research_result(result: ResearchSummaryResult) -> dict[str, Any]:
        """Format research summary for output.

        Args:
            result: Research summary result

        Returns:
            Formatted dictionary
        """
        return {
            "status": "success" if result.success else "failure",
            "trace_id": result.trace_id,
            "execution_time_ms": result.execution_time_ms,
            "error": result.error or "",
            "research_question": result.research_question,
            "answer": result.answer,
            "summary": {
                "context": result.context_summary,
                "key_points": result.key_points,
            },
            "references": result.document_references,
            "extensibility": result.extensibility_note,
            "tools_used": result.tool_calls_used,
        }

    @staticmethod
    def format_as_json_lines(result: dict[str, Any]) -> str:
        """Convert result to JSON Lines format.

        Args:
            result: Formatted result dictionary

        Returns:
            JSON string
        """
        import json

        return json.dumps(result, indent=2)

    @staticmethod
    def format_as_markdown(result: dict[str, Any], title: str = "Analysis Result") -> str:
        """Convert result to Markdown format.

        Args:
            result: Formatted result dictionary
            title: Title for the markdown

        Returns:
            Markdown string
        """
        lines = [f"# {title}\n"]

        lines.append(f"**Status**: {result.get('status', 'unknown')}")
        lines.append(f"**Trace ID**: `{result.get('trace_id', 'unknown')}`")
        lines.append(f"**Execution Time**: {result.get('execution_time_ms', 0):.2f}ms\n")

        if result.get("error"):
            lines.append(f"**Error**: {result['error']}\n")

        # Format patient/context info
        if result.get("patient_summary"):
            lines.append("## Patient Summary")
            lines.append(result["patient_summary"])
            lines.append("")

        if result.get("trial_summary"):
            lines.append("## Trial Summary")
            lines.append(result["trial_summary"])
            lines.append("")

        if result.get("context"):
            lines.append("## Safety Context")
            lines.append(result["context"])
            lines.append("")

        if result.get("research_question"):
            lines.append("## Research Question")
            lines.append(result["research_question"])
            lines.append("")

        # Format assessment/analysis
        if result.get("assessment"):
            lines.append("## Assessment")
            for key, value in result["assessment"].items():
                lines.append(f"**{key.replace('_', ' ').title()}**: {value}")
            lines.append("")

        if result.get("analysis"):
            lines.append("## Analysis")
            for key, value in result["analysis"].items():
                lines.append(f"**{key.replace('_', ' ').title()}**: {value}")
            lines.append("")

        if result.get("answer"):
            lines.append("## Answer")
            lines.append(result["answer"])
            lines.append("")

        # Format findings
        if result.get("findings"):
            lines.append("## Findings")
            for key, items in result["findings"].items():
                if items:
                    lines.append(f"### {key.replace('_', ' ').title()}")
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                lines.append(f"- {item}")
                            else:
                                lines.append(f"- {item}")
                    else:
                        lines.append(str(items))
                    lines.append("")

        # Format summary for research
        if result.get("summary"):
            lines.append("## Summary")
            if result["summary"].get("context"):
                lines.append(result["summary"]["context"])
            if result["summary"].get("key_points"):
                lines.append("\n### Key Points")
                for point in result["summary"]["key_points"]:
                    lines.append(f"- {point}")
            lines.append("")

        # Format risk factors
        if result.get("risk_factors"):
            lines.append("## Risk Factors")
            for factor in result["risk_factors"]:
                lines.append(f"- {factor}")
            lines.append("")

        # Format evidence
        if result.get("evidence"):
            lines.append("## Evidence")
            for evidence in result["evidence"]:
                lines.append(f"- {evidence}")
            lines.append("")

        # Format references
        if result.get("references"):
            lines.append("## References")
            for ref in result["references"]:
                lines.append(f"- {ref}")
            lines.append("")

        # Format extensibility note
        if result.get("extensibility"):
            lines.append("## Extensibility Note")
            lines.append(result["extensibility"])
            lines.append("")

        # Format tools used
        if result.get("tools_used"):
            lines.append("## Tools Used")
            for tool in result["tools_used"]:
                lines.append(f"- {tool}")

        return "\n".join(lines)
