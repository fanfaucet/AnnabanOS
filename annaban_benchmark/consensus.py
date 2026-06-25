from __future__ import annotations

import math
from typing import Iterable, List


def _cosine(a: Iterable[float], b: Iterable[float]) -> float:
    a_values = list(a)
    b_values = list(b)
    dot = sum(x * y for x, y in zip(a_values, b_values))
    norm_a = math.sqrt(sum(x * x for x in a_values))
    norm_b = math.sqrt(sum(y * y for y in b_values))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class ConsensusEngine:
    """Computes output agreement as execution metadata, not truth validation."""

    def evaluate(self, outputs):
        if not outputs:
            return {"winner": None, "agreement_ratio": 0.0, "stability": 0.0}

        embeddings: List[List[float]] = [o["embedding"] for o in outputs]
        matrix = [[_cosine(left, right) for right in embeddings] for left in embeddings]
        mean_similarities = [sum(row) / len(row) for row in matrix]
        winner_idx = max(range(len(mean_similarities)), key=mean_similarities.__getitem__)

        agreement = sum(1 for score in matrix[winner_idx] if score > 0.85) / len(outputs)
        stability = sum(sum(row) for row in matrix) / (len(matrix) * len(matrix))

        return {
            "winner": outputs[winner_idx]["model"],
            "agreement_ratio": agreement,
            "stability": stability,
            "note": "Agreement is a routing/audit signal and is not a truth judgment.",
        }


def agreement_score(outputs) -> float:
    """Return the advisory agreement ratio for benchmark outputs."""
    return ConsensusEngine().evaluate(outputs).get("agreement_ratio", 0.0)
