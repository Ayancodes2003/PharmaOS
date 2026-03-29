"""OpenAI-compatible LLM provider."""

from __future__ import annotations

import logging
from typing import Any

from pharma_os.agents.llm.provider import LLMProvider, LLMResponse, Message

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI-compatible LLM provider using httpx or requests."""

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
    ):
        """Initialize OpenAI-compatible provider.

        Args:
            model: Model name (e.g., gpt-4, gpt-3.5-turbo)
            api_key: API key for authentication
            base_url: Base URL for API (defaults to OpenAI, can be changed for other providers)
        """
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "openai_compatible"

    def get_model_name(self) -> str:
        """Get model name."""
        return self.model

    def is_available(self) -> bool:
        """Check if provider is available."""
        return bool(self.api_key and self.model)

    async def complete(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate completion from messages.

        Args:
            messages: List of messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt

        Returns:
            LLMResponse
        """
        # Prepare messages
        msg_list = []

        if system_prompt:
            msg_list.append({"role": "system", "content": system_prompt})

        for msg in messages:
            msg_list.append({"role": msg.role, "content": msg.content})

        # Lazy import of httpx to avoid hard dependency
        try:
            import httpx
        except ImportError:
            logger.error("httpx not installed. Install with: pip install httpx")
            return LLMResponse(
                content="",
                model=self.model,
                raw_response=None,
            )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": msg_list,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()

                content = ""
                usage = 0

                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0].get("message", {}).get("content", "")

                if "usage" in data:
                    usage = data["usage"].get("total_tokens", 0)

                return LLMResponse(
                    content=content,
                    model=self.model,
                    usage_tokens=usage,
                    raw_response=data,
                )

        except Exception as e:
            logger.error(f"Error calling LLM API: {e}")
            return LLMResponse(
                content="",
                model=self.model,
                raw_response=None,
            )
