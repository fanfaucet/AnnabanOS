"""FastAPI endpoints for the AnnabanOS Maritime core."""

from typing import Any

from fastapi import FastAPI, HTTPException, status

from annaban_business import get_business_profile
from annaban_evidence import create_evidence_envelope
from annaban_maritime.alignment.evaluator import evaluate_route
from annaban_maritime.api.schemas import (
    BestRouteRequest,
    BestRouteResponse,
    BusinessProfileResponse,
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

business_profile = get_business_profile()

app = FastAPI(
    title=f"{business_profile.operating_system} Maritime",
    version="0.2.0",
    description=f"{business_profile.organization} logistics API for {business_profile.owner}.",
)


def _to_vessel(payload: Any) -> Vessel:
    return Vessel(**payload.model_dump())


def _to_state(payload: Any) -> MaritimeState:
    return MaritimeState(**payload.model_dump())


def _to_weights(payload: Any) -> RouteScoringWeights:
    return RouteScoringWeights(**payload.model_dump())


def _evidence(payload: dict[str, Any], interpretation_status: str) -> dict[str, Any]:
    """Wrap a maritime result without granting downstream execution authority."""

    return create_evidence_envelope(
        source="annaban_maritime.api",
        source_type="deterministic_logistics_simulation",
        provenance="local-simulation-derived",
        payload=payload,
        interpretation_status=interpretation_status,
    ).as_dict()


@app.get("/business/profile", response_model=BusinessProfileResponse)
def business_profile_endpoint() -> dict[str, object]:
    """Return the Jacob Wayne Kinnaird business context for this service."""

    return business_profile.as_dict()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service health for deployment probes."""

    return HealthResponse(status="ok")


@app.post("/maritime/eta", response_model=EtaResponse)
def get_eta(request: EtaRequest) -> dict[str, Any]:
    """Estimate ETA for a vessel and destination coordinate."""

    state = _to_state(request.state) if request.state else None
    result = estimate_eta(
        _to_vessel(request.vessel),
        request.destination.model_dump(),
        uncertainty=request.uncertainty,
        state=state,
        current_factor=request.current_factor,
    )
    return {**result, "evidence": _evidence(result, "ETA_ESTIMATE")}


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

    return BestRouteResponse(
        route=selected,
        evidence=_evidence({"route": selected}, "ROUTE_SELECTION"),
    )


@app.post("/maritime/generate_routes", response_model=GeneratedRoutesResponse)
def generate_routes(request: GenerateRoutesRequest) -> GeneratedRoutesResponse:
    """Generate deterministic placeholder candidate routes for scoring."""

    routes = generate_candidate_routes(
        _to_vessel(request.vessel),
        request.destination.model_dump(),
        _to_state(request.state),
    )
    return GeneratedRoutesResponse(
        routes=routes,
        evidence=_evidence({"routes": routes}, "ROUTE_GENERATION"),
    )
