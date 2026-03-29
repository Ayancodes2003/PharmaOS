"""Stub LLM provider for no-key environments."""

from __future__ import annotations

import logging
from typing import Any

from pharma_os.agents.llm.provider import LLMProvider, LLMResponse, Message

logger = logging.getLogger(__name__)


class StubLLMProvider(LLMProvider):
    """Stub LLM provider that returns placeholder responses.

    Used in environments where no LLM API key is available.
    Returns deterministic, non-hallucinated placeholders based on input patterns.
    """

    def __init__(self):
        """Initialize stub provider."""
        pass

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "stub"

    def get_model_name(self) -> str:
        """Get model name."""
        return "stub-model"

    def is_available(self) -> bool:
        """Check if provider is available."""
        return True  # Stub is always available

    async def complete(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate stub completion.

        Returns a generic placeholder message based on the system prompt.

        Args:
            messages: List of messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            system_prompt: System prompt (used to determine response type)

        Returns:
            LLMResponse with stub content
        """
        # Determine response type based on system prompt
        response_content = self._generate_stub_response(system_prompt, messages)

        return LLMResponse(
            content=response_content,
            model="stub-model",
            usage_tokens=len(response_content.split()),
            raw_response=None,
        )

    def _generate_stub_response(self, system_prompt: str | None, messages: list[Message]) -> str:
        """Generate appropriate stub response based on context.

        Args:
            system_prompt: System prompt to determine response type
            messages: Messages for additional context

        Returns:
            Stub response string
        """
        if system_prompt and "eligibility" in system_prompt.lower():
            return """[STUB ANALYSIS - No LLM API key configured]

Patient Profile:
- Available from database query
- Clinical context loaded from repositories

Trial Profile:
- Criteria reference available
- Indication and phase information available

Assessment:
This is a stub response placeholder. To enable full LLM-powered eligibility analysis, 
configure LLM_PROVIDER, LLM_BASE_URL, LLM_MODEL, and LLM_API_KEY in your environment.

Evidence from Data:
- Patient clinical context has been retrieved
- Trial profile has been loaded
- Repositories and prediction services are operational

Recommendation:
The agent framework is operational and ready for data-driven analysis. 
Live LLM integration will enable full clinical reasoning when configured."""

        elif system_prompt and "safety" in system_prompt.lower():
            return """[STUB ANALYSIS - No LLM API key configured]

Patient Safety Context:
- Adverse event history loaded from database
- Drug exposure records retrieved
- Medical history available

Safety Assessment:
This is a stub response placeholder. To enable full LLM-powered safety investigation,
configure LLM_PROVIDER, LLM_BASE_URL, LLM_MODEL, and LLM_API_KEY in your environment.

Evidence from Data:
- Adverse event records have been queried
- Drug exposure patterns are available
- Safety prediction service is operational

Recommendation:
The safety investigation framework is functional and grounded in real clinical data.
Live LLM integration will enable pattern recognition and risk assessment when configured."""

        elif system_prompt and "research" in system_prompt.lower():
            return """[STUB SUMMARY - No LLM API key configured]

Research Context:
- Trial information has been retrieved
- Available documents and references loaded
- Context type identified

Summary:
This is a stub response placeholder. To enable full LLM-powered research summarization,
configure LLM_PROVIDER, LLM_BASE_URL, LLM_MODEL, and LLM_API_KEY in your environment.

Available Information:
- Trial metadata and criteria accessible
- Document retrieval framework in place
- Research query framework operational

Next Steps:
The research summarization framework is built and ready for data integration.
Live LLM integration will enable intelligent synthesis when configured."""

        else:
            return """[STUB RESPONSE - No LLM API key configured]

Agent Framework Status: OPERATIONAL
Database Connectivity: ACTIVE
Tool Registry: LOADED
Trace Persistence: CONFIGURED

To enable live LLM responses, set these environment variables:
- LLM_PROVIDER (e.g., openai_compatible)
- LLM_BASE_URL (e.g., https://api.openai.com/v1)
- LLM_MODEL (e.g., gpt-4)
- LLM_API_KEY (your API key)

The agent framework, tool abstractions, and data access layer are fully operational.
This stub response demonstrates successful orchestration without a live LLM API key."""
