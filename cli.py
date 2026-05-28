import asyncio

from annaban_benchmark.harness import BenchmarkHarness


def main():
    harness = BenchmarkHarness()
    result = asyncio.run(harness.run_benchmark())

    print("\n=== ANNABAN BENCHMARK REPORT ===")
    print(f"Tasks: {result['tasks']}")
    print(f"Failure Rate: {result['avg_failure_rate']:.3f}")
    print(f"Cost: ${result['avg_cost']:.4f}")
    print(f"Agreement: {result['avg_agreement']:.3f}")
    print(f"Governance Score: {result['annaban_governance_score']:.4f}")


if __name__ == "__main__":
    main()
