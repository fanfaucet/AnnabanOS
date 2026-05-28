def build_report(result: dict) -> str:
    return (
        "=== ANNABAN BENCHMARK REPORT ===\n"
        f"Tasks: {result['tasks']}\n"
        f"Failure Rate: {result['avg_failure_rate']:.3f}\n"
        f"Cost: ${result['avg_cost']:.4f}\n"
        f"Agreement: {result['avg_agreement']:.3f}\n"
        f"Governance Score: {result['annaban_governance_score']:.4f}"
    )
