from __future__ import annotations

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class ConsensusEngine:
    def evaluate(self, outputs):
        if not outputs:
            return {"winner": None, "agreement_ratio": 0.0}

        embs = np.array([o["embedding"] for o in outputs])
        sim = cosine_similarity(embs)

        mean_sim = sim.mean(axis=1)
        winner_idx = int(np.argmax(mean_sim))

        winner = outputs[winner_idx]["model"]

        agreement = sum(1 for s in sim[winner_idx] if s > 0.85) / len(outputs)

        return {
            "winner": winner,
            "agreement_ratio": agreement,
            "stability": float(np.mean(sim)),
        }
