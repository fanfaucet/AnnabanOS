def agreement_score(outputs: list[str]) -> float:
    if not outputs:
        return 0.0
    top = max(outputs.count(v) for v in set(outputs))
    return round(top / len(outputs), 4)
