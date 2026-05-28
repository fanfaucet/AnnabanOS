def governance_score(avg_policy_pass: float, avg_cost: float, avg_audit_integrity: float) -> float:
    """Composite operational score; not an epistemic correctness score."""

    return (avg_policy_pass * avg_audit_integrity) / (1 + avg_cost)
