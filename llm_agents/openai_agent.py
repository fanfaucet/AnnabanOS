from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI, OpenAI

from .base_agent import BaseAgent


class OpenAIAgent(BaseAgent):
    def __init__(self, name: str, api_key: str, model: str = "gpt-4o-mini"):
        super().__init__(name=name, api_key=api_key)
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)

    def send_request(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        response = self.client.responses.create(
            model=kwargs.get("model", self.model),
            input=prompt,
            max_output_tokens=kwargs.get("max_output_tokens", 512),
        )
        return {
            "text": response.output_text,
            "response_id": response.id,
        }

    async def stream_request(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        stream = await self.async_client.responses.create(
            model=kwargs.get("model", self.model),
            input=prompt,
            max_output_tokens=kwargs.get("max_output_tokens", 512),
            stream=True,
        )
        async for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta

    def estimate_cost(self, tokens: int) -> float:
        return tokens * 0.0000006
