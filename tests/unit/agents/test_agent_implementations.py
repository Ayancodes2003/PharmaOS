"""Tests for agent implementations."""

import pytest
from pharma_os.agents.core.context import AgentExecutionContext
from pharma_os.agents.impl.eligibility_agent import EligibilityAgent
from pharma_os.agents.impl.safety_agent import SafetyAgent
from pharma_os.agents.impl.research_agent import ResearchAgent


class TestEligibilityAgent:
    """Tests for eligibility assessment agent."""

    def test_agent_initialization(self):
        """Test agent creation."""
        agent = EligibilityAgent()
        assert agent.agent_type == "eligibility_assessment"

    def test_eligibility_execution_success(self):
        """Test successful eligibility assessment."""
        agent = EligibilityAgent()
        context = AgentExecutionContext()
        
        # Add test data
        context.add_input_data("patient", {
            "age": 45,
            "gender": "M",
            "medical_history": ["hypertension"],
            "current_medications": ["lisinopril"],
            "allergies": ["penicillin"]
        })
        
        context.add_input_data("trial", {
            "trial_name": "COVID-19 Treatment Study",
            "phase": "II",
            "condition": "COVID-19",
            "age_range": {"min": 18, "max": 75},
            "contraindicated_drugs": ["warfarin"]
        })
        
        result = agent.execute(context)
        
        assert result.success
        assert result.eligibility_assessment in ["ELIGIBLE", "NOT ELIGIBLE"]
        assert len(result.patient_summary) > 0
        assert len(result.trial_summary) > 0

    def test_eligibility_missing_patient_data(self):
        """Test handling of missing patient data."""
        agent = EligibilityAgent()
        context = AgentExecutionContext()
        
        # Only add trial data
        context.add_input_data("trial", {"trial_name": "Test Trial"})
        
        result = agent.execute(context)
        
        assert not result.success
        assert "No patient data" in result.error

    def test_patient_summary_generation(self):
        """Test patient summary generation."""
        agent = EligibilityAgent()
        patient_data = {
            "age": 50,
            "gender": "F",
            "medical_history": ["diabetes", "hypertension"]
        }
        
        summary = agent._summarize_patient(patient_data)
        
        assert "50" in summary
        assert "F" in summary
        assert "diabetes" in summary

    def test_risk_factor_identification(self):
        """Test risk factor identification."""
        agent = EligibilityAgent()
        
        patient_data = {
            "medical_history": ["diabetes", "hypertension", "asthma"],
            "current_medications": ["metformin", "lisinopril", "albuterol", "atorvastatin", "aspirin", "omeprazole"],
            "allergies": ["penicillin", "sulfa"]
        }
        trial_data = {}
        
        risk_factors = agent._identify_risk_factors(patient_data, trial_data)
        
        assert len(risk_factors) > 0
        assert any("comorbidities" in rf.lower() for rf in risk_factors)


class TestSafetyAgent:
    """Tests for safety investigation agent."""

    def test_agent_initialization(self):
        """Test agent creation."""
        agent = SafetyAgent()
        assert agent.agent_type == "safety_investigation"

    def test_safety_execution_success(self):
        """Test successful safety investigation."""
        agent = SafetyAgent()
        context = AgentExecutionContext()
        
        # Add test data
        context.add_input_data("patient", {
            "patient_id": "P001",
            "age": 60,
            "gender": "M",
            "medical_history": ["MI", "HFpEF"],
            "current_medications": ["atorvastatin", "lisinopril", "metoprolol"],
            "allergies": []
        })
        
        context.add_input_data("event", {
            "event_type": "Chest pain",
            "event_date": "2024-01-15",
            "severity": "moderate"
        })
        
        result = agent.execute(context)
        
        assert result.success
        assert result.risk_assessment in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
        assert result.recommendation is not None

    def test_risk_assessment_scoring(self):
        """Test risk scoring logic."""
        agent = SafetyAgent()
        
        patient_data = {
            "medical_history": ["diabetes", "CAD", "CKD", "HFpEF"],
            "current_medications": ["med1", "med2", "med3", "med4", "med5", "med6"],
            "allergies": ["penicillin"]
        }
        
        event_data = {"severity": "severe"}
        
        risk = agent._assess_risk(patient_data, event_data)
        
        assert risk in ["LOW", "MODERATE", "HIGH", "CRITICAL"]

    def test_pattern_detection(self):
        """Test suspicious pattern detection."""
        agent = SafetyAgent()
        
        patient_data = {
            "current_medications": ["warfarin", "aspirin", "ibuprofen"]
        }
        
        event_data = {
            "event_history": [
                {"type": "bleeding", "date": "2024-01-01"},
                {"type": "bleeding", "date": "2024-01-08"},
                {"type": "bleeding", "date": "2024-01-15"}
            ]
        }
        
        patterns = agent._identify_patterns(patient_data, event_data)
        
        assert len(patterns) > 0

    def test_drug_interaction_checking(self):
        """Test drug interaction detection."""
        agent = SafetyAgent()
        
        patient_data = {
            "current_medications": ["warfarin", "aspirin", "tramadol", "sertraline"]
        }
        
        interactions = agent._check_drug_interactions(patient_data)
        
        assert len(interactions) > 0


class TestResearchAgent:
    """Tests for research summarization agent."""

    def test_agent_initialization(self):
        """Test agent creation."""
        agent = ResearchAgent()
        assert agent.agent_type == "research_summarization"

    def test_research_execution_success(self):
        """Test successful research analysis."""
        agent = ResearchAgent()
        context = AgentExecutionContext()
        
        # Add test data
        context.add_input_data("research_question", "What is the efficacy of Drug X in treating condition Y?")
        context.add_input_data("documents", [
            {
                "title": "Efficacy of Drug X: A Randomized Controlled Trial",
                "key_findings": ["Drug X shows 75% efficacy", "Well tolerated"]
            },
            {
                "title": "Long-term Safety Profile of Drug X",
                "key_findings": ["No long-term side effects identified"]
            }
        ])
        
        result = agent.execute(context)
        
        assert result.success
        assert result.research_question is not None
        assert len(result.key_points) > 0
        assert result.answer is not None

    def test_key_point_extraction(self):
        """Test key point extraction."""
        agent = ResearchAgent()
        
        documents = [
            {"key_findings": ["Finding 1", "Finding 2"]},
            {"summary": "This is a summary"}
        ]
        
        key_points = agent._extract_key_points(documents)
        
        assert len(key_points) > 0

    def test_reference_gathering(self):
        """Test reference gathering."""
        agent = ResearchAgent()
        
        documents = [
            {"title": "Study 1"},
            {"title": "Study 2"},
            {"citation": "Smith et al. 2023"}
        ]
        
        references = agent._gather_references(documents)
        
        assert len(references) > 0

    def test_extensibility_note_generation(self):
        """Test extensibility note generation."""
        agent = ResearchAgent()
        
        question = "What is the mortality benefit of drug X?"
        note = agent._generate_extensibility_note(question)
        
        assert "extensibility" in note.lower() or "extend" in note.lower()
        assert len(note) > 50


class TestAgentIntegration:
    """Integration tests across multiple agents."""

    def test_sequential_agent_execution(self):
        """Test executing agents sequentially."""
        context = AgentExecutionContext()
        
        # Prepare data for both agents
        context.add_input_data("patient", {
            "age": 50,
            "gender": "M",
            "medical_history": ["hypertension"],
            "current_medications": ["lisinopril"]
        })
        context.add_input_data("trial", {
            "trial_name": "Test Trial",
            "age_range": {"min": 18, "max": 75}
        })
        context.add_input_data("event", {
            "event_type": "Mild headache",
            "severity": "mild"
        })
        
        # Execute eligibility agent
        eligibility_agent = EligibilityAgent()
        eligibility_result = eligibility_agent.execute(context)
        assert eligibility_result.success
        
        # Execute safety agent
        safety_agent = SafetyAgent()
        safety_result = safety_agent.execute(context)
        assert safety_result.success

    def test_error_handling_across_agents(self):
        """Test error handling when data is missing."""
        context = AgentExecutionContext()
        
        # Don't add any data
        agent = EligibilityAgent()
        result = agent.execute(context)
        
        assert not result.success
        assert result.error is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
