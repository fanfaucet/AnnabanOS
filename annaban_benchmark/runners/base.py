from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass


@dataclass
class ModelResponse:
    content: str
    latency_ms: int
    cost: float
    usage: dict


class BaseRunner:
    def __init__(self, name: str):
        self.name = name

    async def chat(self, prompt: str) -> ModelResponse:
        seed = int(hashlib.sha256((self.name + prompt).encode()).hexdigest(), 16) % 100_000
        random.seed(seed)
        latency = random.randint(80, 600)
        cost = round(random.uniform(0.001, 0.02), 5)
        content = f"[{self.name}] synthetic response for: {prompt[:80]}"
        return ModelResponse(content=content, latency_ms=latency, cost=cost, usage={"cost": cost})

    def embed(self, text: str):
        seed = int(hashlib.md5((self.name + text).encode()).hexdigest(), 16)
        random.seed(seed)
        return [random.random() for _ in range(16)]
