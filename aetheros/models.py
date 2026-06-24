"""Typed contracts for AetherOS API emulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from core.contracts import JurisdictionScope, VisibilityScope


class APIVersion(str, Enum):
    """Supported AetherOS emulator API versions."""

    V1 = "v1"


def versioned_route(path: str, version: APIVersion = APIVersion.V1) -> str:
    """Build a stable versioned API route."""
    return f"/api/{version.value}{path}"


class AetherOSMode(str, Enum):
    """Dashboard/API visibility modes aligned with AetherOS views."""

    SOVEREIGN = "sovereign"
    COALITION = "coalition"
    EMERGENCY = "emergency"
    SIMULATION_ONLY = "simulation_only"


class AetherOSRoute(str, Enum):
    """Versioned emulated advisory API routes; none are command/control paths."""

    STATUS = versioned_route("/aetheros/status")
    FEDERATED_EVENTS = versioned_route("/aetheros/federated-events")
    ANNABANOS_EXECUTION = versioned_route("/annabanos/execution")
    ANNABANAI_AUTOMATION = versioned_route("/annabanai/automation")
    ANNABAN_BOOT = versioned_route("/annaban/boot-simulation")


@dataclass(frozen=True)
class AetherOSRequest:
    """A scoped request for the local AetherOS emulator."""

    route: AetherOSRoute
    scope: JurisdictionScope
    payload: dict[str, Any] = field(default_factory=dict)
    mode: AetherOSMode = AetherOSMode.SOVEREIGN
    request_id: str = field(default_factory=lambda: str(uuid4()))
    version: APIVersion = APIVersion.V1

    def validate_scope_mode(self) -> None:
        if self.scope.is_expired():
            raise ValueError("Visibility scope has expired")
        if self.mode == AetherOSMode.SIMULATION_ONLY and self.scope.visibility != VisibilityScope.SIMULATION_ONLY:
            raise ValueError("Simulation-only mode requires simulation-only visibility scope")
