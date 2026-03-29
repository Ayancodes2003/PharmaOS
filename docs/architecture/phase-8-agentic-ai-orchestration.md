"""Phase 8: Agentic AI Orchestration Layer

PHARMA-OS Phase 8 implements a production-grade multi-agent AI subsystem enabling
role-specific clinical workflow assistance without generic chatbot patterns or hallucination.

==================================================
OVERVIEW
==================================================

Phase 8 provides three specialized agents operating on top of PHARMA-OS data,
prediction services, and document context:

1. Trial Eligibility Analyst Agent
   - Analyzes patient-trial fit
   - Incorporates patient profile, trial criteria, adverse events, drug exposures
   - Produces structured analysis with inclusion/exclusion reasoning
   - Outputs: patient/trial summary, eligibility assessment, recommendation, risk factors

2. Safety Signal Investigator Agent
   - Analyzes patient safety context and adverse event patterns
   - Incorporates adverse event history, drug exposures, safety predictions
   - Identifies suspicious patterns and risk factors
   - Outputs: safety context, risk assessment, drug interactions

3. Research Summarization Agent
   - Summarizes trial information, criteria, and research context
   - Answers structured research questions grounded in data
   - Extensible for RAG integration and literature retrieval
   - Outputs: context summary, key points, research question/answer

==================================================
ARCHITECTURE
==================================================

Phase 8 follows a clean, modular architecture with separated concerns:

### Base Abstractions (agents/base/)
- agent.py: BaseAgent interface and ExecutionContext
- contracts.py: Request/response Pydantic models for all agents (AgentRequest, AgentResult, etc.)
- tools.py: Tool base class and ToolRegistry for agent-callable tools
- trace.py: AgentTraceRecord and AgentMemoryRecord for MongoDB persistence

### LLM Provider Layer (agents/llm/)
- provider.py: Abstract LLMProvider interface (provider-agnostic)
- openai_client.py: OpenAI-compatible provider (async, httpx-based)
- stub.py: StubLLMProvider for no-key environments (returns deterministic, grounded placeholders)
- __init__.py: Provider factory (create_llm_provider)

Purpose: Enable provider swapping, fallback stub mode, and no-key execution.

### Prompt Registry (agents/prompts/)
- registry.py: PromptRegistry for organized, loadable prompts
- Prompts stored as markdown files or registered programmatically
- Avoids hardcoded prompt strings in business logic

Purpose: Keep prompts maintainable and separated from agent code.

### Tool Abstractions (agents/tools/)
- base.py: Six concrete tool implementations
  - PatientLookupTool: Retrieve patient profile (demographics, condition, enrollment)
  - TrialLookupTool: Retrieve trial information (title, phase, status, criteria refs)
  - AdverseEventLookupTool: Retrieve adverse event history
  - DrugExposureLookupTool: Retrieve drug exposure history
  - PredictionLookupTool: Retrieve eligibility/safety/recruitment predictions
  - DocumentRetrievalTool: Retrieve trial criteria, literature (RAG-ready stub)
- __init__.py: ToolRegistry initialization and registration

Purpose: Ground agents in real data via existing repositories, avoid hallucination.

### Specific Agents (agents/)
- eligibility_analyst.py: EligibilityAnalystAgent implementation
  - Queries patient and trial data
  - Analyzes against trial criteria
  - Produces structured eligibility output with reasoning
  - Methods: _summarize_patient, _extract_inclusion/exclusion_reasoning, _identify_risk_factors

- safety_investigator.py: SafetyInvestigatorAgent implementation
  - Queries adverse event history and drug exposures
  - Identifies suspicious patterns and drug interactions
  - Produces structured safety assessment
  - Methods: _extract_recent_events, _identify_suspicious_patterns, _identify_drug_interactions

- research_summarizer.py: ResearchSummarizerAgent implementation
  - Retrieves trial information, documents, or literature
  - Summarizes context and answers research questions
  - Extensible for RAG integration
  - Methods: _summarize_trial_context, _summarize_literature_context, _extract_key_points

### Orchestration Layer (agents/orchestration/)
- dispatcher.py: AgentDispatcher and AgentExecutor
  - AgentDispatcher: Routes requests to correct agent, manages initialization
  - AgentExecutor: Executes requests with trace persistence
  - Deterministic routing, no agent confusion

Purpose: Clean request handling, trace collection, orchestration control.

### Trace Persistence (agents/persistence/)
- trace_store.py: TraceStore class for MongoDB persistence
  - persist_trace(): Saves agent trace with metadata
  - retrieve_trace(): Retrieves single trace
  - list_traces(): Lists recent traces (with optional filtering)
  - get_agent_statistics(): Aggregates execution stats

Purpose: Audit trail, debugging, analytics, agent behavior tracking.

### Operational CLI (scripts/run_agent.py)
- Async CLI for manual agent execution
- Commands: eligibility, safety, research, info
- Optional JSON output, trace ID correlation
- LLM provider fallback to stub mode

Purpose: Operational execution without API routes, manual testing, debugging.

==================================================
DATA FLOW
==================================================

Request → Dispatcher → Agent → Tool Calls (via existing repos) → LLM → Response → TraceStore

Example (Eligibility Analysis):
1. User: python scripts/run_agent.py eligibility <patient_id> <trial_id>
2. CLI: Creates EligibilityAnalystRequest
3. Dispatcher: Routes to EligibilityAnalystAgent
4. Agent: Calls PatientLookupTool, TrialLookupTool, AdverseEventLookupTool, etc.
5. Tools: Query existing repositories (PatientRepository, TrialRepository, etc.)
6. Agent: Formats context, calls LLM for analysis (or stub if no key)
7. LLM: Returns completion with clinical reasoning
8. Agent: Constructs EligibilityAnalysisResult with structured output
9. Executor: Persists trace to MongoDB
10. CLI: Prints formatted result, optionally saves JSON

==================================================
LLM PROVIDER STRATEGY
==================================================

### OpenAI-Compatible Provider
- Provider: openai_client.py (OpenAICompatibleProvider)
- Supports: OpenAI API, Azure OpenAI, compatible endpoints
- Configuration: LLM_PROVIDER=openai_compatible, LLM_BASE_URL, LLM_MODEL, LLM_API_KEY
- Async: Uses httpx for non-blocking API calls
- Fallback: Returns empty response if API key missing or call fails

### Stub Provider (No-Key Mode)
- Provider: stub.py (StubLLMProvider)
- Purpose: Enables code to run without LLM API key
- Output: Deterministic, grounded placeholder text based on agent type
- NOT hallucination: Stub responses reference actual data retrieved by tools
- Example: "Adverse event records have been queried. Tool integration is functional."

### Provider Factory
- create_llm_provider(): Routes to appropriate provider
- Strategy: No provider or no API key → use stub automatically
- Future extensible: Add other providers easily

==================================================
TOOL INTEGRATION PATTERN
==================================================

Each tool follows this pattern:

1. Tool class extends Tool base class
2. get_name(): Returns tool name
3. get_description(): Returns human-readable description
4. execute(args): Async execution that queries existing service/repository
5. Returns ToolResult(success, data, error, message)

Example: PatientLookupTool

```python
class PatientLookupTool(Tool):
    async def execute(self, args):
        patient_id = args.get("patient_id")
        repo = PatientRepository(session)
        patient = repo.get_by_id(patient_id) or repo.get_by_external_patient_id(patient_id)
        return ToolResult(success=True, data=patient_dict)
```

Tools call existing repositories cleanly:
- PatientRepository, TrialRepository, AdverseEventRepository, etc. (existing Phase 3)
- PredictionRepository for Phase 7 prediction outputs
- Document retrieval stubs ready for RAG future work

==================================================
TRACE PERSISTENCE
==================================================

Traces persisted to MongoDB collection: agent_traces

TraceRecord fields:
- trace_id: Unique correlation ID for request flow
- timestamp: Execution timestamp
- metadata: Agent type, execution time, success flag, tool count
- request_summary: Concise request description
- result_summary: Concise result description (truncated)
- tool_calls: List of tool names used
- full_result: Full result dict if < 10KB

Usage:
- Audit trail for clinical workflows
- Analytics on agent performance
- Debugging agent behavior
- Traceability correlations

MongoDB aggregation example:
```
db.agent_traces.aggregate([
    { $match: { "metadata.agent_type": "eligibility_analyst" } },
    { $group: { _id: "$metadata.agent_type", avg_time: { $avg: "$metadata.execution_time_ms" } } }
])
```

==================================================
OPERATIONAL EXECUTION
==================================================

```bash
# Info: Show agents and tools
python scripts/run_agent.py info

# Eligibility analysis
python scripts/run_agent.py eligibility <patient_id> <trial_id> \
  --trace-id my-trace-123 \
  --output-json results.json

# Safety investigation
python scripts/run_agent.py safety <patient_id> \
  --drug "Metformin" \
  --trace-id my-trace-456

# Research summarization
python scripts/run_agent.py research \
  --trial <trial_code> \
  --query "How does this trial compare to similar studies?" \
  --context literature

# No-key stub mode (automatic if LLM_API_KEY not set)
unset LLM_API_KEY
python scripts/run_agent.py eligibility P123 T456
# Returns stub response demonstrating operational framework
```

==================================================
STRICT RULES IMPLEMENTED
==================================================

✅ No generic chatbot wrapper
  - Three specific agents with defined roles and outputs

✅ No hallucinated fake retrieval
  - Tools call existing repositories and services
  - Document retrieval is explicit stub (ready for RAG)

✅ No hardcoded fake clinical outputs
  - Outputs computed from real data or default fallbacks

✅ No frontend chat UI yet
  - CLI-only operational execution

✅ No API routes yet
  - Next phase (Phase 9) will add FastAPI endpoints

✅ No giant prompt spaghetti
  - Prompts organized in PromptRegistry, separated from business logic

✅ Clean architecture with separated concerns
  - Base abstractions, LLM provider, prompts, tools, agents, orchestration, persistence

✅ LLM provider abstraction (not OpenAI-specific)
  - Works with any OpenAI-compatible provider
  - Stub mode for no-key execution
  - Easy to swap providers later

✅ Modular and extensible
  - Add new agents by creating new Agent class and registering in dispatcher
  - Add new tools by implementing Tool interface and registering in ToolRegistry
  - Add new LLM providers by implementing LLMProvider interface

==================================================
FILES CREATED / UPDATED
==================================================

Created:
- agents/base/agent.py
- agents/base/contracts.py
- agents/base/tools.py
- agents/base/trace.py
- agents/base/__init__.py
- agents/llm/provider.py
- agents/llm/openai_client.py
- agents/llm/stub.py
- agents/llm/__init__.py
- agents/prompts/registry.py
- agents/prompts/__init__.py
- agents/tools/base.py
- agents/tools/__init__.py
- agents/eligibility_analyst.py
- agents/safety_investigator.py
- agents/research_summarizer.py
- agents/orchestration/dispatcher.py
- agents/orchestration/__init__.py
- agents/persistence/trace_store.py
- agents/persistence/__init__.py
- agents/__init__.py (updated with comprehensive exports)
- scripts/run_agent.py (CLI entrypoint)
- docs/architecture/phase-8-agentic-ai-orchestration.md (this file)

==================================================
NEXT STEPS (PHASE 9)
==================================================

Recommended future work:
1. FastAPI agent endpoints (/agents/eligibility, /agents/safety, /agents/research)
2. Request validation and error handling middleware
3. Agent-specific integration tests with fixture data
4. Frontend chat UI or Agent Builder UI
5. Full RAG integration for document_retrieval tool
6. Agent memory/context management for multi-turn conversations
7. Streaming support for long-running analyses
8. Production hardening (rate limiting, auth, caching)

==================================================
VALIDATION COMMANDS
==================================================

# Syntax check
python -m compileall src/pharma_os/agents scripts/run_agent.py

# Basic execution (no key required, uses stub)
python scripts/run_agent.py info

# Full execution test (with real data)
python scripts/run_agent.py eligibility <valid_external_patient_id> <trial_code>

# With LLM key (after configuring LLM_API_KEY)
LLM_PROVIDER=openai_compatible \
LLM_BASE_URL=https://api.openai.com/v1 \
LLM_MODEL=gpt-3.5-turbo \
LLM_API_KEY=sk-... \
python scripts/run_agent.py safety <patient_id> --drug "Aspirin"
"""
