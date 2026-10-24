import hashlib
import unittest

from annabanai_sidecar_sim import (
    AppendOnlyAuditLedger,
    HumanApproval,
    Proposal,
    evaluate_proposal,
    run_demo,
    sha256_hex,
)


def proposal(diff="print('hello')\n", proposal_id="P-1"):
    return Proposal(
        proposal_id=proposal_id,
        summary="test proposal",
        diff_sha256=hashlib.sha256(diff.encode()).hexdigest(),
    )


class SidecarSimulationTests(unittest.TestCase):
    def test_canonical_hash_is_order_independent(self):
        self.assertEqual(sha256_hex({"b": 2, "a": 1}), sha256_hex({"a": 1, "b": 2}))

    def test_missing_approval_is_pending_and_not_authorized(self):
        result = evaluate_proposal(proposal())
        self.assertEqual(result.status, "PENDING_HUMAN")
        self.assertFalse(result.authorized)
        self.assertEqual(result.external_effect, 0)

    def test_matching_human_approval_is_simulation_only(self):
        item = proposal()
        approval = HumanApproval.create("reviewer-1", item, "approve")
        result = evaluate_proposal(item, approval)
        self.assertEqual(result.status, "SIMULATION_APPROVED")
        self.assertFalse(result.authorized)
        self.assertEqual(result.mode, "SIMULATION_ONLY")

    def test_changed_diff_invalidates_approval(self):
        item = proposal()
        approval = HumanApproval.create("reviewer-1", item, "approve")
        changed = Proposal(
            proposal_id=item.proposal_id,
            summary=item.summary,
            diff_sha256=hashlib.sha256(b"changed diff").hexdigest(),
        )
        self.assertEqual(evaluate_proposal(changed, approval).status, "REJECTED_DIFF_MISMATCH")

    def test_rejected_human_decision_is_preserved(self):
        item = proposal()
        approval = HumanApproval.create("reviewer-1", item, "reject")
        self.assertEqual(evaluate_proposal(item, approval).status, "HUMAN_REJECTED")

    def test_ledger_verifies_and_detects_tampering(self):
        ledger = AppendOnlyAuditLedger()
        ledger.append({"event": "ONE"})
        ledger.append({"event": "TWO"})
        self.assertEqual(AppendOnlyAuditLedger.verify(ledger.records), (True, "chain verified"))
        altered = list(ledger.records)
        altered[0]["event"] = "ALTERED"
        ok, reason = AppendOnlyAuditLedger.verify(altered)
        self.assertFalse(ok)
        self.assertIn("record_hash mismatch", reason)

    def test_demo_stays_within_simulation_boundary(self):
        result = run_demo()
        self.assertTrue(result["ledger_verified"])
        self.assertFalse(result["authorized"])
        self.assertEqual(result["external_effect"], 0)
        self.assertEqual(result["mode"], "SIMULATION_ONLY")


if __name__ == "__main__":
    unittest.main()
