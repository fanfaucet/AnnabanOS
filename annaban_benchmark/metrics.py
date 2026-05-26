def governance_score(avg_failure: float, avg_cost: float, avg_agreement: float) -> float:
    return (1 - avg_failure) * avg_agreement / (1 + avg_cost)
