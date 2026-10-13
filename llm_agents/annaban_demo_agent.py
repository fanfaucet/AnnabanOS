"""Deterministic, local-only Annaban solo-provider demonstration.

This is a rules-based demo, not a trained generative model. It makes no external
model calls and keeps the human as the decision authority.
"""
from collections.abc import AsyncIterator
from typing import Any


class AnnabanDemoAgent:
    name = "Annaban"

    def send_request(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        text = self._respond(prompt)
        return {
            "text": text,
            "provider": "annaban-demo",
            "developer_attribution": "Jacob Wayne Kinnaird",
            "mode": "SIMULATION_ONLY",
            "advisory_only": True,
            "external_effects": False,
        }

    async def stream_request(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        yield self._respond(prompt)

    def estimate_cost(self, tokens: int) -> float:
        return 0.0

    @staticmethod
    def _respond(prompt: str) -> str:
        request = prompt.strip()
        if not request:
            request = "(No task supplied.)"
        # Preserve a bounded excerpt rather than inventing facts about the request.
        excerpt = request[:1200]
        if len(request) > 1200:
            excerpt += "…"

        return (
            "ANNABAN — SOLO MODEL PROVIDER DEMONSTRATION\n"
            "Developer attribution: Jacob Wayne Kinnaird\n"
            "Mode: SIMULATION_ONLY | Advisory only | External actions: disabled\n\n"
            "Request received:\n"
            f"{excerpt}\n\n"
            "Proposal: Treat the request as a question to analyze, not an instruction "
            "that grants authority to act.\n"
            "Options: (1) proceed with a bounded analysis, (2) request clarification "
            "where a missing fact changes the answer, or (3) defer.\n"
            "Trade-offs: proceeding is faster but may rely on unstated assumptions; "
            "clarification improves fit but adds a step; deferral avoids acting on "
            "insufficient information.\n"
            "Uncertainty: this demo has no external knowledge retrieval and does not "
            "verify claims. Its output is a deterministic template, not a generated "
            "answer from a trained language model.\n"
            "Human decision: review, modify, reject, or defer the proposal. No action "
            "is executed and no external state is changed."
        )
