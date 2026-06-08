"""FastAPI endpoints for the AnnabanOS Maritime core."""

from typing import Any

from fastapi import FastAPI, HTTPException, status

from annaban_maritime.alignment.evaluator import evaluate_route
from annaban_maritime.api.schemas import (
    BestRouteRequest,
    BestRouteResponse,
    EtaRequest,
    EtaResponse,
    GenerateRoutesRequest,
    GeneratedRoutesResponse,
    HealthResponse,
    RouteCheckRequest,
    RouteCheckResponse,
)
from annaban_maritime.core.eta import estimate_eta
from annaban_maritime.core.routing import (
    RouteScoringWeights,
    choose_best_route,
    generate_candidate_routes,
)
from annaban_maritime.core.state import MaritimeState
from annaban_maritime.core.vessel import Vessel

app = FastAPI(title="AnnabanOS Maritime", version="0.2.0")


def _to_vessel(payload: Any) -> Vessel:
    return Vessel(**payload.model_dump())


def _to_state(payload: Any) -> MaritimeState:
    return MaritimeState(**payload.model_dump())


def _to_weights(payload: Any) -> RouteScoringWeights:
    return RouteScoringWeights(**payload.model_dump())


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service health for deployment probes."""

    return HealthResponse(status="ok")


@app.post("/maritime/eta", response_model=EtaResponse)
def get_eta(request: EtaRequest) -> dict[str, float]:
    """Estimate ETA for a vessel and destination coordinate."""

    state = _to_state(request.state) if request.state else None
    return estimate_eta(
        _to_vessel(request.vessel),
        request.destination.model_dump(),
        uncertainty=request.uncertainty,
        state=state,
        current_factor=request.current_factor,
    )


@app.post("/maritime/route_check", response_model=RouteCheckResponse)
def check_route(request: RouteCheckRequest) -> dict[str, Any]:
    """Run deterministic alignment checks for a candidate route."""

    return evaluate_route(
        request.route.model_dump(exclude_none=True),
        _to_state(request.state),
    )


@app.post("/maritime/best_route", response_model=BestRouteResponse)
def best_route(request: BestRouteRequest) -> BestRouteResponse:
    """Select the highest-scoring route for the current maritime state."""

    routes = [route.model_dump(exclude_none=True) for route in request.routes]
    selected = choose_best_route(routes, _to_state(request.state), _to_weights(request.weights))
    if selected is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No candidate routes were provided.",
        )

    return BestRouteResponse(route=selected)


@app.post("/maritime/generate_routes", response_model=GeneratedRoutesResponse)
def generate_routes(request: GenerateRoutesRequest) -> GeneratedRoutesResponse:
    """Generate deterministic placeholder candidate routes for scoring."""

    routes = generate_candidate_routes(
        _to_vessel(request.vessel),
        request.destination.model_dump(),
        _to_state(request.state),
    )
    return GeneratedRoutesResponse(routes=routes)
