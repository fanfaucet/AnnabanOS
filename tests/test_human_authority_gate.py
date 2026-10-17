import unittest
from datetime import datetime, timezone
from mvd.human_authority_gate import GateError, HumanAuthorityGate

class HumanAuthorityGateTests(unittest.TestCase):
    def setUp(self):
        self.gate = HumanAuthorityGate(allowed_keys={"mode", "limit"}, initial_state={"mode": "safe", "limit": 1}, clock=lambda: datetime(2026, 10, 12, tzinfo=timezone.utc))

    def test_pending_proposal_does_not_change_state(self):
        self.gate.propose(proposal_id="p-1", actor="agent-a", key="mode", value="active")
        self.assertEqual(self.gate.state["mode"], "safe")
        self.assertEqual(self.gate.proposal("p-1").status, "pending")

    def test_approval_applies_allowlisted_update(self):
        self.gate.propose(proposal_id="p-1", actor="agent-a", key="mode", value="active")
        event = self.gate.decide(proposal_id="p-1", human_id="operator-1", approve=True)
        self.assertEqual(self.gate.state["mode"], "active")
        self.assertEqual(event["details"]["status"], "approved_applied")

    def test_rejection_does_not_change_state(self):
        self.gate.propose(proposal_id="p-1", actor="agent-a", key="mode", value="active")
        event = self.gate.decide(proposal_id="p-1", human_id="operator-1", approve=False)
        self.assertEqual(self.gate.state["mode"], "safe")
        self.assertEqual(event["details"]["status"], "rejected")

    def test_unapproved_key_is_denied(self):
        with self.assertRaises(GateError):
            self.gate.propose(proposal_id="p-1", actor="agent-a", key="admin", value=True)

    def test_missing_human_identity_is_denied(self):
        self.gate.propose(proposal_id="p-1", actor="agent-a", key="mode", value="active")
        with self.assertRaises(GateError):
            self.gate.decide(proposal_id="p-1", human_id=" ", approve=True)
        self.assertEqual(self.gate.state["mode"], "safe")

    def test_duplicate_decision_is_denied(self):
        self.gate.propose(proposal_id="p-1", actor="agent-a", key="mode", value="active")
        self.gate.decide(proposal_id="p-1", human_id="operator-1", approve=False)
        with self.assertRaises(GateError):
            self.gate.decide(proposal_id="p-1", human_id="operator-1", approve=True)

    def test_event_chain_detects_tampering(self):
        self.gate.propose(proposal_id="p-1", actor="agent-a", key="mode", value="active")
        self.gate.decide(proposal_id="p-1", human_id="operator-1", approve=True)
        self.assertTrue(self.gate.verify_event_chain())
        self.gate.events[0]["details"]["actor"] = "tampered"
        self.assertFalse(self.gate.verify_event_chain())

if __name__ == "__main__":
    unittest.main()
