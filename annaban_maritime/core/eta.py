"""ETA estimation engine."""

from collections.abc import Mapping
from typing import Any

from annaban_maritime.core.vessel import Vessel
from annaban_maritime.utils.geo import haversine

KNOT_TO_KMH = 1.852
DEFAULT_UNCERTAINTY = 0.15


def estimate_eta(
    vessel: Vessel,
    destination: Mapping[str, float],
    uncertainty: float = DEFAULT_UNCERTAINTY,
) -> dict[str, float]:
    """Estimate ETA and a bounded uncertainty window in hours.

    This v1 model intentionally stays deterministic: distance is calculated via
    haversine and speed is converted from knots to km/h. More advanced models
    can layer in weather, current, draft, and port congestion adjustments later.
    """

    distance_km = haversine(
        vessel.lat,
        vessel.lon,
        destination["lat"],
        destination["lon"],
    )
    speed_kmh = vessel.speed_knots * KNOT_TO_KMH
    base_time = distance_km / max(speed_kmh, 1e-6)

    return {
        "distance_km": distance_km,
        "speed_kmh": speed_kmh,
        "eta_hours": base_time,
        "eta_lower": base_time * (1 - uncertainty),
        "eta_upper": base_time * (1 + uncertainty),
    }
