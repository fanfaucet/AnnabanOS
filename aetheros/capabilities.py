"""Capability policy layer for the AetherOS emulator."""

from __future__ import annotations

from core.contracts import CapabilityClass, capability_allows
from aetheros.models import AetherOSRoute


ROUTE_CAPABILITIES: dict[AetherOSRoute, CapabilityClass] = {
    AetherOSRoute.STATUS: CapabilityClass.READ_ONLY,
    AetherOSRoute.FEDERATED_EVENTS: CapabilityClass.READ_ONLY,
    AetherOSRoute.ANNABANOS_EXECUTION: CapabilityClass.SIMULATION,
    AetherOSRoute.ANNABANAI_AUTOMATION: CapabilityClass.ADVISORY,
    AetherOSRoute.ANNABAN_BOOT: CapabilityClass.SIMULATION,
}


class CapabilityPolicy:
    """Enforce route capability ceilings before delegated evaluation."""

    def capability_for_route(self, route: AetherOSRoute) -> CapabilityClass:
        return ROUTE_CAPABILITIES[route]

    def requested_capability(self, payload: dict, default: CapabilityClass) -> CapabilityClass:
        raw = payload.get("capability", default.value)
        return CapabilityClass(raw)

    def validate(self, route: AetherOSRoute, payload: dict) -> None:
        maximum = self.capability_for_route(route)
        requested = self.requested_capability(payload, maximum)
        if not capability_allows(maximum, requested):
            raise ValueError(f"Requested capability {requested.value} exceeds route ceiling {maximum.value}")
