"""Minimal human-authorization gate for bounded, local state changes.

This module is a demonstration, not a production security boundary.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Callable

class GateError(ValueError):
    """Raised when a request violates the authority-gate protocol."""

@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    actor: str
    key: str
    value: Any
    status: str = "pending"

class HumanAuthorityGate:
    """Require a human decision before an allowlisted state update."""
    def __init__(self, *, allowed_keys: set[str], initial_state: dict[str, Any] | None = None, clock: Callable[[], datetime] | None = None) -> None:
        if not allowed_keys:
            raise GateError("allowed_keys must not be empty")
        self._allowed_keys = frozenset(allowed_keys)
        self.state: dict[str, Any] = dict(initial_state or {})
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._proposals: dict[str, Proposal] = {}
        self.events: list[dict[str, Any]] = []
        self._last_hash = "0" * 64

    def propose(self, *, proposal_id: str, actor: str, key: str, value: Any) -> Proposal:
        if not proposal_id.strip() or not actor.strip():
            raise GateError("proposal_id and actor are required")
        if proposal_id in self._proposals:
            raise GateError("proposal_id must be unique")
        if key not in self._allowed_keys:
            raise GateError(f"key is not allowlisted: {key}")
        proposal = Proposal(proposal_id, actor, key, value)
        self._proposals[proposal_id] = proposal
        self._record("proposal_created", {"proposal_id": proposal_id, "actor": actor, "key": key, "value": value})
        return proposal

    def decide(self, *, proposal_id: str, human_id: str, approve: bool) -> dict[str, Any]:
        if not human_id.strip():
            raise GateError("human_id is required")
        if proposal_id not in self._proposals:
            raise GateError("unknown proposal_id")
        proposal = self._proposals[proposal_id]
        if proposal.status != "pending":
            raise GateError("proposal has already received a decision")
        if approve:
            self.state[proposal.key] = proposal.value
            status = "approved_applied"
        else:
            status = "rejected"
        self._proposals[proposal_id] = Proposal(proposal.proposal_id, proposal.actor, proposal.key, proposal.value, status)
        return self._record("human_decision", {"proposal_id": proposal_id, "human_id": human_id, "decision": "approve" if approve else "reject", "status": status, "state_changed": bool(approve)})

    def proposal(self, proposal_id: str) -> Proposal:
        try:
            return self._proposals[proposal_id]
        except KeyError as exc:
            raise GateError("unknown proposal_id") from exc

    def verify_event_chain(self) -> bool:
        previous_hash = "0" * 64
        for event in self.events:
            if event.get("previous_hash") != previous_hash:
                return False
            payload = {k: v for k, v in event.items() if k != "event_hash"}
            expected = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
            if event.get("event_hash") != expected:
                return False
            previous_hash = expected
        return True

    def _record(self, event_type: str, details: dict[str, Any]) -> dict[str, Any]:
        event = {"sequence": len(self.events) + 1, "timestamp": self._clock().astimezone(timezone.utc).isoformat(), "event_type": event_type, "details": details, "previous_hash": self._last_hash}
        event["event_hash"] = hashlib.sha256(_canonical_json(event).encode("utf-8")).hexdigest()
        self._last_hash = event["event_hash"]
        self.events.append(event)
        return dict(event)

def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
