"""Shared contracts across AnnabanOS, AetherOS, and AnnabanAI packages.

These types define jurisdiction-scoped, visibility-aware, advisory-only boundaries
used by the emulator, benchmark suite, and automation bridges.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional


class CapabilityClass(str, Enum):
    """Capability ceiling classes for route enforcement.

    Higher classes do NOT imply more authority; they describe the
    *nature* of access. SIMULATION and ADVISORY are the only
    classes that produce actionable output, and both are
    explicitly non-binding.
    """

    READ_ONLY = "read_only"
    SIMULATION = "simulation"
    ADVISORY = "advisory"


class VisibilityScope(str, Enum):
    """Visibility scopes aligned with jurisdiction sovereignty."""

    SOVEREIGN = "sovereign"
    COALITION = "coalition"
    EMERGENCY = "emergency"
    SIMULATION_ONLY = "simulation_only"


@dataclass(frozen=True)
class JurisdictionScope:
    """A jurisdiction-scoped visibility container.

    Carries metadata about which jurisdiction owns the request and
    how widely the result may be visible.
    """

    jurisdiction_id: str
    visibility: VisibilityScope = VisibilityScope.SOVEREIGN
    expires_at: Optional[datetime] = field(default=None)

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @staticmethod
    def sovereign(jurisdiction_id: str, ttl_seconds: int = 3600) -> JurisdictionScope:
        return JurisdictionScope(
            jurisdiction_id=jurisdiction_id,
            visibility=VisibilityScope.SOVEREIGN,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
        )

    @staticmethod
    def simulation_only(jurisdiction_id: str, ttl_seconds: int = 3600) -> JurisdictionScope:
        return JurisdictionScope(
            jurisdiction_id=jurisdiction_id,
            visibility=VisibilityScope.SIMULATION_ONLY,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
        )


def capability_allows(maximum: CapabilityClass, requested: CapabilityClass) -> bool:
    """Check whether a requested capability is allowed within a maximum ceiling.

    Ordering (most to least permissive for advisory action):
        ADVISORY >= SIMULATION >= READ_ONLY
    """
    order = [CapabilityClass.READ_ONLY, CapabilityClass.SIMULATION, CapabilityClass.ADVISORY]
    try:
        max_index = order.index(maximum)
        req_index = order.index(requested)
    except ValueError:
        return False
    return req_index <= max_index
