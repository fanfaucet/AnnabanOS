"""FastAPI endpoints for the AnnabanOS Maritime core."""

from typing import Any

from fastapi import FastAPI

from annaban_maritime.alignment.evaluator import evaluate_route
from annaban_maritime.core.eta import estimate_eta
from annaban_maritime.core.routing import choose_best_route
from annaban_maritime.core.state import MaritimeState
from annaban_maritime.core.vessel import Vessel

app = FastAPI(title="AnnabanOS Maritime", version="0.1.0")


@app.post("/maritime/eta")
def get_eta(vessel: dict[str, Any], destination: dict[str, float]) -> dict[str, float]:
    """Estimate ETA for a vessel and destination coordinate."""

    return estimate_eta(Vessel(**vessel), destination)


@app.post("/maritime/route_check")
def check_route(route: dict[str, Any], state: dict[str, float]) -> dict[str, Any]:
    """Run deterministic alignment checks for a candidate route."""

    return evaluate_route(route, MaritimeState(**state))


@app.post("/maritime/best_route")
def best_route(
    routes: list[dict[str, Any]],
    state: dict[str, float],
) -> dict[str, Any] | None:
    """Select the highest-scoring route for the current maritime state."""

    return choose_best_route(routes, MaritimeState(**state))
