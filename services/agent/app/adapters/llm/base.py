"""LLM provider abstract interface.

This defines the contract for structured LLM generation.
V0 uses MockLLMProvider. Future: OpenAIProvider, DeepSeekProvider, etc.
Core business logic must never depend on a specific model SDK.
"""

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel


class LLMRequest(BaseModel):
    """A request to the LLM provider."""

    system_prompt: str = ""
    user_prompt: str
    response_format: dict[str, Any] | None = None
    temperature: float = 0.7
    max_tokens: int = 2000


class LLMResponse(BaseModel):
    """Response from the LLM provider."""

    text: str
    structured: dict[str, Any] | None = None
    tokens_used: int = 0


@runtime_checkable
class LLMProvider(Protocol):
    """Abstract interface for LLM providers.

    Implementations must provide structured generation capability.
    Platform-specific SDK details must be isolated within adapters.
    """

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a text response from the LLM."""
        ...

    async def generate_structured(
        self,
        request: LLMRequest,
        schema: dict[str, Any],
    ) -> LLMResponse:
        """Generate a structured response conforming to the given JSON schema."""
        ...
