"""LLM provider factory and initialization."""

from __future__ import annotations

import logging

from pharma_os.agents.llm.openai_client import OpenAICompatibleProvider
from pharma_os.agents.llm.provider import LLMProvider
from pharma_os.agents.llm.stub import StubLLMProvider

logger = logging.getLogger(__name__)


def create_llm_provider(
    provider: str | None,
    model: str | None,
    api_key: str | None,
    base_url: str | None = None,
) -> LLMProvider:
    """Create and return appropriate LLM provider.

    Args:
        provider: Provider type (openai_compatible, stub, or None)
        model: Model name
        api_key: API key for authentication
        base_url: Base URL for API (optional, defaults for OpenAI)

    Returns:
        LLMProvider instance
    """
    # If no provider specified or no API key, use stub
    if not provider or not api_key:
        logger.info("No LLM provider configured. Using stub provider.")
        return StubLLMProvider()

    # Handle OpenAI-compatible providers
    if provider.lower() in ("openai", "openai_compatible"):
        if not model:
            logger.warning(
                "OpenAI provider requested but no model specified. "
                "Defaulting to gpt-3.5-turbo."
            )
            model = "gpt-3.5-turbo"

        base_url = base_url or "https://api.openai.com/v1"
        logger.info(f"Using OpenAI-compatible provider: {model} at {base_url}")
        return OpenAICompatibleProvider(
            model=model,
            api_key=api_key,
            base_url=base_url,
        )

    # Default to stub for unknown providers
    logger.warning(f"Unknown provider: {provider}. Using stub provider.")
    return StubLLMProvider()


__all__ = [
    "LLMProvider",
    "OpenAICompatibleProvider",
    "StubLLMProvider",
    "create_llm_provider",
]
