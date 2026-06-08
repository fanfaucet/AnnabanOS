"""Multi-objective maritime route scoring and candidate generation."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from annaban_maritime.core.state import MaritimeState
from annaban_maritime.core.vessel import Vessel
from annaban_maritime.utils.geo import bearing, haversine


@dataclass(frozen=True)
class RouteScoringWeights:
    """Configurable weights for deterministic route scoring."""

    distance: float = 0.6
    weather_risk: float = 100.0
    congestion: float = 80.0
    ecological_zone: float = 120.0
    priority: float = 150.0


def _route_value(route: Mapping[str, Any], key: str, fallback: float) -> float:
    value = route.get(key, fallback)
    return float(value)


def score_route(
    distance: float,
    state: MaritimeState,
    weights: RouteScoringWeights | None = None,
    route: Mapping[str, Any] | None = None,
) -> float:
    """Score a candidate route, with higher scores indicating better fit.

    ``weights`` makes the formerly hardcoded policy tradeoffs explicit and
    configurable. If a route carries route-specific risk signals, those values
    override the global state for scoring that candidate.
    """

    weights = weights or RouteScoringWeights()
    route = route or {}
    weather_risk = _route_value(route, "weather_risk", state.weather_risk)
    congestion = _route_value(route, "congestion", state.congestion)
    ecological_zone = _route_value(route, "ecological_zone_crossing", state.ecological_zone)
    priority = _route_value(route, "priority", state.priority)

    return (
        -distance * weights.distance
        - weather_risk * weights.weather_risk
        - congestion * weights.congestion
        - ecological_zone * weights.ecological_zone
        + priority * weights.priority
    )


def choose_best_route(
    routes: Iterable[Mapping[str, Any]],
    state: MaritimeState,
    weights: RouteScoringWeights | None = None,
) -> dict[str, Any] | None:
    """Return the highest-scoring route from an iterable of route mappings."""

    best: Mapping[str, Any] | None = None
    best_score = float("-inf")

    for route in routes:
        distance = float(route["distance"])
        candidate_score = score_route(distance, state, weights, route)
        if candidate_score > best_score:
            best_score = candidate_score
            best = route

    if best is None:
        return None

    selected = dict(best)
    selected["score"] = best_score
    return selected


def generate_candidate_routes(
    vessel: Vessel,
    destination: Mapping[str, float],
    state: MaritimeState,
) -> list[dict[str, Any]]:
    """Generate deterministic placeholder route candidates.

    This is not a nautical chart router. It provides stable candidates that let
    callers exercise downstream scoring, ETA, and policy flows until a real
    route-generation backend is connected.
    """

    direct_distance = haversine(vessel.lat, vessel.lon, destination["lat"], destination["lon"])
    initial_bearing = bearing(vessel.lat, vessel.lon, destination["lat"], destination["lon"])

    return [
        {
            "route_id": "direct",
            "distance": direct_distance,
            "bearing": initial_bearing,
            "weather_risk": state.weather_risk,
            "congestion": state.congestion,
            "ecological_zone_crossing": state.ecological_zone,
            "priority": state.priority,
        },
        {
            "route_id": "weather_avoidance",
            "distance": direct_distance * 1.12,
            "bearing": initial_bearing,
            "weather_risk": max(0.0, state.weather_risk - 0.25),
            "congestion": state.congestion,
            "ecological_zone_crossing": state.ecological_zone,
            "priority": state.priority,
        },
        {
            "route_id": "eco_avoidance",
            "distance": direct_distance * 1.18,
            "bearing": initial_bearing,
            "weather_risk": state.weather_risk,
            "congestion": max(0.0, state.congestion - 0.10),
            "ecological_zone_crossing": max(0.0, state.ecological_zone - 0.35),
            "priority": state.priority,
        },
    ]
