"""Multi-objective maritime route scoring."""

from collections.abc import Iterable, Mapping
from typing import Any

from annaban_maritime.core.state import MaritimeState


def score_route(distance: float, state: MaritimeState) -> float:
    """Score a candidate route, with higher scores indicating better fit."""

    return (
        -1.0 * distance * 0.6
        - 1.0 * state.weather_risk * 100
        - 1.0 * state.congestion * 80
        - 1.0 * state.ecological_zone * 120
        + 1.0 * state.priority * 150
    )


def choose_best_route(
    routes: Iterable[Mapping[str, Any]],
    state: MaritimeState,
) -> dict[str, Any] | None:
    """Return the highest-scoring route from an iterable of route mappings."""

    best: Mapping[str, Any] | None = None
    best_score = float("-inf")

    for route in routes:
        candidate_score = score_route(route["distance"], state)
        if candidate_score > best_score:
            best_score = candidate_score
            best = route

    if best is None:
        return None

    selected = dict(best)
    selected["score"] = best_score
    return selected
