"""Local AetherOS API emulator with AnnabanOS and AnnabanAI integration.

The emulator is intentionally in-process and deterministic for tests. It provides
integration boundaries without exposing operational command paths.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from aetheros.capabilities import CapabilityPolicy
from aetheros.models import AetherOSRequest, AetherOSRoute
from annabanos.boot import AnnabanBootSimulator
from annabanos.execution import AnnabanExecutionEngine
from annabanos.integration import AnnabanAIAutomationBridge


@dataclass(frozen=True)
class AetherOSResponse:
    """Normalized emulated API response."""

    request_id: str
    status_code: int
    route: str
    advisory_only: bool
    body: dict[str, Any]
    errors: list[str] = field(default_factory=list)


class AetherOSAPIEmulator:
    """Route scoped AetherOS requests to advisory-only local components."""

    def __init__(
        self,
        execution_engine: AnnabanExecutionEngine | None = None,
        automation_bridge: AnnabanAIAutomationBridge | None = None,
        boot_simulator: AnnabanBootSimulator | None = None,
        capability_policy: CapabilityPolicy | None = None,
    ) -> None:
        self.execution_engine = execution_engine or AnnabanExecutionEngine()
        self.automation_bridge = automation_bridge or AnnabanAIAutomationBridge()
        self.boot_simulator = boot_simulator or AnnabanBootSimulator(self.automation_bridge)
        self.capability_policy = capability_policy or CapabilityPolicy()
        self._events: list[dict[str, Any]] = []

    def handle(self, request: AetherOSRequest) -> AetherOSResponse:
        try:
            request.validate_scope_mode()
            self.capability_policy.validate(request.route, request.payload)
            if request.route == AetherOSRoute.STATUS:
                return self._status(request)
            if request.route == AetherOSRoute.FEDERATED_EVENTS:
                return self._federated_events(request)
            if request.route == AetherOSRoute.ANNABANOS_EXECUTION:
                return self._annabanos_execution(request)
            if request.route == AetherOSRoute.ANNABANAI_AUTOMATION:
                return self._annabanai_automation(request)
            if request.route == AetherOSRoute.ANNABAN_BOOT:
                return self._annaban_boot(request)
            return self._error(request, 404, "Unknown AetherOS route")
        except Exception as exc:
            return self._error(request, 400, str(exc))

    def publish_event(self, event: dict[str, Any]) -> None:
        if event.get("advisory_only") is not True:
            raise ValueError("AetherOS events must be advisory-only")
        self._events.append(dict(event))

    def _status(self, request: AetherOSRequest) -> AetherOSResponse:
        return AetherOSResponse(
            request_id=request.request_id,
            status_code=200,
            route=request.route.value,
            advisory_only=True,
            body={
                "service": "aetheros-api-emulator",
                "mode": request.mode.value,
                "jurisdiction_id": request.scope.jurisdiction_id,
                "routes": [route.value for route in AetherOSRoute],
                "capabilities": {route.value: self.capability_policy.capability_for_route(route).value for route in AetherOSRoute},
                "constraints": ["advisory_only", "no_sensor_control", "no_binding_commands"],
            },
        )

    def _federated_events(self, request: AetherOSRequest) -> AetherOSResponse:
        visible = [
            event
            for event in self._events
            if event.get("jurisdiction_id") == request.scope.jurisdiction_id
            or request.mode.value in {"coalition", "emergency", "simulation_only"}
        ]
        return AetherOSResponse(request.request_id, 200, request.route.value, True, {"events": visible})

    def _annabanos_execution(self, request: AetherOSRequest) -> AetherOSResponse:
        result = self.execution_engine.evaluate_payload(request.payload, request.scope)
        return AetherOSResponse(
            request.request_id,
            200,
            request.route.value,
            True,
            {"execution_result": asdict(result)},
        )

    def _annabanai_automation(self, request: AetherOSRequest) -> AetherOSResponse:
        result = self.automation_bridge.process_payload(request.payload, request.scope)
        return AetherOSResponse(
            request.request_id,
            200,
            request.route.value,
            True,
            {"automation_result": result},
        )

    def _annaban_boot(self, request: AetherOSRequest) -> AetherOSResponse:
        result = self.boot_simulator.simulate(request.scope, request.payload)
        return AetherOSResponse(
            request.request_id,
            200,
            request.route.value,
            True,
            {"boot_result": self.boot_simulator.as_dict(result)},
        )

    def _error(self, request: AetherOSRequest, status_code: int, message: str) -> AetherOSResponse:
        return AetherOSResponse(
            request_id=request.request_id,
            status_code=status_code,
            route=request.route.value,
            advisory_only=True,
            body={"message": message},
            errors=[message],
        )
