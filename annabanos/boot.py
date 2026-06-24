"""AnnabanOS boot simulation — deterministic startup emulation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from core.contracts import JurisdictionScope
from annabanos.integration import AnnabanAIAutomationBridge


@dataclass(frozen=True)
class BootResult:
    """Result of a boot simulation."""

    phase: str = "simulated_boot"
    services: list[str] = field(default_factory=list)
    jurisdiction_id: str = ""
    advisory_only: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class AnnabanBootSimulator:
    """Simulate AnnabanOS boot sequences without operational side effects.

    All boot phases are deterministic and emit advisory-only events.
    """

    def __init__(self, automation_bridge: AnnabanAIAutomationBridge | None = None) -> None:
        self.automation_bridge = automation_bridge or AnnabanAIAutomationBridge()

    def simulate(
        self,
        scope: JurisdictionScope,
        payload: dict[str, Any] | None = None,
    ) -> BootResult:
        services = payload.get("services", ["orchestrator", "router", "audit"]) if payload else ["orchestrator", "router", "audit"]

        return BootResult(
            phase="simulated_boot_complete",
            services=services,
            jurisdiction_id=scope.jurisdiction_id,
            advisory_only=True,
            metadata={
                "boot_mode": "simulation",
                "visibility": scope.visibility.value,
                "services_initialized": len(services),
            },
        )

    def as_dict(self, result: BootResult) -> dict[str, Any]:
        return asdict(result)
