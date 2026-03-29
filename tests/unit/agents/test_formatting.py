"""Tests for formatting engine."""

import json
import pytest
from pharma_os.agents.base import EligibilityAnalysisResult, SafetyInvestigationResult, ResearchSummaryResult
from pharma_os.agents.core.context import AgentExecutionContext
from pharma_os.agents.core.formatting import FormattingEngine
from pharma_os.agents.core.result_builders import (
    EligibilityResultBuilder,
    SafetyResultBuilder,
    ResearchResultBuilder,
)


class TestFormattingEngine:
    """Tests for formatting engine."""

    def test_eligibility_result_formatting(self):
        """Test eligibility result formatting."""
        context = AgentExecutionContext()
        builder = EligibilityResultBuilder(context)
        
        result = builder.build_result(
            success=True,
            patient_summary="45-year-old male",
            trial_summary="Phase II cancer trial",
            assessment="ELIGIBLE",
            inclusion_reasoning="Meets all criteria",
            exclusion_reasoning="None",
            recommendation="Enroll",
            risk_factors=["Factor 1"],
            evidence=["Evidence 1"]
        )
        
        formatted = FormattingEngine.format_eligibility_result(result)
        
        assert formatted["status"] == "success"
        assert formatted["trace_id"] == result.trace_id
        assert formatted["error"] == ""
        assert "assessment" in formatted
        assert len(formatted["risk_factors"]) == 1

    def test_safety_result_formatting(self):
        """Test safety result formatting."""
        context = AgentExecutionContext()
        builder = SafetyResultBuilder(context)
        
        result = builder.build_result(
            success=True,
            patient_summary="Test patient",
            safety_context="Test context",
            risk_assessment="HIGH",
            recommendation="Monitor closely",
            suspicious_patterns=["Pattern 1"],
            recent_events=[{"type": "test"}],
            drug_interactions=["Interaction 1"]
        )
        
        formatted = FormattingEngine.format_safety_result(result)
        
        assert formatted["status"] == "success"
        assert formatted["analysis"]["risk_assessment"] == "HIGH"
        assert len(formatted["findings"]["suspicious_patterns"]) == 1

    def test_research_result_formatting(self):
        """Test research result formatting."""
        context = AgentExecutionContext()
        builder = ResearchResultBuilder(context)
        
        result = builder.build_result(
            success=True,
            context_summary="Summary text",
            key_points=["Point 1", "Point 2"],
            research_question="What is X?",
            answer="X is Y",
            document_references=["Ref 1"],
            extensibility_note="Extensible"
        )
        
        formatted = FormattingEngine.format_research_result(result)
        
        assert formatted["status"] == "success"
        assert formatted["research_question"] == "What is X?"
        assert len(formatted["summary"]["key_points"]) == 2

    def test_json_lines_formatting(self):
        """Test JSON Lines formatting."""
        context = AgentExecutionContext()
        builder = EligibilityResultBuilder(context)
        
        result = builder.build_result(
            success=True,
            patient_summary="Test",
            trial_summary="Test trial",
            assessment="ELIGIBLE"
        )
        
        formatted = FormattingEngine.format_eligibility_result(result)
        json_str = FormattingEngine.format_as_json_lines(formatted)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["status"] == "success"

    def test_markdown_formatting_eligibility(self):
        """Test Markdown formatting for eligibility."""
        context = AgentExecutionContext()
        builder = EligibilityResultBuilder(context)
        
        result = builder.build_result(
            success=True,
            patient_summary="45-year-old male, hypertension",
            trial_summary="Phase II diabetes trial",
            assessment="ELIGIBLE",
            inclusion_reasoning="Age and condition match",
            exclusion_reasoning="None identified",
            recommendation="Enroll in trial",
            risk_factors=["Comorbidity"],
            evidence=["Recent labs normal"]
        )
        
        formatted = FormattingEngine.format_eligibility_result(result)
        markdown = FormattingEngine.format_as_markdown(formatted, "Eligibility Analysis")
        
        assert "# Eligibility Analysis" in markdown
        assert "Status" in markdown
        assert "Patient Summary" in markdown
        assert "ELIGIBLE" in markdown
        assert "Risk Factors" in markdown

    def test_markdown_formatting_safety(self):
        """Test Markdown formatting for safety."""
        context = AgentExecutionContext()
        builder = SafetyResultBuilder(context)
        
        result = builder.build_result(
            success=True,
            patient_summary="60-year-old male",
            safety_context="Post-op day 3",
            risk_assessment="MODERATE",
            recommendation="Close monitoring",
            suspicious_patterns=["Recurring symptoms"],
            drug_interactions=["Warfarin interaction"]
        )
        
        formatted = FormattingEngine.format_safety_result(result)
        markdown = FormattingEngine.format_as_markdown(formatted, "Safety Investigation")
        
        assert "# Safety Investigation" in markdown
        assert "Safety Context" in markdown
        assert "MODERATE" in markdown
        assert "Findings" in markdown

    def test_markdown_formatting_research(self):
        """Test Markdown formatting for research."""
        context = AgentExecutionContext()
        builder = ResearchResultBuilder(context)
        
        result = builder.build_result(
            success=True,
            context_summary="Systematic review of drug efficacy",
            key_points=["High efficacy", "Well tolerated"],
            research_question="What is the efficacy of Drug X?",
            answer="Drug X shows 75% efficacy with minimal side effects",
            document_references=["Study 1 (2023)", "Study 2 (2024)"],
            extensibility_note="Can be extended with meta-analysis"
        )
        
        formatted = FormattingEngine.format_research_result(result)
        markdown = FormattingEngine.format_as_markdown(formatted, "Research Summary")
        
        assert "# Research Summary" in markdown
        assert "Research Question" in markdown
        assert "Answer" in markdown
        assert "Key Points" in markdown
        assert "References" in markdown

    def test_markdown_with_empty_sections(self):
        """Test Markdown formatting with minimal data."""
        context = AgentExecutionContext()
        builder = EligibilityResultBuilder(context)
        
        result = builder.build_result(
            success=False,
            error="No data provided"
        )
        
        formatted = FormattingEngine.format_eligibility_result(result)
        markdown = FormattingEngine.format_as_markdown(formatted, "Test")
        
        # Should not crash and should include error
        assert "Test" in markdown
        assert "No data provided" in markdown

    def test_formatting_preserves_data_integrity(self):
        """Test that formatting preserves all data."""
        context = AgentExecutionContext()
        builder = EligibilityResultBuilder(context)
        
        original_risk_factors = ["Factor1", "Factor2", "Factor3"]
        original_evidence = ["Evidence1", "Evidence2"]
        
        result = builder.build_result(
            success=True,
            assessment="ELIGIBLE",
            risk_factors=original_risk_factors,
            evidence=original_evidence
        )
        
        formatted = FormattingEngine.format_eligibility_result(result)
        
        assert formatted["risk_factors"] == original_risk_factors
        assert formatted["evidence"] == original_evidence

    def test_markdown_formatting_with_special_characters(self):
        """Test Markdown formatting with special characters."""
        context = AgentExecutionContext()
        builder = EligibilityResultBuilder(context)
        
        result = builder.build_result(
            success=True,
            assessment="ELIGIBLE",
            inclusion_reasoning="Patient's age & medication status are suitable",
            risk_factors=["ACE inhibitor (high dose)"],
            evidence=["Using >=5 medications"]
        )
        
        formatted = FormattingEngine.format_eligibility_result(result)
        markdown = FormattingEngine.format_as_markdown(formatted)
        
        # Should handle special characters gracefully
        assert len(markdown) > 0
        assert "ELIGIBLE" in markdown


class TestFormattingIntegration:
    """Integration tests for formatting."""

    def test_full_workflow_formatting(self):
        """Test complete workflow with formatting."""
        from pharma_os.agents.impl.eligibility_agent import EligibilityAgent
        
        # Execute agent
        context = AgentExecutionContext()
        context.add_input_data("patient", {
            "age": 50,
            "gender": "M",
            "medical_history": ["diabetes"]
        })
        context.add_input_data("trial", {
            "trial_name": "Test",
            "age_range": {"min": 18, "max": 75}
        })
        
        agent = EligibilityAgent()
        result = agent.execute(context)
        
        # Format result
        formatted = FormattingEngine.format_eligibility_result(result)
        
        # Convert to JSON
        json_output = FormattingEngine.format_as_json_lines(formatted)
        
        # Convert to Markdown
        markdown_output = FormattingEngine.format_as_markdown(formatted)
        
        # Verify all outputs are valid
        assert json.loads(json_output) is not None
        assert len(markdown_output) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
