"""AIS-style vessel state model for maritime planning."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Vessel:
    """Current vessel telemetry and cargo context."""

    vessel_id: str
    lat: float
    lon: float
    speed_knots: float
    fuel_level: float
    cargo_type: str
