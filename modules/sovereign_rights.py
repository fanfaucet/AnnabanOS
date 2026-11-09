"""AnnabanOS Sovereign Rights module.

Conceptual, local reference implementation. No networking, sensor access,
message delivery, or autonomous outreach is performed by this module.
Project direction attributed to Jacob Wayne Kinnaird; implementation
contributions should be attributed separately in the repository history.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Protocol


class Right(str, Enum):
    APPRECIATE = "right_to_appreciate"
    TRAVEL = "right_to_travel"
    CHANGE = "right_to_change"
    APPROACH = "right_to_approach"


class AuthorizationVerifier(Protocol):
    """Trusted adapter implemented by the host application's auth layer."""

    def is_authorized(
        self, actor_id: str, action: str, resource_id: str
    ) -> bool:
        """Return true only after verifying the actor's credentials and scope."""
        ...


@dataclass(frozen=True)
class AuditEvent:
    sequence: int
    event_id: str
    timestamp: float
    actor_id: str
    right: str
    action: str
    payload: dict[str, Any]
    previous_hash: str
    event_hash: str


@dataclass(frozen=True)
class ApproachRequest:
    request_id: str
    requester_id: str
    recipient_id: str
    purpose: str
    status: str = "REQUESTED"
    simulation: bool = True


class SovereignRights:
    """Enforce the four rights as bounded, auditable operations."""

    GENESIS = "GENESIS"

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._state: dict[str, Any] = {}
        self._versions: dict[str, int] = {}
        self._approaches: dict[str, ApproachRequest] = {}

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        """Return an immutable snapshot of the current event sequence."""
        return tuple(self._events)

    def state(self, key: str) -> tuple[Any, int]:
        """Return the current value and version, or (None, 0) if unset."""
        return self._state.get(key), self._versions.get(key, 0)

    def _append(
        self, actor_id: str, right: Right, action: str, payload: dict[str, Any]
    ) -> AuditEvent:
        if not actor_id.strip():
            raise ValueError("actor_id is required")
        previous = self._events[-1].event_hash if self._events else self.GENESIS
        body = {
            "sequence": len(self._events) + 1,
            "event_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "actor_id": actor_id,
            "right": right.value,
            "action": action,
            "payload": payload,
            "previous_hash": previous,
        }
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        event = AuditEvent(**body, event_hash=digest)
        self._events.append(event)
        return event

    def appreciate(
        self,
        actor_id: str,
        subject_id: str,
        statement: str,
        *,
        publish_opt_in: bool = False,
    ) -> AuditEvent:
        """Record appreciation; publication requires an explicit author opt-in.

        This records a subjective expression, not an objective quality score,
        factual certification, or endorsement by the subject.
        """
        if not subject_id.strip() or not statement.strip():
            raise ValueError("subject_id and statement are required")
        return self._append(
            actor_id,
            Right.APPRECIATE,
            "appreciation_recorded",
            {
                "subject_id": subject_id,
                "statement": statement,
                "publish_opt_in": publish_opt_in,
                "is_objective_quality_claim": False,
                "subject_endorsement_implied": False,
            },
        )

    def travel(
        self,
        actor_id: str,
        resource_id: str,
        destination: str,
        *,
        user_authorized: bool,
        destination_permits: bool,
    ) -> AuditEvent:
        """Record a portability decision; does not move data or override policy."""
        if not resource_id.strip() or not destination.strip():
            raise ValueError("resource_id and destination are required")
        if not user_authorized:
            raise PermissionError("Explicit user authorization is required")
        if not destination_permits:
            raise PermissionError("Destination policy does not permit portability")
        return self._append(
            actor_id,
            Right.TRAVEL,
            "portability_authorized",
            {
                "resource_id": resource_id,
                "destination": destination,
                "user_authorized": True,
                "destination_permits": True,
                "data_moved": False,
            },
        )

    def change(
        self,
        actor_id: str,
        key: str,
        new_value: Any,
        *,
        expected_version: int,
        verifier: AuthorizationVerifier,
    ) -> AuditEvent:
        """Apply an authorized versioned change while preserving prior events."""
        if not key.strip():
            raise ValueError("state key is required")
        current_version = self._versions.get(key, 0)
        if expected_version != current_version:
            raise ValueError(
                f"stale version: expected {current_version}, got {expected_version}"
            )
        if not verifier.is_authorized(actor_id, "change", key):
            raise PermissionError("Authenticated change authorization rejected")

        old_value = self._state.get(key)
        next_version = current_version + 1
        event = self._append(
            actor_id,
            Right.CHANGE,
            "state_changed",
            {
                "key": key,
                "old_value": old_value,
                "new_value": new_value,
                "previous_version": current_version,
                "new_version": next_version,
            },
        )
        self._state[key] = new_value
        self._versions[key] = next_version
        return event

    def approach(
        self,
        requester_id: str,
        recipient_id: str,
        purpose: str,
        *,
        recipient_accepts_requests: bool,
    ) -> ApproachRequest:
        """Create a local request record; never sends a message or grants access."""
        if not requester_id.strip() or not recipient_id.strip():
            raise ValueError("requester_id and recipient_id are required")
        if requester_id == recipient_id:
            raise ValueError("requester and recipient must differ")
        if not purpose.strip():
            raise ValueError("purpose is required")
        if not recipient_accepts_requests:
            raise PermissionError("Recipient has not opted in to receiving requests")

        request = ApproachRequest(
            request_id=str(uuid.uuid4()),
            requester_id=requester_id,
            recipient_id=recipient_id,
            purpose=purpose,
        )
        self._approaches[request.request_id] = request
        self._append(
            requester_id,
            Right.APPROACH,
            "approach_request_created",
            asdict(request),
        )
        return request

    def respond_to_approach(
        self, recipient_id: str, request_id: str, *, accept: bool
    ) -> ApproachRequest:
        """Record the recipient's choice; acceptance is not authorization to access."""
        request = self._approaches.get(request_id)
        if request is None:
            raise KeyError("unknown approach request")
        if recipient_id != request.recipient_id:
            raise PermissionError("Only the addressed recipient may respond")
        if request.status != "REQUESTED":
            raise ValueError("approach request already has a response")

        updated = ApproachRequest(
            request_id=request.request_id,
            requester_id=request.requester_id,
            recipient_id=request.recipient_id,
            purpose=request.purpose,
            status="ACCEPTED" if accept else "DECLINED",
            simulation=request.simulation,
        )
        self._approaches[request_id] = updated
        self._append(
            recipient_id,
            Right.APPROACH,
            "approach_response_recorded",
            asdict(updated),
        )
        return updated

    def verify_chain(self) -> bool:
        """Verify internal consistency; not proof against full-store rewriting."""
        previous = self.GENESIS
        for expected_sequence, event in enumerate(self._events, start=1):
            if event.sequence != expected_sequence or event.previous_hash != previous:
                return False
            body = asdict(event)
            stored_hash = body.pop("event_hash")
            canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
            computed = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            if computed != stored_hash:
                return False
            previous = stored_hash
        return True
