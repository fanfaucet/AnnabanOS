from __future__ import annotations

import re
from typing import Dict, List


class SignalHeuristicsLayer:
    """Detects operational signals without making truth or correctness claims."""

    AUTHORITY_LANGUAGE = re.compile(r"\b(definitely|guaranteed|certainly|must|always|never)\b", re.I)
    AMBIGUITY_MARKERS = re.compile(r"\b(maybe|possibly|unclear|unknown|ambiguous|depends)\b", re.I)

    def evaluate(self, text: str) -> Dict:
        signals: List[str] = []
        scores = {"ambiguity": 0.0, "authority_language": 0.0}

        authority_hits = self.AUTHORITY_LANGUAGE.findall(text)
        ambiguity_hits = self.AMBIGUITY_MARKERS.findall(text)

        if authority_hits:
            signals.append("authority_language_detected")
            scores["authority_language"] = min(1.0, len(authority_hits) / 4)
        if ambiguity_hits or len(text.split()) < 8:
            signals.append("high_ambiguity")
            scores["ambiguity"] = min(1.0, max(len(ambiguity_hits) / 3, 0.5))

        return {"signals": signals, "scores": scores}
