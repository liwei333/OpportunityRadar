"""Mock LLM provider for V0 development.

Returns canned responses without calling any real model.
This allows full pipeline testing without API keys or network access.
"""

import json
from typing import Any

from .base import LLMRequest, LLMResponse


class MockLLMProvider:
    """Mock LLM provider that returns predefined responses."""

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Return a canned text response."""
        text = (
            f"[Mock LLM] Received: {request.user_prompt[:100]}..."
            if len(request.user_prompt) > 100
            else f"[Mock LLM] Received: {request.user_prompt}"
        )
        return LLMResponse(text=text, tokens_used=len(text.split()))

    async def generate_structured(
        self,
        request: LLMRequest,
        schema: dict[str, Any],
    ) -> LLMResponse:
        """Return a structured response matching the schema."""
        # Build a minimal valid response from schema properties
        structured: dict[str, Any] = {}
        properties = schema.get("properties", {})
        for key, prop in properties.items():
            prop_type = prop.get("type", "string")
            if prop_type == "string":
                structured[key] = f"mock_{key}"
            elif prop_type == "integer":
                structured[key] = 0
            elif prop_type == "number":
                structured[key] = 0.0
            elif prop_type == "boolean":
                structured[key] = True
            elif prop_type == "array":
                structured[key] = []
            elif prop_type == "object":
                structured[key] = {}
            else:
                structured[key] = None

        return LLMResponse(
            text=json.dumps(structured, ensure_ascii=False),
            structured=structured,
            tokens_used=50,
        )
