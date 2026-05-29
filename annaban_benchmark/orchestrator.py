from __future__ import annotations

from dataclasses import asdict
from typing import Dict

from .audit import AuditLogger
from .constraints import ConstraintLayer
from .normalizer import OutputNormalizer
from .router import LatencyAwareRouter
from .signals import SignalHeuristicsLayer


class AnnabanOrchestrator:
    """Stateless LLM wrapper with deterministic policy and stateful audit logging."""

    def __init__(self, audit_path: str | None = None):
        self.router = LatencyAwareRouter()
        self.constraints = ConstraintLayer()
        self.signals = SignalHeuristicsLayer()
        self.normalizer = OutputNormalizer()
        self.audit = AuditLogger(audit_path)

    async def run(self, prompt: str, context: Dict | None = None) -> Dict:
        context = context or {}
        selection = self.router.route(prompt, context)
        self.audit.record("route", {"selection": asdict(selection), "context": context})

        runner = self.router.registry[selection.model]
        response = await runner.chat(prompt)
        response_metadata = {
            "model": runner.name,
            "latency_ms": response.latency_ms,
            "cost": response.cost,
            "route_reason": selection.reason,
            "fallback_chain": selection.fallback_chain,
        }
        self.audit.record("model_call", response_metadata)

        signal_report = self.signals.evaluate(response.content)
        self.audit.record("signals", signal_report)

        constrained_text, constrained_metadata = self.constraints.apply(response.content, response_metadata)
        normalized = self.normalizer.normalize(constrained_text, constrained_metadata, signal_report)
        self.audit.record("normalize", asdict(normalized))

        return {
            "output": asdict(normalized),
            "audit_hash": self.audit.last_hash,
            "audit_verified": self.audit.verify(),
        }
