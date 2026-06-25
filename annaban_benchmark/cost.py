class CostTracker:
    def __init__(self):
        self.total_cost = {}

    def record(self, model, usage):
        cost = usage.get("cost", 0.0)
        self.total_cost[model] = self.total_cost.get(model, 0.0) + cost

    def get_total(self):
        return sum(self.total_cost.values())


def total_cost(items):
    """Aggregate cost fields from benchmark records."""
    return sum(float(item.get("cost", 0.0)) for item in items)
