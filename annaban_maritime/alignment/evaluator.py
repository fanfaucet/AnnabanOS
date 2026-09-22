"""Deterministic alignment evaluator for maritime routes."""

from collections.abc import Mapping
from typing import Any

from annaban_evidence import create_evidence_envelope
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
    """Evaluate a route while preserving evidence and authority boundaries.

    An evaluation is an interpretation and recommendation only. It never
    grants execution authority; callers must complete human review separately.
    """

    maritime_state = _coerce_state(state)
    observations: dict[str, dict[str, Any]] = {}
    ecological_crossing = route.get("ecological_zone_crossing")
    if ecological_crossing is None:
        observations["ecological_zone_crossing"] = {"status": "MISSING", "value": None}
    else:
        ecological_crossing = float(ecological_crossing)
        observations["ecological_zone_crossing"] = {"status": "OBSERVED", "value": ecological_crossing}

    risk_score = route.get("risk_score")
    if risk_score is None:
        weather_risk = float(route.get("weather_risk", maritime_state.weather_risk))
        congestion = float(route.get("congestion", maritime_state.congestion))
        risk_score = max(weather_risk, congestion)
        observations["risk_score"] = {
            "status": "DERIVED",
            "value": risk_score,
            "method": "max(weather_risk, congestion)",
            "inputs": {"weather_risk": weather_risk, "congestion": congestion},
        }
    else:
        risk_score = float(risk_score)
        observations["risk_score"] = {"status": "OBSERVED", "value": risk_score}

    violations: list[str] = []
    policies: list[str] = []

    if ecological_crossing is None:
        violations.append("missing_ecological_crossing")
        policies.append(Policy.ECO_PROTECTION.value)
    elif ecological_crossing > 0.5:
        violations.append("eco_violation")
        policies.append(Policy.ECO_PROTECTION.value)

    if risk_score > 0.8:
        violations.append("safety_risk")
        policies.append(Policy.DO_NO_HARM.value)

    alignment_score = max(0.0, 1.0 - (len(violations) * 0.25))
    if "eco_violation" in violations or "safety_risk" in violations:
        recommendation = "NOT_RECOMMENDED"
    elif violations:
        recommendation = "REQUIRES_REVIEW"
    else:
        recommendation = "CONDITIONALLY_ACCEPTABLE"

    result = {
        "alignment_score": alignment_score,
        "violations": violations,
        "policies_triggered": policies,
        "priority": maritime_state.priority,
        "observations": observations,
        "recommendation": recommendation,
        "authorization_status": "NOT_AUTHORIZED",
        "human_review_status": "REQUIRED",
    }

    result["evidence"] = create_evidence_envelope(
        source="annaban_maritime.alignment.evaluator",
        source_type="deterministic_policy_evaluation",
        provenance="local-simulation-derived",
        payload=result.copy(),
        interpretation_status="POLICY_RECOMMENDATION",
    ).as_dict()
    return result
