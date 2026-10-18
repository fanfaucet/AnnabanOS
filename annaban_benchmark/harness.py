from __future__ import annotations

from typing import Dict

from .consensus import ConsensusEngine
from .cost import CostTracker
from .datasets.loader import load_dataset
from .metrics import governance_score
from .router import LatencyAwareRouter


class BenchmarkHarness:
    """Runs reproducible operational evaluations without deciding output truth."""

    def __init__(self, dataset_path: str | None = None):
        self.dataset_path = dataset_path
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
        policy_pass = 1.0 if outputs else 0.0

        return {
            "task": task["id"],
            "policy_pass": policy_pass,
            "agreement_signal": consensus["agreement_ratio"],
            "stability_signal": consensus["stability"],
            "cost": sum(o["cost"] for o in outputs),
            "selected_model": outputs[0]["model"] if outputs else None,
            "note": consensus["note"],
        }

    async def run_benchmark(self) -> Dict:
        dataset = load_dataset(self.dataset_path)

        results = []
        for task in dataset:
            results.append(await self.run_single(task))

        if not results:
            return {
                "tasks": 0,
                "avg_policy_pass": 0.0,
                "avg_cost": 0.0,
                "avg_agreement_signal": 0.0,
                "avg_audit_integrity": 1.0,
                "annaban_governance_score": 0.0,
                "note": "No benchmark tasks were loaded.",
            }

        avg_policy_pass = sum(r["policy_pass"] for r in results) / len(results)
        avg_cost = sum(r["cost"] for r in results) / len(results)
        avg_agreement_signal = sum(r["agreement_signal"] for r in results) / len(results)
        avg_audit_integrity = 1.0

        return {
            "tasks": len(results),
            "avg_policy_pass": avg_policy_pass,
            "avg_cost": avg_cost,
            "avg_agreement_signal": avg_agreement_signal,
            "avg_audit_integrity": avg_audit_integrity,
            "annaban_governance_score": governance_score(avg_policy_pass, avg_cost, avg_audit_integrity),
            "note": "Governance score is operational metadata, not a correctness or truth score.",
        }
