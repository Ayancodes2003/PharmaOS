# PharmaOS Agent Framework - Phase 8.5 Enhancement

## Overview

The enhanced PharmaOS Agent Framework provides a structured, extensible system for multi-agent task execution with comprehensive orchestration, state management, and output formatting capabilities.

## Architecture

### Core Components

#### 1. AgentExecutionContext
**Location**: `pharma_os/agents/core/context.py`

Manages the execution context for agents including:
- Input data storage and retrieval
- Tool call registration and tracking
- Parent result sharing for sequential execution
- Trace ID for request correlation

**Usage**:
```python
from pharma_os.agents.core import AgentExecutionContext

context = AgentExecutionContext(trace_id="request-001")
context.add_input_data("patient", {"age": 50, "gender": "M"})
patient_data = context.get_input_data("patient")
```

#### 2. Result Builders
**Location**: `pharma_os/agents/core/result_builders.py`

Builder pattern classes for constructing agent results:
- `EligibilityResultBuilder` - For eligibility analysis results
- `SafetyResultBuilder` - For safety investigation results
- `ResearchResultBuilder` - For research summarization results

**Benefits**:
- Consistent result structure
- Execution time tracking
- Tool call logging
- Type safety

**Usage**:
```python
from pharma_os.agents.core import EligibilityResultBuilder

builder = EligibilityResultBuilder(context)
result = builder.build_result(
    success=True,
    assessment="ELIGIBLE",
    risk_factors=["Factor1"],
    evidence=["Evidence1"]
)
```

#### 3. Formatting Engine
**Location**: `pharma_os.agents/core/formatting.py`

Unified output formatting supporting:
- JSON format (for APIs and services)
- Markdown format (for human readability)
- Structured dictionaries (for programmatic access)

**Key Features**:
- Consistent formatting across output types
- Special character handling
- Data integrity preservation

**Usage**:
```python
from pharma_os.agents.core import FormattingEngine

# Format as structured dict
formatted = FormattingEngine.format_eligibility_result(result)

# Format as JSON
json_output = FormattingEngine.format_as_json_lines(formatted)

# Format as Markdown
markdown_output = FormattingEngine.format_as_markdown(
    formatted, 
    title="Clinical Eligibility Assessment"
)
```

#### 4. Composite Agent Handler
**Location**: `pharma_os/agents/core/composite_handler.py`

Orchestrates execution of multiple agents with strategies:
- Sequential execution (with or without result sharing)
- Parallel execution (simulated)
- Fallback strategies (try agents in order)

**Usage**:
```python
from pharma_os.agents.core import CompositeAgentHandler
from pharma_os.agents.impl import EligibilityAgent, SafetyAgent

handler = CompositeAgentHandler(context)
agents = [EligibilityAgent(), SafetyAgent()]
results = handler.execute_sequential(agents, share_results=True)
```

#### 5. Pipeline Manager
**Location**: `pharma_os/agents/core/pipeline_manager.py`

Manages multi-stage agent pipelines with state tracking:
- Initialization stage
- Extraction stage
- Analysis stage
- Inference stage
- Formatting stage
- Completion stage

**Features**:
- State tracking per stage
- Error handling and recovery
- Execution time tracking
- Progress reporting

**Usage**:
```python
from pharma_os.agents.core import PipelineManager, PipelineStage
from pharma_os.agents.impl import EligibilityAgent, SafetyAgent

manager = PipelineManager(context)

stages = {
    PipelineStage.ANALYSIS: ([EligibilityAgent(), SafetyAgent()], False),
    PipelineStage.FORMATTING: ([FormattingAgent()], False),
}

state = manager.execute_full_pipeline(stages)
results = manager.get_all_results()
```

#### 6. Agent Factory
**Location**: `pharma_os/agents/core/factory.py`

Factory pattern for dynamic agent creation:
- Agent type registration
- Instance creation
- Singleton pattern support
- Type validation

**Usage**:
```python
from pharma_os.agents.core import AgentFactory
from pharma_os.agents.impl import EligibilityAgent

# Register agent
AgentFactory.register_agent("eligibility", EligibilityAgent)

# Create instance
agent = AgentFactory.create_agent("eligibility")

# Get singleton
singleton = AgentFactory.get_agent_instance("eligibility")

# List available agents
available = AgentFactory.list_registered_agents()
```

### Agent Implementations

#### 1. EligibilityAgent
**Location**: `pharma_os/agents/impl/eligibility_agent.py`

Analyzes patient eligibility for clinical trials.

**Capabilities**:
- Patient profile summarization
- Trial requirement matching
- Risk factor identification
- Inclusion/exclusion reasoning
- Evidence gathering

**Data Requirements**:
```python
context.add_input_data("patient", {
    "age": 50,
    "gender": "M",
    "medical_history": ["hypertension", "diabetes"],
    "current_medications": ["lisinopril", "metformin"],
    "allergies": ["penicillin"]
})

context.add_input_data("trial", {
    "trial_name": "Drug X Study",
    "phase": "III",
    "condition": "Hypertension",
    "age_range": {"min": 18, "max": 75},
    "contraindicated_drugs": ["warfarin"]
})
```

#### 2. SafetyAgent
**Location**: `pharma_os/agents/impl/safety_agent.py`

Investigates patient safety and adverse events.

**Capabilities**:
- Risk level assessment
- Pattern detection in adverse events
- Drug interaction checking
- Safety recommendations

**Risk Levels**: LOW, MODERATE, HIGH, CRITICAL

**Data Requirements**:
```python
context.add_input_data("patient", {
    "patient_id": "P001",
    "medical_history": ["MI", "CKD"],
    "current_medications": ["warfarin", "aspirin"]
})

context.add_input_data("event", {
    "event_type": "Bleeding",
    "event_date": "2024-01-15",
    "severity": "severe",
    "event_history": [...]
})
```

#### 3. ResearchAgent
**Location**: `pharma_os/agents/impl/research_agent.py`

Summarizes and analyzes research literature.

**Capabilities**:
- Context summarization
- Key point extraction
- Research question answering
- Reference gathering
- Extensibility recommendations

**Data Requirements**:
```python
context.add_input_data("research_question", 
    "What is the efficacy of Drug X in treating condition Y?"
)

context.add_input_data("documents", [
    {
        "title": "Study 1",
        "key_findings": ["Finding 1", "Finding 2"],
        "reference": "Smith et al. 2023"
    },
    {
        "title": "Study 2",
        "summary": "...",
        "citation": "Jones et al. 2024"
    }
])
```

## Usage Patterns

### Pattern 1: Simple Single Agent Execution

```python
from pharma_os.agents.impl import EligibilityAgent
from pharma_os.agents.core import AgentExecutionContext

context = AgentExecutionContext()
context.add_input_data("patient", {...})
context.add_input_data("trial", {...})

agent = EligibilityAgent()
result = agent.execute(context)

if result.success:
    print(f"Assessment: {result.eligibility_assessment}")
else:
    print(f"Error: {result.error}")
```

### Pattern 2: Sequential Multi-Agent Workflow

```python
from pharma_os.agents.impl import EligibilityAgent, SafetyAgent
from pharma_os.agents.core import CompositeAgentHandler

context = AgentExecutionContext()
# Add data...

handler = CompositeAgentHandler(context)
agents = [EligibilityAgent(), SafetyAgent()]

results = handler.execute_sequential(agents, share_results=True)

print(handler.get_execution_summary())
```

### Pattern 3: Pipeline Execution with Formatting

```python
from pharma_os.agents.core import PipelineManager, PipelineStage, FormattingEngine
from pharma_os.agents.impl import EligibilityAgent

manager = PipelineManager(context)

stages = {
    PipelineStage.ANALYSIS: ([EligibilityAgent()], False),
}

state = manager.execute_full_pipeline(stages)
analysis_results = manager.get_stage_result(PipelineStage.ANALYSIS)

# Format output
if analysis_results:
    formatted = FormattingEngine.format_eligibility_result(analysis_results[0])
    markdown = FormattingEngine.format_as_markdown(formatted)
    print(markdown)
```

### Pattern 4: Fallback Strategy

```python
from pharma_os.agents.core import CompositeAgentHandler
from pharma_os.agents.impl import EligibilityAgent, SafetyAgent

handler = CompositeAgentHandler(context)

# Try agents in priority order
primary = EligibilityAgent()
fallback = SafetyAgent()

result = handler.execute_fallback([primary, fallback])
if result and result.success:
    print("Analysis completed")
```

### Pattern 5: Factory-Based Agent Creation

```python
from pharma_os.agents.core import AgentFactory
from pharma_os.agents.impl import EligibilityAgent, SafetyAgent, ResearchAgent

# Register agents
AgentFactory.register_agent("eligibility", EligibilityAgent)
AgentFactory.register_agent("safety", SafetyAgent)
AgentFactory.register_agent("research", ResearchAgent)

# Create agents dynamically
context_type = "patient_eligibility"
if context_type == "patient_eligibility":
    agent = AgentFactory.create_agent("eligibility")

result = agent.execute(context)
```

## Best Practices

### 1. Context Management
- Always create a new `AgentExecutionContext` per request
- Use unique trace IDs for correlation
- Clear sensitive data from context after use

### 2. Error Handling
```python
try:
    result = agent.execute(context)
    if not result.success:
        logger.error(f"Agent failed: {result.error}")
        # Handle failure
    else:
        # Process result
except Exception as e:
    logger.error(f"Execution error: {str(e)}", exc_info=True)
```

### 3. Result Validation
```python
if result.success and result.execution_time_ms < 5000:
    # Use result
    formatted = FormattingEngine.format_eligibility_result(result)
else:
    # Handle timeout or failure
```

### 4. Output Formatting
- Use JSON for APIs and service-to-service communication
- Use Markdown for human-readable reports
- Use structured dicts for programmatic processing

### 5. agent Composition
- Start simple with single agents
- Build up to pipelines as complexity increases
- Use CompositeHandler for coordination
- Monitor execution times and success rates

## Testing

### Running Tests

```bash
# Run all infrastructure tests
pytest tests/unit/agents/test_core_infrastructure.py -v

# Run agent implementation tests
pytest tests/unit/agents/test_agent_implementations.py -v

# Run formatting tests
pytest tests/unit/agents/test_formatting.py -v

# Run all agent tests
pytest tests/unit/agents/ -v
```

### Writing Custom Tests

```python
import pytest
from pharma_os.agents.impl import CustomAgent
from pharma_os.agents.core import AgentExecutionContext

class TestCustomAgent:
    def test_custom_execution(self):
        context = AgentExecutionContext()
        context.add_input_data("key", {"data": "value"})
        
        agent = CustomAgent()
        result = agent.execute(context)
        
        assert result.success
        assert result.execution_time_ms > 0
```

## Future Enhancements

### Planned Features
1. Async agent execution
2. Agent caching and memoization
3. Advanced logging and telemetry
4. Result persistence and versioning
5. Agent performance metrics
6. Custom agent base classes
7. Workflow templates
8. Result streaming

### Extension Points
- Custom result builders
- Custom formatters
- Agent-specific orchestration logic
- Result aggregation strategies
- Error recovery mechanisms

## Troubleshooting

### Issue: Agent returns False success with no error message
**Solution**: Check that all required input data is present in context

### Issue: Formatting produces empty sections
**Solution**: Ensure result builders are called with appropriate data

### Issue: Pipeline stages not executing in order
**Solution**: Verify stage dependencies and error handling configuration

### Issue: Factory unable to create registered agent
**Solution**: Ensure agent is properly registered before creation

## References

- [Agent Base Class](pharma_os/agents/base.py)
- [Core Infrastructure](pharma_os/agents/core/)
- [Agent Implementations](pharma_os/agents/impl/)
- [Tests](tests/unit/agents/)
