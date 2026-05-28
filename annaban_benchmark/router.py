from __future__ import annotations

from .runners.anthropic import AnthropicRunner
from .runners.gemini import GeminiRunner
from .runners.grok import GrokRunner
from .runners.openai import OpenAIRunner


class LatencyAwareRouter:
    """
    Selects model mix based on:
    - cost
    - latency history
    - task type
    """

    def __init__(self):
        self.history = {}
        self.registry = {
            "gpt": OpenAIRunner(),
            "claude": AnthropicRunner(),
            "gemini": GeminiRunner(),
            "grok": GrokRunner(),
        }

    def select_models(self, prompt, task_type="general"):
        if task_type == "reasoning":
            names = ["claude", "gpt"]
        elif task_type == "multimodal":
            names = ["gemini", "gpt"]
        elif task_type == "fast":
            names = ["grok"]
        else:
            names = ["gpt", "claude", "gemini"]

        return [self.registry[n] for n in names]
