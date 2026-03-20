from collections.abc import AsyncIterator
from typing import Any

from .base_agent import BaseAgent


class AnthropicAgent(BaseAgent):
    def send_request(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "text": "Anthropic integration placeholder. Configure SDK wiring before production use.",
            "prompt": prompt,
        }

    async def stream_request(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        yield "Anthropic integration placeholder"
        yield f" for prompt: {prompt}"

    def estimate_cost(self, tokens: int) -> float:
        return tokens * 0.0000008
