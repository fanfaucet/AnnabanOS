import argparse
import asyncio
import json

from annaban_benchmark.harness import BenchmarkHarness
from annaban_benchmark.orchestrator import AnnabanOrchestrator


async def run_benchmark() -> None:
    harness = BenchmarkHarness()
    result = await harness.run_benchmark()

    print("\n=== ANNABAN GOVERNANCE BENCHMARK ===")
    print(f"Tasks: {result['tasks']}")
    print(f"Policy Pass: {result['avg_policy_pass']:.3f}")
    print(f"Cost: ${result['avg_cost']:.4f}")
    print(f"Agreement Signal: {result['avg_agreement_signal']:.3f}")
    print(f"Audit Integrity: {result['avg_audit_integrity']:.3f}")
    print(f"Governance Score: {result['annaban_governance_score']:.4f}")
    print(result["note"])


async def run_once(prompt: str, task_type: str) -> None:
    orchestrator = AnnabanOrchestrator()
    result = await orchestrator.run(prompt, {"task_type": task_type})
    print(json.dumps(result, indent=2, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description="AnnabanAI governance middleware CLI")
    parser.add_argument("--prompt", help="Run one audited prompt through the orchestrator")
    parser.add_argument("--task-type", default="general", help="Operational routing task type")
    args = parser.parse_args()

    if args.prompt:
        asyncio.run(run_once(args.prompt, args.task_type))
    else:
        asyncio.run(run_benchmark())


if __name__ == "__main__":
    main()
