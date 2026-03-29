# Agent Framework Integration Guide

## Overview

This guide explains how to integrate the new Phase 8.5 Agent Framework with existing PharmaOS components and how to migrate existing code to use the enhanced framework.

## Architecture Context

```
PharmaOS
├── pharma_os/agents/
│   ├── [Existing Phase 8 Implementation]
│   │   ├── base.py (BaseAgent, ExecutionContext, etc.)
│   │   ├── eligibility_analyst.py
│   │   ├── safety_investigator.py
│   │   ├── research_summarizer.py
│   │   └── orchestration.py
│   │
│   └── [NEW Phase 8.5 Enhancement]
│       ├── core/
│       │   ├── context.py (new execution context)
│       │   ├── result_builders.py
│       │   ├── formatting.py
│       │   ├── composite_handler.py
│       │   ├── pipeline_manager.py
│       │   └── factory.py
│       │
│       └── impl/
│           ├── eligibility_agent.py
│           ├── safety_agent.py
│           └── research_agent.py
```

## Migration Patterns

### Pattern 1: Wrap Existing Agents

If you have existing agent implementations, wrap them to use the new framework:

```python
from pharma_os.agents.base import BaseAgent as ExistingBaseAgent
from pharma_os.agents.core import AgentExecutionContext
from pharma_os.agents.impl import EligibilityAgent as NewEligibilityAgent

class LegacyEligibilityWrapper(NewEligibilityAgent):
    """Adapter for existing eligibility agent."""
    
    def __init__(self):
        super().__init__()
        self._legacy_agent = ExistingBaseAgent()
    
    def execute(self, context: AgentExecutionContext):
        """Execute with new framework."""
        # Convert new context to legacy format if needed
        legacy_result = self._legacy_agent.execute(...)
        
        # Convert result back to new framework format
        builder = EligibilityResultBuilder(context)
        return builder.build_result(
            success=legacy_result.success,
            assessment=legacy_result.assessment,
            # ... map other fields
        )
```

### Pattern 2: Parallel Implementation

Use both frameworks in parallel:

```python
from pharma_os.agents.impl import EligibilityAgent
from pharma_os.agents.core import AgentExecutionContext, FormattingEngine

# Old way (continue to work)
legacy_result = legacy_agent.execute(legacy_context)

# New way (alongside old)
context = AgentExecutionContext()
context.add_input_data("patient", patient_data)
context.add_input_data("trial", trial_data)

agent = EligibilityAgent()
result = agent.execute(context)

# Format with new framework
formatted = FormattingEngine.format_eligibility_result(result)
```

### Pattern 3: Gradual Migration

Migrate components incrementally:

**Phase 1: Extract Data Layer**
```python
# Move data into new context format
legacy_data = get_legacy_data()
context = AgentExecutionContext()
context.add_input_data("patient", extract_patient(legacy_data))
context.add_input_data("trial", extract_trial(legacy_data))

# Execute with new agent
agent = EligibilityAgent()
result = agent.execute(context)

# Convert result back for compatibility
legacy_result = convert_to_legacy_format(result)
```

**Phase 2: Update APIs**
```python
# Update endpoint to return new format
@app.route('/eligibility')
def eligibility_check():
    # Use new framework internally
    result = new_agent.execute(context)
    
    # Return new format
    formatted = FormattingEngine.format_eligibility_result(result)
    return json.dumps(FormattingEngine.format_as_json_lines(formatted))
```

**Phase 3: Retire Legacy Code**
After testing, remove legacy implementation.

## Integration Examples

### Example 1: REST API Integration

```python
from flask import Flask, request, jsonify
from pharma_os.agents.impl import EligibilityAgent
from pharma_os.agents.core import AgentExecutionContext, FormattingEngine

app = Flask(__name__)

@app.route('/api/v2/eligibility-check', methods=['POST'])
def eligibility_check():
    """New endpoint using Phase 8.5 framework."""
    
    data = request.json
    context = AgentExecutionContext(trace_id=data.get('trace_id'))
    
    context.add_input_data("patient", data.get('patient'))
    context.add_input_data("trial", data.get('trial'))
    
    agent = EligibilityAgent()
    result = agent.execute(context)
    
    formatted = FormattingEngine.format_eligibility_result(result)
    return jsonify(formatted), 200 if result.success else 400
```

### Example 2: Batch Processing

```python
from pharma_os.agents.impl import EligibilityAgent, SafetyAgent
from pharma_os.agents.core import CompositeAgentHandler, AgentExecutionContext

def process_patient_batch(patients: list[dict], trial: dict):
    """Process multiple patients."""
    
    results = []
    
    for patient in patients:
        context = AgentExecutionContext()
        context.add_input_data("patient", patient)
        context.add_input_data("trial", trial)
        
        handler = CompositeAgentHandler(context)
        agents = [EligibilityAgent(), SafetyAgent()]
        
        batch_results = handler.execute_sequential(agents, share_results=True)
        results.append(batch_results)
    
    return results
```

### Example 3: CLI Integration

```python
import click
from pharma_os.agents.impl import ResearchAgent
from pharma_os.agents.core import AgentExecutionContext, FormattingEngine

@click.command()
@click.option('--question', required=True, help='Research question')
@click.option('--format', type=click.Choice(['json', 'markdown']), default='markdown')
def research_analyze(question: str, format: str):
    """Analyze research literature."""
    
    context = AgentExecutionContext()
    context.add_input_data("research_question", question)
    context.add_input_data("documents", load_documents())
    
    agent = ResearchAgent()
    result = agent.execute(context)
    
    formatted = FormattingEngine.format_research_result(result)
    
    if format == 'json':
        output = FormattingEngine.format_as_json_lines(formatted)
    else:
        output = FormattingEngine.format_as_markdown(formatted)
    
    click.echo(output)

if __name__ == '__main__':
    research_analyze()
```

## Data Model Mapping

### Patient Data
```python
# Legacy format
legacy_patient = {
    'patient_id': 'P001',
    'demographics': {'age': 50, 'gender': 'M'},
    'clinical': {'conditions': [...], 'medications': [...]}
}

# New format
patient_data = {
    'age': legacy_patient['demographics']['age'],
    'gender': legacy_patient['demographics']['gender'],
    'medical_history': legacy_patient['clinical']['conditions'],
    'current_medications': legacy_patient['clinical']['medications']
}

context.add_input_data("patient", patient_data)
```

### Trial Data
```python
# Legacy format
legacy_trial = {
    'nct_id': 'NCT03000123',
    'summary': {'name': '...', 'phase': 'III'},
    'criteria': {'inclusion': [...], 'exclusion': [...]}
}

# New format
trial_data = {
    'trial_name': legacy_trial['summary']['name'],
    'phase': legacy_trial['summary']['phase'],
    'inclusion_criteria': legacy_trial['criteria']['inclusion'],
    'exclusion_criteria': legacy_trial['criteria']['exclusion'],
    'age_range': {'min': 18, 'max': 75}
}

context.add_input_data("trial", trial_data)
```

## Compatibility Matrix

| Component | Legacy Code | New Framework | Co-exist |
|-----------|-------------|---------------|----------|
| Data Models | Yes | Yes | With mapping |
| Agents | Yes | Yes | Via wrapper |
| Orchestration | Yes | Yes | Via adapter |
| Output | Varies | JSON/Markdown | Formatters |
| Testing | Yes | Yes | Parallel |

## Performance Considerations

### Execution Time
- New framework overhead: ~5-10ms per agent
- Result building: ~1-2ms per result
- Formatting: ~5-15ms per result (depends on size)

### Memory
- Context per request: ~5KB
- Result builders: ~2KB each
- Format output: ~10-50KB (depends on data size)

## Testing Strategy

### Unit Tests
```bash
# Test new framework independently
pytest tests/unit/agents/test_core_infrastructure.py -v
pytest tests/unit/agents/test_agent_implementations.py -v
pytest tests/unit/agents/test_formatting.py -v
```

### Integration Tests
```bash
# Test alongside legacy code
pytest tests/integration/agents/ -v
```

### Regression Tests
```bash
# Ensure legacy functionality still works
pytest tests/legacy/agents/ -v
```

## Configuration

### Framework Configuration

```python
from pharma_os.agents.core import AgentFactory

# Optional: Configure factory
class FrameworkConfig:
    TRACE_ENABLED = True
    LOGGING_LEVEL = "INFO"
    MAX_EXECUTION_TIME_MS = 5000
    ENABLE_RESULT_CACHING = False
```

### Agent Configuration

```python
# Custom agent initialization
from pharma_os.agents.impl import EligibilityAgent

class CustomEligibilityAgent(EligibilityAgent):
    def __init__(self, rules_engine=None):
        super().__init__()
        self.rules_engine = rules_engine
```

## Troubleshooting

### Issue: Legacy interface incompatibility
**Solution**: Use wrapper adapter pattern

### Issue: Data format mismatch
**Solution**: Create converter functions between formats

### Issue: Test failures
**Solution**: Ensure dependencies are installed, run tests with verbose output

### Issue: Performance degradation
**Solution**: Profile with timing, check execution time metrics

## Rollback Plan

If issues arise during integration:

1. **Immediate**: Continue using existing agents
2. **Short-term**: Use wrapper adapters for gradual migration
3. **Long-term**: File issues and iterate on framework

## Timeline

### Phase 1: Evaluation (Week 1)
- Review framework
- Test with sample data
- Plan migration strategy

### Phase 2: Integration (Week 2-3)
- Implement adapters/wrappers
- Run parallel tests
- Update documentation

### Phase 3: Migration (Week 4+)
- Gradually move to new framework
- Monitor performance
- Retire legacy code

## Support Resources

- **Documentation**: AGENT_FRAMEWORK.md
- **Examples**: examples/agent_framework_usage.py
- **Tests**: tests/unit/agents/
- **API Reference**: Inline docstrings

## Best Practices

1. ✅ Use type hints consistently
2. ✅ Validate input data before passing to agents
3. ✅ Log execution with trace IDs
4. ✅ Format output appropriately for consumers
5. ✅ Handle errors gracefully
6. ✅ Monitor execution performance
7. ✅ Keep legacy and new code separate initially
8. ✅ Test thoroughly before switching over
