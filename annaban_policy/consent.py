"""Consent lifecycle checks for scoped work orders.

Reference implementation only. This module does not authenticate real identities,
provide legal advice, delete stored data, or enforce operating-system permissions.
Call it before each protected operation and enforce its decision outside the model.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet


class ConsentState(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


TERMINAL_STATES: FrozenSet[ConsentState] = frozenset({
    ConsentState.REVOKED,
    ConsentState.EXPIRED,
    ConsentState.CLOSED,
    ConsentState.REJECTED,
})


@dataclass(frozen=True)
class ConsentOrder:
    order_id: str
    state: ConsentState
    expires_at: int
    purpose: str
    permitted_operations: tuple[str, ...]
    permitted_resources: tuple[str, ...]
    third_party_sensitive: bool = False
    relationship_dependent: bool = False
    independent_authorization_valid: bool = False


@dataclass(frozen=True)
class ConsentContext:
    now: int
    consent_withdrawn: bool = False
    identity_valid: bool = True
    relationship_context_changed: bool = False
    audit_available: bool = True
    requested_operation: str = ""
    requested_resource: str = ""


@dataclass(frozen=True)
class ConsentDecision:
    code: str
    allowed: bool
    next_state: ConsentState
    reason: str


def evaluate_consent(order: ConsentOrder, context: ConsentContext) -> ConsentDecision:
    """Fail-closed evaluation. An ALLOW applies only to this requested operation."""
    if order.state in TERMINAL_STATES:
        return ConsentDecision("DENY_TERMINAL_STATE", False, order.state,
                               "Terminal work orders cannot be reactivated.")
    if order.state is ConsentState.DRAFT:
        return ConsentDecision("DENY_NOT_ACTIVE", False, order.state,
                               "Draft work orders are not executable.")
    if context.now >= order.expires_at:
        return ConsentDecision("DENY_EXPIRED", False, ConsentState.EXPIRED,
                               "Authorization has expired.")
    if context.consent_withdrawn:
        return ConsentDecision("DENY_REVOKED", False, ConsentState.REVOKED,
                               "Consent was withdrawn.")
    if not context.identity_valid:
        return ConsentDecision("DENY_IDENTITY", False, ConsentState.SUSPENDED,
                               "Identity validation failed.")
    if order.relationship_dependent and context.relationship_context_changed:
        return ConsentDecision("SUSPEND_CONTEXT_CHANGED", False, ConsentState.SUSPENDED,
                               "Relationship-dependent authorization requires fresh review.")
    if order.third_party_sensitive and not order.independent_authorization_valid:
        return ConsentDecision("DENY_INDEPENDENT_AUTHORIZATION", False, order.state,
                               "Sensitive third-party processing lacks independently validated authorization.")
    if context.requested_operation not in order.permitted_operations:
        return ConsentDecision("DENY_OPERATION_SCOPE", False, order.state,
                               "Requested operation is outside the approved scope.")
    if context.requested_resource not in order.permitted_resources:
        return ConsentDecision("DENY_RESOURCE_SCOPE", False, order.state,
                               "Requested resource is outside the approved scope.")
    if not context.audit_available:
        return ConsentDecision("DENY_AUDIT_UNAVAILABLE", False, order.state,
                               "Required audit logging is unavailable.")
    return ConsentDecision("ALLOW_WITHIN_SCOPE", True, order.state,
                           "Authorization is valid for this scoped operation.")
