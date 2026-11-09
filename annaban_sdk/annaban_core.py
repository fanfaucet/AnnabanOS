"""Core SDK primitives: bounded context, fail-closed gate, hash-chained ledger."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
import time
import uuid
from typing import Any, Mapping


class GateDecision(str, Enum):
    ALLOW_ADVISORY = "ALLOW_ADVISORY"
    SAFE_HOLD = "SAFE_HOLD"
    HUMAN_APPROVAL_REQUIRED = "HUMAN_APPROVAL_REQUIRED"


@dataclass(frozen=True)
class SDKContext:
    """Request context; it grants no external authority by itself."""
    actor_id: str
    request_id: str
    simulation: bool = True
    external_effects_enabled: bool = False

    def __post_init__(self) -> None:
        if not self.actor_id.strip() or not self.request_id.strip():
            raise ValueError("actor_id and request_id are required")
        if self.external_effects_enabled and self.simulation:
            raise ValueError("simulation contexts cannot enable external effects")


@dataclass(frozen=True)
class EventRecord:
    sequence: int
    event_id: str
    timestamp: float
    actor_id: str
    event_type: str
    payload: Mapping[str, Any]
    previous_hash: str
    event_hash: str


class AuditLedger:
    """Process-local hash chain; not durable storage or a trusted timestamp."""
    GENESIS = "GENESIS"

    def __init__(self) -> None:
        self._events: list[EventRecord] = []

    @property
    def events(self) -> tuple[EventRecord, ...]:
        return tuple(self._events)

    def append(self, actor_id: str, event_type: str, payload: Mapping[str, Any]) -> EventRecord:
        if not actor_id.strip() or not event_type.strip():
            raise ValueError("actor_id and event_type are required")
        # Round-trip to reject non-JSON values and detach mutable caller objects.
        safe_payload = json.loads(json.dumps(dict(payload), sort_keys=True, allow_nan=False))
        previous = self._events[-1].event_hash if self._events else self.GENESIS
        body = {
            "sequence": len(self._events) + 1,
            "event_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "actor_id": actor_id,
            "event_type": event_type,
            "payload": safe_payload,
            "previous_hash": previous,
        }
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        record = EventRecord(**body, event_hash=digest)
        self._events.append(record)
        return record

    def verify(self) -> bool:
        previous = self.GENESIS
        for index, event in enumerate(self._events, start=1):
            if event.sequence != index or event.previous_hash != previous:
                return False
            body = asdict(event)
            digest = body.pop("event_hash")
            canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False)
            if hashlib.sha256(canonical.encode("utf-8")).hexdigest() != digest:
                return False
            previous = digest
        return True


def authorize_effect(*, context: SDKContext, human_approved: bool, policy_allowed: bool) -> GateDecision:
    """Require explicit approval and policy permission; no action is executed."""
    if not policy_allowed:
        return GateDecision.SAFE_HOLD
    if context.simulation or not context.external_effects_enabled:
        return GateDecision.ALLOW_ADVISORY
    if not human_approved:
        return GateDecision.HUMAN_APPROVAL_REQUIRED
    return GateDecision.ALLOW_ADVISORY
