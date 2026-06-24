"""AnnabanOS execution engine — simulation-only evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.contracts import JurisdictionScope


@dataclass(frozen=True)
class ExecutionResult:
    """Immutable result of a simulation-scoped execution."""

    status: str = "simulated"
    jurisdiction_id: str = ""
    outputs: dict[str, Any] = field(default_factory=dict)
    audit_metadata: dict[str, Any] = field(default_factory=dict)


class AnnabanExecutionEngine:
    """Evaluate payloads in a simulation-only advisory context.

    Never issues binding operational commands. All outputs carry
    rationale, confidence, and audit metadata.
    """

    def evaluate_payload(
        self,
        payload: dict[str, Any],
        scope: JurisdictionScope,
    ) -> ExecutionResult:
        rationale = payload.get("rationale", "No rationale provided")
        confidence = payload.get("confidence", 0.0)

        return ExecutionResult(
            status="simulated",
            jurisdiction_id=scope.jurisdiction_id,
            outputs={
                "rationale": rationale,
                "confidence": confidence,
                "affected_constraints": payload.get("constraints", []),
                "projected_tradeoffs": payload.get("tradeoffs", {}),
            },
            audit_metadata={
                "timestamp": "2026-06-25T00:00:00Z",
                "scope": {
                    "jurisdiction_id": scope.jurisdiction_id,
                    "visibility": scope.visibility.value,
                },
                "capability_class": "simulation",
                "advisory_only": True,
            },
        )
