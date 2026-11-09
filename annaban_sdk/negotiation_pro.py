"""Negotiation-Pro: validate proposed changes against explicit policy ceilings."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class NegotiationDecision:
    status: str
    requested_percent: str
    proposed_percent: str
    ceiling_percent: str
    external_effect: int = 0
    reason: str = ""


class NegotiationPro:
    """Pure validator. Percentages are represented as Decimal-compatible strings."""
    def evaluate(self, requested_percent: str, proposed_percent: str, ceiling_percent: str) -> NegotiationDecision:
        try:
            requested = Decimal(requested_percent)
            proposed = Decimal(proposed_percent)
            ceiling = Decimal(ceiling_percent)
        except (InvalidOperation, TypeError):
            raise ValueError("percentages must be valid decimal values") from None
        if not all(v.is_finite() for v in (requested, proposed, ceiling)):
            raise ValueError("percentages must be finite")
        if requested < 0 or proposed < 0 or ceiling < 0:
            raise ValueError("percentages must be non-negative")
        if proposed > requested:
            return NegotiationDecision("SAFE_HOLD", str(requested), str(proposed), str(ceiling), 0,
                                       "proposal exceeds requested limit")
        if proposed > ceiling:
            return NegotiationDecision("SAFE_HOLD", str(requested), str(proposed), str(ceiling), 0,
                                       "proposal exceeds policy ceiling")
        return NegotiationDecision("WITHIN_POLICY", str(requested), str(proposed), str(ceiling), 0,
                                   "validation only; no negotiation or transaction executed")
