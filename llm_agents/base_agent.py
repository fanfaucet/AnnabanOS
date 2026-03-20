from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any


class BaseAgent(ABC):
    def __init__(self, name: str, api_key: str):
        self.name = name
        self.api_key = api_key

    @abstractmethod
    def send_request(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def stream_request(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        yield ""

    @abstractmethod
    def estimate_cost(self, tokens: int) -> float:
        raise NotImplementedError
