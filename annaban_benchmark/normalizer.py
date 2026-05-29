from __future__ import annotations

from typing import Dict, List

from .models import NormalizedOutput


class OutputNormalizer:
    """Wraps output in a stable schema without paraphrasing or changing meaning."""

    def normalize(self, answer: str, metadata: Dict, signals: Dict) -> NormalizedOutput:
        uncertainty_tags: List[str] = []
        if "high_ambiguity" in signals.get("signals", []):
            uncertainty_tags.append("ambiguity_detected")
        if "authority_language_detected" in signals.get("signals", []):
            uncertainty_tags.append("authority_language_detected")

        return NormalizedOutput(
            answer=answer,
            uncertainty_tags=uncertainty_tags,
            metadata={**metadata, "signals": signals},
        )
