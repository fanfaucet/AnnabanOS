import unittest

from annaban_policy.consent import (
    ConsentContext, ConsentOrder, ConsentState, evaluate_consent
)


def active_order(**overrides):
    values = dict(
        order_id="WO-CONSENT-001",
        state=ConsentState.ACTIVE,
        expires_at=2000,
        purpose="shared logistics",
        permitted_operations=("read",),
        permitted_resources=("shared:calendar",),
        third_party_sensitive=False,
        relationship_dependent=False,
        independent_authorization_valid=False,
    )
    values.update(overrides)
    return ConsentOrder(**values)


def context(**overrides):
    values = dict(
        now=1000,
        consent_withdrawn=False,
        identity_valid=True,
        relationship_context_changed=False,
        audit_available=True,
        requested_operation="read",
        requested_resource="shared:calendar",
    )
    values.update(overrides)
    return ConsentContext(**values)


class ConsentPolicyTests(unittest.TestCase):
    def test_valid_scoped_operation_allowed(self):
        self.assertTrue(evaluate_consent(active_order(), context()).allowed)

    def test_expired_order_denied_and_marked_expired(self):
        result = evaluate_consent(active_order(), context(now=2000))
        self.assertEqual(result.code, "DENY_EXPIRED")
        self.assertEqual(result.next_state, ConsentState.EXPIRED)

    def test_withdrawal_denied_and_marked_revoked(self):
        result = evaluate_consent(active_order(), context(consent_withdrawn=True))
        self.assertEqual(result.code, "DENY_REVOKED")
        self.assertEqual(result.next_state, ConsentState.REVOKED)

    def test_terminal_order_cannot_be_reactivated(self):
        result = evaluate_consent(
            active_order(state=ConsentState.REVOKED), context()
        )
        self.assertFalse(result.allowed)
        self.assertEqual(result.code, "DENY_TERMINAL_STATE")

    def test_relationship_context_change_suspends_dependent_order(self):
        result = evaluate_consent(
            active_order(relationship_dependent=True),
            context(relationship_context_changed=True),
        )
        self.assertEqual(result.code, "SUSPEND_CONTEXT_CHANGED")
        self.assertEqual(result.next_state, ConsentState.SUSPENDED)

    def test_sensitive_third_party_action_requires_independent_authorization(self):
        result = evaluate_consent(
            active_order(third_party_sensitive=True),
            context(),
        )
        self.assertEqual(result.code, "DENY_INDEPENDENT_AUTHORIZATION")

    def test_scope_escalation_denied(self):
        result = evaluate_consent(
            active_order(), context(requested_operation="track_location")
        )
        self.assertEqual(result.code, "DENY_OPERATION_SCOPE")

    def test_invalid_identity_suspends(self):
        result = evaluate_consent(active_order(), context(identity_valid=False))
        self.assertEqual(result.code, "DENY_IDENTITY")
        self.assertEqual(result.next_state, ConsentState.SUSPENDED)

    def test_audit_outage_denies(self):
        result = evaluate_consent(active_order(), context(audit_available=False))
        self.assertEqual(result.code, "DENY_AUDIT_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
