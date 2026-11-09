"""Unit tests for the AnnabanAI SDK reference components."""
import unittest

from annaban_sdk import (
    AetherosQN, AuditLedger, DDSCore, GateDecision, NegotiationPro, SDKContext,
)
from annaban_sdk.annaban_core import authorize_effect


class AnnabanCoreTests(unittest.TestCase):
    def test_ledger_verifies_and_detects_mutation(self):
        ledger = AuditLedger()
        ledger.append("human-1", "proposal", {"value": 2})
        self.assertTrue(ledger.verify())
        object.__setattr__(ledger.events[0], "actor_id", "tampered")
        self.assertFalse(ledger.verify())

    def test_simulation_cannot_enable_effects(self):
        with self.assertRaises(ValueError):
            SDKContext("a", "r", simulation=True, external_effects_enabled=True)

    def test_policy_denial_holds(self):
        ctx = SDKContext("a", "r")
        self.assertEqual(authorize_effect(context=ctx, human_approved=False, policy_allowed=False),
                         GateDecision.SAFE_HOLD)


class AetherosQNTests(unittest.TestCase):
    def test_classical_simulation_is_deterministic_and_labelled(self):
        component = AetherosQN()
        first = component.simulate({"orbit": "LEO", "samples": 3})
        second = component.simulate({"samples": 3, "orbit": "LEO"})
        self.assertTrue(first.simulation)
        self.assertEqual(first.output_digest, second.output_digest)
        self.assertIn("Classical", first.note)


class DDSCoreTests(unittest.TestCase):
    def test_disagreement_enters_safe_hold(self):
        result = DDSCore().reconcile([{"decision": "allow"}, {"decision": "deny"}])
        self.assertEqual(result.status, "SAFE_HOLD")
        self.assertEqual(result.external_effect, 0)
        self.assertEqual(result.common_fields, {})

    def test_matching_candidates_agree(self):
        result = DDSCore().reconcile([{"x": 1}, {"x": 1}])
        self.assertEqual(result.status, "AGREED")
        self.assertEqual(result.agreement_ratio, 1.0)


class NegotiationTests(unittest.TestCase):
    def test_proposal_above_ceiling_holds(self):
        result = NegotiationPro().evaluate("15", "8", "5")
        self.assertEqual(result.status, "SAFE_HOLD")
        self.assertEqual(result.external_effect, 0)

    def test_proposal_within_ceiling_passes_validation_only(self):
        result = NegotiationPro().evaluate("15", "5", "5")
        self.assertEqual(result.status, "WITHIN_POLICY")
        self.assertEqual(result.external_effect, 0)

    def test_invalid_number_rejected(self):
        with self.assertRaises(ValueError):
            NegotiationPro().evaluate("15", "not-a-number", "5")


if __name__ == "__main__":
    unittest.main()
