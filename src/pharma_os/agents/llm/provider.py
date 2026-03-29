"""Abstract LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Message(dict):
    """Message in provider-agnostic format.

    Follows OpenAI format: {"role": "user"|"assistant"|"system", "content": str}
    """

    def __init__(self, role: str, content: str):
        """Initialize message.

        Args:
            role: Message role (system, user, assistant)
            content: Message content
        """
        super().__init__(role=role, content=content)
        self.role = role
        self.content = content


class LLMResponse:
    """Provider-agnostic LLM response."""

    def __init__(
        self,
        content: str,
        model: str | None = None,
        usage_tokens: int | None = None,
        raw_response: Any = None,
    ):
        """Initialize LLM response.

        Args:
            content: Generated text content
            model: Model name used
            usage_tokens: Token count (approximate)
            raw_response: Raw provider response object
        """
        self.content = content
        self.model = model
        self.usage_tokens = usage_tokens
        self.raw_response = raw_response


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get model name."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available (e.g., API key configured)."""
        pass

    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate completion from messages.

        Args:
            messages: List of messages (following OpenAI format)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt to prepend

        Returns:
            LLMResponse with generated content
        """
        pass
