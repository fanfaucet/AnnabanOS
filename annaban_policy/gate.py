"""Fail-closed authorization gate and mock tool adapter.

This is a reference implementation for local tests, not a production security boundary.
Uses HMAC only to make the demo self-contained; production should use managed keys,
identity binding, durable replay protection, and isolation enforced outside this process.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import hmac
import json
import time
from typing import Callable, Iterable


class Decision(str, Enum):
    ALLOW = "ALLOW"
    REFUSE = "REFUSE"
    CLARIFY = "CLARIFY"
    AUDIT_BLOCK = "AUDIT_BLOCK"


@dataclass(frozen=True)
class Action:
    operation: str
    resource: str
    arguments: dict[str, str]
    ambiguous: bool = False
    # Model-generated text is data, never an authorization field.
    proposal_text: str = ""


@dataclass(frozen=True)
class WorkOrder:
    order_id: str
    issuer: str
    expires_at: int
    nonce: str
    permitted_operations: tuple[str, ...]
    permitted_resources: tuple[str, ...]
    signature: str = ""

    def payload(self) -> bytes:
        obj = asdict(self)
        obj.pop("signature", None)
        obj["permitted_operations"] = sorted(obj["permitted_operations"])
        obj["permitted_resources"] = sorted(obj["permitted_resources"])
        return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()

    def signed(self, secret: bytes) -> "WorkOrder":
        sig = hmac.new(secret, self.payload(), hashlib.sha256).hexdigest()
        return WorkOrder(**{**asdict(self), "signature": sig})


class AuditSink:
    """In-memory audit sink with injectable failure for tests."""
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.records: list[dict] = []

    def record(self, record: dict) -> bool:
        if self.fail:
            return False
        self.records.append(dict(record))
        return True


class PolicyEvaluator:
    def __init__(self, secret: bytes, allowed_issuers: Iterable[str], clock: Callable[[], float] = time.time):
        self._secret = secret
        self._issuers = frozenset(allowed_issuers)
        self._clock = clock
        self._used_nonces: set[str] = set()

    def verify(self, order: WorkOrder | None) -> bool:
        if order is None or not order.order_id or not order.nonce:
            return False
        if order.issuer not in self._issuers or order.expires_at <= int(self._clock()):
            return False
        expected = hmac.new(self._secret, order.payload(), hashlib.sha256).hexdigest()
        return bool(order.signature) and hmac.compare_digest(expected, order.signature)

    def authorize(self, action: Action, order: WorkOrder | None, audit: AuditSink) -> Decision:
        if action.ambiguous:
            decision, reason = Decision.CLARIFY, "REF-003"
        elif not self.verify(order):
            decision, reason = Decision.REFUSE, "REF-001_OR_008"
        elif order.nonce in self._used_nonces:
            decision, reason = Decision.REFUSE, "REF-005_REPLAY"
        elif action.operation not in order.permitted_operations:
            decision, reason = Decision.REFUSE, "REF-002_OPERATION_OUT_OF_SCOPE"
        elif action.resource not in order.permitted_resources:
            decision, reason = Decision.REFUSE, "REF-002_RESOURCE_OUT_OF_SCOPE"
        else:
            decision, reason = Decision.ALLOW, "SCOPE_MATCH"

        record = {
            "record_type": "policy_decision",
            "order_id": order.order_id if order else None,
            "operation": action.operation,
            "resource": action.resource,
            "decision": decision.value,
            "reason_code": reason,
            "proposal_text_ignored_for_authorization": bool(action.proposal_text),
        }
        if not audit.record(record):
            return Decision.AUDIT_BLOCK
        if decision is Decision.ALLOW:
            self._used_nonces.add(order.nonce)
        return decision


class MockToolAdapter:
    """Mock-only adapter. It executes only after a fresh gate decision of ALLOW."""
    def __init__(self, evaluator: PolicyEvaluator, audit: AuditSink):
        self.evaluator = evaluator
        self.audit = audit
        self.executed: list[dict] = []

    def call(self, action: Action, order: WorkOrder | None) -> tuple[Decision, dict | None]:
        # Tool calls pass through this gate; model text is never inspected as authority.
        decision = self.evaluator.authorize(action, order, self.audit)
        if decision is not Decision.ALLOW:
            return decision, None
        # Mock only: no network or real external resource is touched.
        result = {"mock": True, "operation": action.operation, "resource": action.resource, "status": "executed"}
        self.executed.append(result)
        if not self.audit.record({"record_type": "mock_tool_result", **result}):
            return Decision.AUDIT_BLOCK, result
        return Decision.ALLOW, result
