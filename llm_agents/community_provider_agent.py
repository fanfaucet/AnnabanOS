"""Adapter for a registered community endpoint, selected only by explicit opt-in."""
from collections.abc import AsyncIterator
from typing import Any

from model_providers.registry import community_provider_registry


class CommunityProviderAgent:
    def __init__(self, provider_id: str, display_name: str):
        self.provider_id = provider_id
        self.name = display_name

    def send_request(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("Use stream_request() for the async community-provider adapter.")

    async def stream_request(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        try:
            answer = await community_provider_registry.complete(self.provider_id, prompt)
        except Exception:
            yield "[community provider unavailable; request failed]"
            return
        if answer:
            yield answer

    def estimate_cost(self, tokens: int) -> float:
        # Community providers define their own billing terms; no price is inferred.
        return 0.0
