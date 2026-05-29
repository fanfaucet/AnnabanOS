def build_report(result: dict) -> str:
    return (
        "=== ANNABAN GOVERNANCE BENCHMARK ===\n"
        f"Tasks: {result['tasks']}\n"
        f"Policy Pass: {result['avg_policy_pass']:.3f}\n"
        f"Cost: ${result['avg_cost']:.4f}\n"
        f"Agreement Signal: {result['avg_agreement_signal']:.3f}\n"
        f"Audit Integrity: {result['avg_audit_integrity']:.3f}\n"
        f"Governance Score: {result['annaban_governance_score']:.4f}\n"
        f"{result['note']}"
    )
