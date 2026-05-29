from __future__ import annotations

from .models import ModelSelection
from .runners.anthropic import AnthropicRunner
from .runners.gemini import GeminiRunner
from .runners.grok import GrokRunner
from .runners.ollama import OllamaRunner
from .runners.openai import OpenAIRunner


class LatencyAwareRouter:
    """Selects models using operational heuristics only; it does not judge truth."""

    def __init__(self):
        self.history = {}
        self.registry = {
            "gpt": OpenAIRunner(),
            "claude": AnthropicRunner(),
            "gemini": GeminiRunner(),
            "grok": GrokRunner(),
            "ollama": OllamaRunner(),
        }

    def route(self, prompt: str, context: dict | None = None) -> ModelSelection:
        context = context or {}
        task_type = context.get("task_type", "general")
        if task_type == "fast":
            return ModelSelection(model="grok", reason="latency_default", fallback_chain=["gpt"])
        if task_type == "local_fallback":
            return ModelSelection(model="gpt", reason="cloud_primary_local_fallback", fallback_chain=["ollama"])
        if len(prompt) > 1_000:
            return ModelSelection(model="claude", reason="long_context_default", fallback_chain=["gpt", "gemini"])
        return ModelSelection(model="gpt", reason="cost_latency_default", fallback_chain=["claude", "gemini"])

    def select_models(self, prompt, task_type="general"):
        """Compatibility helper for benchmark-style callers."""
        selection = self.route(prompt, {"task_type": task_type})
        names = [selection.model, *selection.fallback_chain]
        return [self.registry[n] for n in names if n in self.registry]
