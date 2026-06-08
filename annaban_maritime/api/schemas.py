"""Pydantic request and response models for the maritime API."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class VesselModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vessel_id: str = Field(min_length=1)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    speed_knots: float = Field(ge=0)
    fuel_level: float = Field(ge=0, le=1)
    cargo_type: str = Field(min_length=1)


class DestinationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class MaritimeStateModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weather_risk: float = Field(ge=0, le=1)
    congestion: float = Field(ge=0, le=1)
    ecological_zone: float = Field(ge=0, le=1)
    priority: float = Field(ge=0, le=1)


class RouteScoringWeightsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    distance: float = Field(default=0.6, ge=0)
    weather_risk: float = Field(default=100.0, ge=0)
    congestion: float = Field(default=80.0, ge=0)
    ecological_zone: float = Field(default=120.0, ge=0)
    priority: float = Field(default=150.0, ge=0)


class EtaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vessel: VesselModel
    destination: DestinationModel
    state: MaritimeStateModel | None = None
    current_factor: float = Field(default=0.0, ge=-1, le=1)
    uncertainty: float = Field(default=0.15, ge=0, le=0.75)


class EtaResponse(BaseModel):
    distance_km: float
    speed_kmh: float
    effective_speed_kmh: float
    congestion_delay_hours: float
    eta_hours: float
    eta_lower: float
    eta_upper: float
    uncertainty: float


class RouteModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    route_id: str | None = None
    distance: float | None = Field(default=None, ge=0)
    ecological_zone_crossing: float | None = Field(default=None, ge=0, le=1)
    risk_score: float | None = Field(default=None, ge=0, le=1)
    weather_risk: float | None = Field(default=None, ge=0, le=1)
    congestion: float | None = Field(default=None, ge=0, le=1)
    priority: float | None = Field(default=None, ge=0, le=1)


class CandidateRouteModel(RouteModel):
    distance: float = Field(ge=0)


class RouteCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    route: RouteModel
    state: MaritimeStateModel


class RouteCheckResponse(BaseModel):
    approved: bool
    alignment_score: float
    violations: list[str]
    policies_triggered: list[str]
    priority: float


class BestRouteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    routes: list[CandidateRouteModel] = Field(min_length=1)
    state: MaritimeStateModel
    weights: RouteScoringWeightsModel = Field(default_factory=RouteScoringWeightsModel)


class GenerateRoutesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vessel: VesselModel
    destination: DestinationModel
    state: MaritimeStateModel


class BestRouteResponse(BaseModel):
    route: dict[str, Any]


class GeneratedRoutesResponse(BaseModel):
    routes: list[dict[str, Any]]


class HealthResponse(BaseModel):
    status: Literal["ok"]
