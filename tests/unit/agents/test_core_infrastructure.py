"""Tests for agent framework core infrastructure."""

import pytest
from pharma_os.agents.core.context import AgentExecutionContext
from pharma_os.agents.core.result_builders import (
    EligibilityResultBuilder,
    SafetyResultBuilder,
    ResearchResultBuilder,
)
from pharma_os.agents.core.composite_handler import CompositeAgentHandler
from pharma_os.agents.core.pipeline_manager import PipelineManager, PipelineStage
from pharma_os.agents.core.factory import AgentFactory


class TestAgentExecutionContext:
    """Tests for AgentExecutionContext."""

    def test_context_creation(self):
        """Test context initialization."""
        context = AgentExecutionContext(trace_id="test-trace-001")
        assert context.trace_id == "test-trace-001"
        assert context.get_input_data("nonexistent") is None

    def test_input_data_management(self):
        """Test input data storage and retrieval."""
        context = AgentExecutionContext()
        context.add_input_data("patient", {"name": "John", "age": 45})
        
        data = context.get_input_data("patient")
        assert data is not None
        assert data["name"] == "John"
        assert data["age"] == 45

    def test_tool_call_tracking(self):
        """Test tool call registration."""
        context = AgentExecutionContext()
        context.register_tool_call("eligibility_check")
        context.register_tool_call("risk_assessment")
        
        calls = context.get_successful_tool_calls()
        assert len(calls) == 2
        assert "eligibility_check" in calls


class TestResultBuilders:
    """Tests for result builders."""

    def test_eligibility_result_builder(self):
        """Test eligibility result building."""
        context = AgentExecutionContext()
        builder = EligibilityResultBuilder(context)
        
        result = builder.build_result(
            success=True,
            patient_summary="45-year-old male",
            trial_summary="Phase II cancer trial",
            assessment="ELIGIBLE",
            inclusion_reasoning="Meets all criteria",
            exclusion_reasoning="None identified",
            recommendation="Enroll in trial",
            risk_factors=["High comorbidity"],
            evidence=["Recent labs normal"]
        )
        
        assert result.success
        assert result.eligibility_assessment == "ELIGIBLE"
        assert len(result.risk_factors) == 1
        assert result.execution_time_ms > 0

    def test_safety_result_builder(self):
        """Test safety result building."""
        context = AgentExecutionContext()
        builder = SafetyResultBuilder(context)
        
        result = builder.build_result(
            success=True,
            patient_summary="45-year-old male",
            safety_context="Post-surgery adverse event",
            risk_assessment="HIGH",
            recommendation="Close monitoring",
            suspicious_patterns=["Recurring events"],
            recent_events=[{"type": "rash", "date": "2024-01-01"}],
            drug_interactions=["Warfarin + Aspirin"]
        )
        
        assert result.success
        assert result.risk_assessment == "HIGH"
        assert len(result.suspicious_patterns) == 1
        assert len(result.recent_events) == 1

    def test_research_result_builder(self):
        """Test research result building."""
        context = AgentExecutionContext()
        builder = ResearchResultBuilder(context)
        
        result = builder.build_result(
            success=True,
            context_summary="Systematic review of drug efficacy",
            key_points=["Drug X shows 70% efficacy", "Side effects minimal"],
            research_question="What is the efficacy of Drug X?",
            answer="Drug X shows 70% efficacy with minimal side effects",
            document_references=["Study 1 (2023)", "Study 2 (2024)"],
            extensibility_note="Framework supports multi-source integration"
        )
        
        assert result.success
        assert "Drug X" in result.answer
        assert len(result.key_points) == 2


class TestCompositeHandler:
    """Tests for composite agent handler."""

    def test_handler_initialization(self):
        """Test handler creation."""
        context = AgentExecutionContext()
        handler = CompositeAgentHandler(context)
        
        assert handler.context == context
        assert len(handler.execution_log) == 0

    def test_execution_summary(self):
        """Test execution summary generation."""
        context = AgentExecutionContext()
        handler = CompositeAgentHandler(context)
        
        # Add mock execution logs
        handler.execution_log.append({
            "agent_name": "TestAgent",
            "success": True,
            "execution_time_ms": 150.5
        })
        
        summary = handler.get_execution_summary()
        assert "TestAgent" in summary
        assert "150.5" in summary


class TestPipelineManager:
    """Tests for pipeline manager."""

    def test_pipeline_initialization(self):
        """Test pipeline creation."""
        context = AgentExecutionContext()
        manager = PipelineManager(context)
        
        assert manager.context == context
        assert manager.state.current_stage == PipelineStage.INITIALIZATION
        assert len(manager.state.completed_stages) == 0

    def test_state_summary(self):
        """Test state summary generation."""
        context = AgentExecutionContext()
        manager = PipelineManager(context)
        
        summary = manager.get_state_summary()
        assert "Pipeline State Summary" in summary
        assert "INITIALIZATION" in summary
        assert "Completed Stages: 0" in summary


class TestAgentFactory:
    """Tests for agent factory."""

    def test_agent_registration(self):
        """Test agent registration."""
        from pharma_os.agents.impl import EligibilityAgent
        
        AgentFactory.register_agent("eligibility", EligibilityAgent)
        
        assert AgentFactory.is_agent_registered("eligibility")
        assert "eligibility" in AgentFactory.list_registered_agents()

    def test_agent_creation(self):
        """Test agent creation."""
        from pharma_os.agents.impl import EligibilityAgent
        
        AgentFactory.register_agent("eligibility", EligibilityAgent)
        agent = AgentFactory.create_agent("eligibility")
        
        assert agent is not None
        assert isinstance(agent, EligibilityAgent)

    def test_singleton_instance(self):
        """Test singleton pattern."""
        from pharma_os.agents.impl import EligibilityAgent
        
        AgentFactory.register_agent("eligibility", EligibilityAgent)
        instance1 = AgentFactory.get_agent_instance("eligibility")
        instance2 = AgentFactory.get_agent_instance("eligibility")
        
        assert instance1 is instance2

    def test_unknown_agent_error(self):
        """Test error for unknown agent type."""
        with pytest.raises(ValueError):
            AgentFactory.create_agent("unknown_type")

    def test_reset_instances(self):
        """Test instance reset."""
        from pharma_os.agents.impl import EligibilityAgent
        
        AgentFactory.register_agent("eligibility", EligibilityAgent)
        AgentFactory.get_agent_instance("eligibility")
        
        AgentFactory.reset_instances()
        # After reset, new instances should be created
        AgentFactory.reset_instances()  # Should not raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
