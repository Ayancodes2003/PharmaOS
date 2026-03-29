"""Example usage of the PharmaOS Agent Framework.

This module demonstrates various patterns for using the enhanced agent framework.
"""

from pharma_os.agents.impl import EligibilityAgent, SafetyAgent, ResearchAgent
from pharma_os.agents.core import (
    AgentExecutionContext,
    CompositeAgentHandler,
    PipelineManager,
    PipelineStage,
    FormattingEngine,
    AgentFactory,
)


def example_1_simple_eligibility_check():
    """Example 1: Simple eligibility check for a single patient."""
    print("\n" + "=" * 60)
    print("Example 1: Simple Eligibility Check")
    print("=" * 60)
    
    # Create execution context
    context = AgentExecutionContext(trace_id="example-001")
    
    # Add patient data
    context.add_input_data("patient", {
        "age": 52,
        "gender": "F",
        "medical_history": ["type_2_diabetes", "hypertension"],
        "current_medications": ["metformin", "lisinopril"],
        "allergies": []
    })
    
    # Add trial data
    context.add_input_data("trial", {
        "trial_name": "CARDIOVASCULAR OUTCOMES STUDY",
        "phase": "III",
        "condition": "Type 2 Diabetes with Hypertension",
        "age_range": {"min": 18, "max": 75},
        "contraindicated_drugs": ["warfarin"]
    })
    
    # Execute agent
    agent = EligibilityAgent()
    result = agent.execute(context)
    
    if result.success:
        print(f"\nTrial Eligibility Assessment")
        print(f"-" * 40)
        print(f"Status: {result.eligibility_assessment}")
        print(f"Patient Summary: {result.patient_summary}")
        print(f"Recommendation: {result.recommendation}")
        print(f"Risk Factors: {', '.join(result.risk_factors)}")
        print(f"Execution Time: {result.execution_time_ms:.2f}ms")
    else:
        print(f"Error: {result.error}")


def example_2_safety_investigation():
    """Example 2: Safety investigation for adverse event."""
    print("\n" + "=" * 60)
    print("Example 2: Safety Investigation")
    print("=" * 60)
    
    # Create execution context
    context = AgentExecutionContext(trace_id="example-002")
    
    # Add patient data
    context.add_input_data("patient", {
        "patient_id": "PT-2024-001",
        "age": 68,
        "gender": "M",
        "medical_history": ["history_of_MI", "chronic_kidney_disease"],
        "current_medications": ["atorvastatin", "lisinopril", "metoprolol", "aspirin"],
        "allergies": ["NSAID"]
    })
    
    # Add adverse event data
    context.add_input_data("event", {
        "event_type": "Unexplained bleeding",
        "event_date": "2024-01-20",
        "severity": "severe",
        "event_history": [
            {"type": "minor_bleeding", "date": "2024-01-15"},
            {"type": "bruising", "date": "2024-01-10"}
        ]
    })
    
    # Execute agent
    agent = SafetyAgent()
    result = agent.execute(context)
    
    if result.success:
        print(f"\nSafety Investigation Report")
        print(f"-" * 40)
        print(f"Risk Level: {result.risk_assessment}")
        print(f"Patient: {result.patient_summary}")
        print(f"Recommendation: {result.recommendation}")
        print(f"Suspicious Patterns: {', '.join(result.suspicious_patterns)}")
        print(f"Drug Interactions: {', '.join(result.drug_interaction_concerns)}")
        print(f"Execution Time: {result.execution_time_ms:.2f}ms")
    else:
        print(f"Error: {result.error}")


def example_3_research_analysis():
    """Example 3: Research literature analysis."""
    print("\n" + "=" * 60)
    print("Example 3: Research Literature Analysis")
    print("=" * 60)
    
    # Create execution context
    context = AgentExecutionContext(trace_id="example-003")
    
    # Add research query
    context.add_input_data("research_question",
        "What is the long-term efficacy and safety profile of Drug X in treating Condition Y?"
    )
    
    # Add research documents
    context.add_input_data("documents", [
        {
            "title": "Efficacy of Drug X: A 5-Year Randomized Controlled Trial",
            "key_findings": [
                "Drug X achieves 78% remission rate",
                "Superior to standard therapy (p<0.01)",
                "Well tolerated with minimal adverse events"
            ],
            "source": "Clinical Medicine Journal, 2023"
        },
        {
            "title": "Long-term Safety Profile of Drug X: Extended Follow-up Study",
            "key_findings": [
                "No long-term organ toxicity identified",
                "Quality of life scores remain stable",
                "Discontinuation rate < 5%"
            ],
            "source": "Patient Outcomes Review, 2024"
        }
    ])
    
    # Execute agent
    agent = ResearchAgent()
    result = agent.execute(context)
    
    if result.success:
        print(f"\nResearch Summary Report")
        print(f"-" * 40)
        print(f"Question: {result.research_question}")
        print(f"Answer: {result.answer}")
        print(f"\nKey Points:")
        for point in result.key_points:
            print(f"  • {point}")
        print(f"Execution Time: {result.execution_time_ms:.2f}ms")
    else:
        print(f"Error: {result.error}")


def example_4_sequential_workflow():
    """Example 4: Sequential execution of eligibility and safety agents."""
    print("\n" + "=" * 60)
    print("Example 4: Sequential Workflow (Eligibility + Safety)")
    print("=" * 60)
    
    # Create execution context
    context = AgentExecutionContext(trace_id="example-004")
    
    # Add patient data
    context.add_input_data("patient", {
        "age": 55,
        "gender": "M",
        "medical_history": ["hypertension"],
        "current_medications": ["lisinopril"],
        "allergies": []
    })
    
    # Add trial data
    context.add_input_data("trial", {
        "trial_name": "ANTIHYPERTENSIVE EFFICACY STUDY",
        "age_range": {"min": 18, "max": 75},
        "contraindicated_drugs": []
    })
    
    # Add event data
    context.add_input_data("event", {
        "event_type": "Mild dizziness",
        "severity": "mild"
    })
    
    # Create handler
    handler = CompositeAgentHandler(context)
    agents = [EligibilityAgent(), SafetyAgent()]
    
    # Execute sequentially
    results = handler.execute_sequential(agents, share_results=True)
    
    print(f"\nSequential Execution Results")
    print(f"-" * 40)
    print(handler.get_execution_summary())
    
    for i, result in enumerate(results, 1):
        print(f"\nAgent {i}: {'Success' if result.success else 'Failed'}")
        if i == 1:  # Eligibility
            print(f"  Assessment: {result.eligibility_assessment}")
        elif i == 2:  # Safety
            print(f"  Risk Level: {result.risk_assessment}")


def example_5_pipeline_with_formatting():
    """Example 5: Pipeline execution with output formatting."""
    print("\n" + "=" * 60)
    print("Example 5: Pipeline with Output Formatting")
    print("=" * 60)
    
    # Create execution context
    context = AgentExecutionContext(trace_id="example-005")
    
    # Add data
    context.add_input_data("patient", {
        "age": 60,
        "gender": "F",
        "medical_history": ["osteoarthritis"],
        "current_medications": ["acetaminophen"]
    })
    
    context.add_input_data("trial", {
        "trial_name": "PAIN MANAGEMENT STUDY",
        "age_range": {"min": 18, "max": 75}
    })
    
    # Create pipeline
    manager = PipelineManager(context)
    
    stages = {
        PipelineStage.ANALYSIS: ([EligibilityAgent()], False),
    }
    
    state = manager.execute_full_pipeline(stages)
    
    # Get and format results
    analysis_results = manager.get_stage_result(PipelineStage.ANALYSIS)
    
    print(f"\nPipeline State Summary")
    print(f"-" * 40)
    print(manager.get_state_summary())
    
    if analysis_results and analysis_results[0].success:
        # Format as JSON
        formatted = FormattingEngine.format_eligibility_result(analysis_results[0])
        print(f"\nFormatted Result (truncated):")
        print(f"  Status: {formatted['status']}")
        print(f"  Assessment: {formatted['assessment']['eligibility']}")
        
        # Show Markdown preview
        markdown = FormattingEngine.format_as_markdown(formatted)
        print(f"\nMarkdown output generated ({len(markdown)} chars)")


def example_6_factory_pattern():
    """Example 6: Using factory pattern for agent creation."""
    print("\n" + "=" * 60)
    print("Example 6: Factory Pattern for Agent Creation")
    print("=" * 60)
    
    # Register agents
    AgentFactory.register_agent("eligibility", EligibilityAgent)
    AgentFactory.register_agent("safety", SafetyAgent)
    AgentFactory.register_agent("research", ResearchAgent)
    
    print(f"\nRegistered Agents:")
    for agent_type in AgentFactory.list_registered_agents():
        print(f"  • {agent_type}")
    
    # Create context
    context = AgentExecutionContext()
    context.add_input_data("patient", {
        "age": 50,
        "gender": "M"
    })
    context.add_input_data("trial", {
        "trial_name": "TEST TRIAL"
    })
    
    # Dynamically create and execute agent
    print(f"\nDynamically creating and executing EligibilityAgent...")
    agent = AgentFactory.create_agent("eligibility")
    result = agent.execute(context)
    
    print(f"Result: {'Success' if result.success else 'Failed'}")
    if result.success:
        print(f"Assessment: {result.eligibility_assessment}")


def example_7_error_handling():
    """Example 7: Error handling patterns."""
    print("\n" + "=" * 60)
    print("Example 7: Error Handling Patterns")
    print("=" * 60)
    
    # Case 1: Missing required data
    print(f"\nCase 1: Missing patient data")
    context = AgentExecutionContext()
    # Don't add patient data
    context.add_input_data("trial", {"trial_name": "TEST"})
    
    agent = EligibilityAgent()
    result = agent.execute(context)
    
    if not result.success:
        print(f"  Expected Error: {result.error}")
    
    # Case 2: Valid execution
    print(f"\nCase 2: Valid execution with required data")
    context = AgentExecutionContext()
    context.add_input_data("patient", {"age": 50, "gender": "M"})
    context.add_input_data("trial", {"trial_name": "TEST"})
    
    result = agent.execute(context)
    print(f"  Status: {'Success' if result.success else 'Failed'}")
    
    if result.success:
        print(f"  Assessment: {result.eligibility_assessment}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("PharmaOS Agent Framework - Example Usage")
    print("=" * 60)
    
    example_1_simple_eligibility_check()
    example_2_safety_investigation()
    example_3_research_analysis()
    example_4_sequential_workflow()
    example_5_pipeline_with_formatting()
    example_6_factory_pattern()
    example_7_error_handling()
    
    print("\n" + "=" * 60)
    print("Examples Completed")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
