from __future__ import annotations

import base64
import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature as CryptoInvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


class TransitionError(ValueError):
    """Base error for rejected workflow transitions."""


class InvalidSignature(TransitionError):
    pass


class RoleViolation(TransitionError):
    pass


class ReplayDetected(TransitionError):
    pass


class BindingMismatch(TransitionError):
    pass


class InvalidTransition(TransitionError):
    pass


class StaleTransition(TransitionError):
    pass


class State(str, Enum):
    INGRESS = "INGRESS"
    REQUEST_ISSUED = "REQUEST_ISSUED"
    MODEL_RESPONDED = "MODEL_RESPONDED"
    VALIDATED = "VALIDATED"
    COMPARED = "COMPARED"
    RECOMMENDED = "RECOMMENDED"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    AUTHORIZED = "AUTHORIZED"
    DENIED = "DENIED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"


ROLE_FOR_STATE: dict[State, str] = {
    State.REQUEST_ISSUED: "annabanai",
    State.MODEL_RESPONDED: "model_adapter",
    State.VALIDATED: "annabanai",
    State.COMPARED: "annabanai",
    State.RECOMMENDED: "annabanai",
    State.APPROVAL_PENDING: "annabanai",
    State.AUTHORIZED: "human",
    State.DENIED: "human",
    State.REVOKED: "human",
    State.EXPIRED: "annabanai",
    State.EXECUTED: "executor",
    State.REJECTED: "annabanai",
}


ALLOWED: dict[State, set[State]] = {
    State.INGRESS: {State.REQUEST_ISSUED, State.REJECTED},
    State.REQUEST_ISSUED: {State.MODEL_RESPONDED, State.REJECTED},
    State.MODEL_RESPONDED: {State.VALIDATED, State.REJECTED},
    State.VALIDATED: {State.COMPARED, State.REJECTED},
    State.COMPARED: {State.RECOMMENDED, State.REJECTED},
    State.RECOMMENDED: {State.APPROVAL_PENDING, State.REJECTED},
    State.APPROVAL_PENDING: {State.AUTHORIZED, State.DENIED, State.EXPIRED, State.REJECTED},
    State.AUTHORIZED: {State.REVOKED, State.EXECUTED, State.EXPIRED},
    State.DENIED: set(),
    State.REVOKED: set(),
    State.EXPIRED: set(),
    State.EXECUTED: set(),
    State.REJECTED: set(),
}


@dataclass(frozen=True)
class SignedTransition:
    transition_id: str
    workflow_id: str
    from_state: str
    to_state: str
    actor_claim: str
    actor_key_id: str
    role: str
    request_hash: str | None
    output_hash: str | None
    action_key: str | None
    display_sha256: str | None
    timestamp: int
    nonce: str
    evidence: dict[str, Any]
    signature: str

    def unsigned_payload(self) -> dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "workflow_id": self.workflow_id,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "actor_claim": self.actor_claim,
            "actor_key_id": self.actor_key_id,
            "role": self.role,
            "request_hash": self.request_hash,
            "output_hash": self.output_hash,
            "action_key": self.action_key,
            "display_sha256": self.display_sha256,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "evidence": self.evidence,
        }


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


class TransitionAuthority:
    """Ed25519 key registry and verifier for security-relevant state changes."""

    def __init__(self) -> None:
        self._private: dict[str, Ed25519PrivateKey] = {}
        self._public: dict[str, Ed25519PublicKey] = {}
        self._roles: dict[str, str] = {}

    def generate(self, key_id: str, role: str) -> None:
        key = Ed25519PrivateKey.generate()
        self._private[key_id] = key
        self._public[key_id] = key.public_key()
        self._roles[key_id] = role

    def sign(
        self,
        key_id: str,
        *,
        workflow_id: str,
        from_state: State,
        to_state: State,
        actor_claim: str,
        request_hash: str | None = None,
        output_hash: str | None = None,
        action_key: str | None = None,
        display_sha256: str | None = None,
        evidence: Mapping[str, Any] | None = None,
        now: int | None = None,
        nonce: str | None = None,
    ) -> SignedTransition:
        if key_id not in self._private:
            raise InvalidSignature("unknown signing key")
        role = self._roles[key_id]
        if ROLE_FOR_STATE.get(to_state) != role:
            raise RoleViolation(f"{role} cannot authorize transition to {to_state.value}")

        transition = SignedTransition(
            transition_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            from_state=from_state.value,
            to_state=to_state.value,
            actor_claim=actor_claim,
            actor_key_id=key_id,
            role=role,
            request_hash=request_hash,
            output_hash=output_hash,
            action_key=action_key,
            display_sha256=display_sha256,
            timestamp=int(time.time() if now is None else now),
            nonce=nonce or uuid.uuid4().hex,
            evidence=dict(evidence or {}),
            signature="",
        )
        signature = self._private[key_id].sign(_canonical(transition.unsigned_payload()))
        return SignedTransition(**transition.unsigned_payload(), signature=base64.b64encode(signature).decode("ascii"))

    def verify(self, transition: SignedTransition, *, expected_workflow_id: str, now: int | None = None, max_skew: int = 300) -> None:
        if transition.workflow_id != expected_workflow_id:
            raise InvalidSignature("workflow_id mismatch")
        try:
            from_state = State(transition.from_state)
            to_state = State(transition.to_state)
        except ValueError as exc:
            raise InvalidTransition("unknown workflow state") from exc
        if to_state not in ALLOWED.get(from_state, set()):
            raise InvalidTransition(f"{from_state.value} -> {to_state.value} is not allowed")
        if self._roles.get(transition.actor_key_id) != transition.role:
            raise RoleViolation("key role does not match transition role")
        if ROLE_FOR_STATE.get(to_state) != transition.role:
            raise RoleViolation("actor role is not authorized for target state")
        current = int(time.time() if now is None else now)
        if abs(current - transition.timestamp) > max_skew:
            raise StaleTransition("transition timestamp outside allowed skew")
        if transition.actor_key_id not in self._public:
            raise InvalidSignature("unknown verification key")
        try:
            self._public[transition.actor_key_id].verify(
                base64.b64decode(transition.signature, validate=True),
                _canonical(transition.unsigned_payload()),
            )
        except (CryptoInvalidSignature, ValueError) as exc:
            raise InvalidSignature("transition signature invalid") from exc


class Workflow:
    """Workflow that cannot advance without a valid signed transition."""

    def __init__(self, authority: TransitionAuthority, workflow_id: str | None = None, *, clock=None) -> None:
        self.authority = authority
        self.workflow_id = workflow_id or str(uuid.uuid4())
        self.state = State.INGRESS
        self.clock = clock or (lambda: int(time.time()))
        self._used_transition_ids: set[str] = set()
        self._used_nonces: set[str] = set()
        self.history: list[SignedTransition] = []

    def apply(self, transition: SignedTransition) -> State:
        self.authority.verify(
            transition,
            expected_workflow_id=self.workflow_id,
            now=self.clock(),
        )
        if transition.transition_id in self._used_transition_ids or transition.nonce in self._used_nonces:
            raise ReplayDetected("transition or nonce already used")
        if transition.from_state != self.state.value:
            raise InvalidTransition("signed from_state does not match workflow state")
        self._used_transition_ids.add(transition.transition_id)
        self._used_nonces.add(transition.nonce)
        self.state = State(transition.to_state)
        self.history.append(transition)
        return self.state

    def bind_matches(self, transition: SignedTransition, bindings: Mapping[str, str | None]) -> bool:
        for field, expected in bindings.items():
            if getattr(transition, field) != expected:
                raise BindingMismatch(f"{field} does not match approved value")
        return True

    def apply_bound(
        self,
        transition: SignedTransition,
        *,
        bindings: Mapping[str, str | None],
    ) -> State:
        self.bind_matches(transition, bindings)
        return self.apply(transition)


def action_key(action_id: str, parameters: Mapping[str, Any]) -> str:
    return _sha256({"action_id": action_id, "parameters": dict(parameters)})
