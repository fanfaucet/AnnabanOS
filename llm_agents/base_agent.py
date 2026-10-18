from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any


class BaseAgent(ABC):
    """Common contract for ANNABAN LLM adapters.

    Implementations normalize provider-specific responses into a small,
    stable interface. Credentials remain adapter-owned.
    """

    provider: str = "unknown"

    def __init__(self, name: str, api_key: str, model: str | None = None):
        if not name.strip():
            raise ValueError("Agent name must not be empty.")
        if not api_key:
            raise ValueError("API key must not be empty.")
        self.name = name
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def send_request(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Send one request and return normalized response metadata."""
        raise NotImplementedError

    @abstractmethod
    async def stream_request(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        """Yield normalized text deltas from a provider stream."""
        raise NotImplementedError

    @abstractmethod
    def estimate_cost(self, tokens: int) -> float:
        """Estimate provider cost for the supplied token count."""
        raise NotImplementedError
