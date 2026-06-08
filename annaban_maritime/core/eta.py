"""ETA estimation engine."""

from collections.abc import Mapping

from annaban_maritime.core.state import MaritimeState
from annaban_maritime.core.vessel import Vessel
from annaban_maritime.utils.geo import haversine

KNOT_TO_KMH = 1.852
DEFAULT_UNCERTAINTY = 0.15
MIN_EFFECTIVE_SPEED_KMH = 1e-6


def estimate_eta(
    vessel: Vessel,
    destination: Mapping[str, float],
    uncertainty: float = DEFAULT_UNCERTAINTY,
    state: MaritimeState | None = None,
    current_factor: float = 0.0,
) -> dict[str, float]:
    """Estimate ETA and a bounded uncertainty window in hours.

    The model remains deterministic, but it now accepts operational context:

    - ``state.weather_risk`` slows effective speed and widens uncertainty.
    - ``state.congestion`` adds port/traffic delay and widens uncertainty.
    - low ``vessel.fuel_level`` adds a conservative speed penalty.
    - ``current_factor`` represents favorable/adverse current as a normalized
      value from -1.0 to 1.0; positive current helps speed, negative current
      slows it.
    """

    distance_km = haversine(
        vessel.lat,
        vessel.lon,
        destination["lat"],
        destination["lon"],
    )
    base_speed_kmh = vessel.speed_knots * KNOT_TO_KMH

    weather_risk = state.weather_risk if state else 0.0
    congestion = state.congestion if state else 0.0
    current_factor = max(-1.0, min(1.0, current_factor))
    fuel_penalty = max(0.0, 0.2 - vessel.fuel_level) * 0.75

    speed_multiplier = max(
        0.2,
        1.0 - (weather_risk * 0.35) - fuel_penalty + (current_factor * 0.15),
    )
    effective_speed_kmh = max(base_speed_kmh * speed_multiplier, MIN_EFFECTIVE_SPEED_KMH)
    transit_hours = distance_km / effective_speed_kmh
    congestion_delay_hours = congestion * 2.0
    eta_hours = transit_hours + congestion_delay_hours
    effective_uncertainty = min(0.75, uncertainty + weather_risk * 0.20 + congestion * 0.10)

    return {
        "distance_km": distance_km,
        "speed_kmh": base_speed_kmh,
        "effective_speed_kmh": effective_speed_kmh,
        "congestion_delay_hours": congestion_delay_hours,
        "eta_hours": eta_hours,
        "eta_lower": eta_hours * (1 - effective_uncertainty),
        "eta_upper": eta_hours * (1 + effective_uncertainty),
        "uncertainty": effective_uncertainty,
    }
