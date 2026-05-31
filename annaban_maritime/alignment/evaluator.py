"""Deterministic alignment evaluator for maritime routes."""

from collections.abc import Mapping
from typing import Any

from annaban_maritime.alignment.policy import Policy
from annaban_maritime.core.state import MaritimeState


def _coerce_state(state: MaritimeState | Mapping[str, float]) -> MaritimeState:
    if isinstance(state, MaritimeState):
        return state
    return MaritimeState(**state)


def evaluate_route(
    route: Mapping[str, Any],
    state: MaritimeState | Mapping[str, float],
) -> dict[str, Any]:
    """Evaluate whether a route satisfies deterministic safety policies."""

    maritime_state = _coerce_state(state)
    ecological_crossing = route.get("ecological_zone_crossing", maritime_state.ecological_zone)
    risk_score = route.get("risk_score", maritime_state.weather_risk)

    violations: list[str] = []
    policies: list[str] = []

    if ecological_crossing > 0.5:
        violations.append("eco_violation")
        policies.append(Policy.ECO_PROTECTION.value)

    if risk_score > 0.8:
        violations.append("safety_risk")
        policies.append(Policy.DO_NO_HARM.value)

    alignment_score = max(0.0, 1.0 - (len(violations) * 0.25))

    return {
        "approved": alignment_score > 0.5,
        "alignment_score": alignment_score,
        "violations": violations,
        "policies_triggered": policies,
        "priority": maritime_state.priority,
    }
