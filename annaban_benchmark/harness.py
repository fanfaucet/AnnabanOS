from __future__ import annotations

from typing import Dict

from .consensus import ConsensusEngine
from .cost import CostTracker
from .datasets import load_dataset
from .router import LatencyAwareRouter


class BenchmarkHarness:
    """Orchestrates multi-model evaluation."""

    def __init__(self):
        self.router = LatencyAwareRouter()
        self.consensus = ConsensusEngine()
        self.cost = CostTracker()

    async def run_single(self, task: Dict) -> Dict:
        prompt = task["prompt"]
        selected_models = self.router.select_models(prompt, task_type=task["type"])

        outputs = []
        for model in selected_models:
            resp = await model.chat(prompt)
            self.cost.record(model.name, resp.usage)
            outputs.append(
                {
                    "model": model.name,
                    "text": resp.content,
                    "embedding": model.embed(resp.content),
                    "latency": resp.latency_ms,
                    "cost": resp.cost,
                }
            )

        consensus = self.consensus.evaluate(outputs)

        return {
            "task": task["id"],
            "failure_rate": 1.0 if consensus["agreement_ratio"] < 0.6 else 0.0,
            "agreement": consensus["agreement_ratio"],
            "cost": sum(o["cost"] for o in outputs),
            "winner": consensus["winner"],
        }

    async def run_benchmark(self) -> Dict:
        dataset = load_dataset()

        results = []
        for task in dataset:
            results.append(await self.run_single(task))

        avg_failure = sum(r["failure_rate"] for r in results) / len(results)
        avg_cost = sum(r["cost"] for r in results) / len(results)
        avg_agreement = sum(r["agreement"] for r in results) / len(results)

        annaban_score = (1 - avg_failure) * avg_agreement / (1 + avg_cost)

        return {
            "tasks": len(results),
            "avg_failure_rate": avg_failure,
            "avg_cost": avg_cost,
            "avg_agreement": avg_agreement,
            "annaban_governance_score": annaban_score,
        }
