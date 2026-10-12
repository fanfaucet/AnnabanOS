"""Toy Kardashev-II power budget and governance guard.

This is a conceptual simulation only. It does not model a feasible megastructure,
control real infrastructure, or imply review/endorsement by any public figure.
Standard library only; Python 3.10+.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import json
import math
from typing import Any

SOLAR_LUMINOSITY_W = 3.83e26


class GovernanceState(str, Enum):
    SIMULATION_ONLY = "SIMULATION_ONLY"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class Scenario:
    name: str
    capture_fraction: float
    conversion_efficiency: float
    transmission_efficiency: float = 1.0

    def validate(self) -> None:
        for field_name, value in (
            ("capture_fraction", self.capture_fraction),
            ("conversion_efficiency", self.conversion_efficiency),
            ("transmission_efficiency", self.transmission_efficiency),
        ):
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be finite and between 0 and 1")


@dataclass(frozen=True)
class PowerBudget:
    scenario: str
    stellar_output_w: float
    captured_power_w: float
    conversion_loss_w: float
    converted_power_w: float
    transmission_loss_w: float
    delivered_power_w: float
    governance_state: GovernanceState
    external_effects_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["governance_state"] = self.governance_state.value
        return result


def calculate_power(
    scenario: Scenario,
    stellar_output_w: float = SOLAR_LUMINOSITY_W,
) -> PowerBudget:
    """Calculate idealized power flows; never authorizes external action."""
    scenario.validate()
    if not math.isfinite(stellar_output_w) or stellar_output_w < 0:
        raise ValueError("stellar_output_w must be finite and non-negative")

    captured = stellar_output_w * scenario.capture_fraction
    converted = captured * scenario.conversion_efficiency
    delivered = converted * scenario.transmission_efficiency
    return PowerBudget(
        scenario=scenario.name,
        stellar_output_w=stellar_output_w,
        captured_power_w=captured,
        conversion_loss_w=captured - converted,
        converted_power_w=converted,
        transmission_loss_w=converted - delivered,
        delivered_power_w=delivered,
        governance_state=GovernanceState.SIMULATION_ONLY,
        external_effects_enabled=False,
    )


def governance_gate(
    *,
    evidence_validated: bool,
    human_authorized: bool,
    simulation_mode: bool = True,
) -> GovernanceState:
    """Fail closed: model output alone is never sufficient authority."""
    if simulation_mode:
        return GovernanceState.SIMULATION_ONLY
    if not evidence_validated:
        return GovernanceState.BLOCKED
    if not human_authorized:
        return GovernanceState.REVIEW_REQUIRED
    # Even an authorized record does not switch on external infrastructure here.
    return GovernanceState.REVIEW_REQUIRED


def hypothetical_review_lenses(budget: PowerBudget) -> dict[str, Any]:
    """Illustrative review prompts, not statements from Elon Musk or anyone else."""
    return {
        "label": "SIMULATED_PUBLIC_FIGURE_LENS_NOT_ACTUAL_REVIEW",
        "person": "Elon Musk",
        "actual_participation_or_endorsement": False,
        "observed_input": "Only the supplied toy power-budget assumptions",
        "engineering_scale": {
            "delivered_power_w": budget.delivered_power_w,
            "note": "Check collector area, orbital dynamics, materials, maintenance, and heat rejection.",
        },
        "systems_reliability": {
            "note": "Specify fault isolation, degradation, safe states, and independently tested interfaces."
        },
        "economics": {
            "valuation_assigned": False,
            "note": "Power magnitude alone does not establish cost, feasibility, revenue, or asset value.",
        },
        "governance": {
            "state": budget.governance_state.value,
            "external_effects_enabled": budget.external_effects_enabled,
            "invariant": "POWER_ESTIMATE != AUTHORITY",
        },
    }


def demo_report() -> dict[str, Any]:
    scenario = Scenario(
        name="mature_10pct_capture",
        capture_fraction=0.10,
        conversion_efficiency=0.80,
        transmission_efficiency=0.95,
    )
    budget = calculate_power(scenario)
    return {
        "status": "SIMULATION_ONLY_NOT_A_FEASIBILITY_FINDING",
        "budget": budget.to_dict(),
        "review_lens": hypothetical_review_lenses(budget),
    }


if __name__ == "__main__":
    print(json.dumps(demo_report(), indent=2, sort_keys=True))
