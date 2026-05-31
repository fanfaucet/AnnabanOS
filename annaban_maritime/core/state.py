"""Environmental and operational state for maritime decisions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MaritimeState:
    """Normalized route context used by scoring and policy engines.

    All values are expected to be in the 0..1 range, where larger values mean
    more of that signal. ``priority`` represents a humanitarian or business
    priority boost rather than risk.
    """

    weather_risk: float
    congestion: float
    ecological_zone: float
    priority: float
