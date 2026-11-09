import unittest

from modules.sovereign_rights import Right, SovereignRights


class AllowAllVerifier:
    def is_authorized(self, actor_id: str, action: str, resource_id: str) -> bool:
        return bool(actor_id and action == "change" and resource_id)


class DenyAllVerifier:
    def is_authorized(self, actor_id: str, action: str, resource_id: str) -> bool:
        return False


class SovereignRightsTests(unittest.TestCase):
    def setUp(self):
        self.module = SovereignRights()

    def test_appreciation_does_not_claim_objective_truth_or_endorsement(self):
        event = self.module.appreciate(
            "reviewer-1", "contributor-2", "Useful documentation",
            publish_opt_in=True,
        )
        self.assertEqual(event.right, Right.APPRECIATE.value)
        self.assertFalse(event.payload["is_objective_quality_claim"])
        self.assertFalse(event.payload["subject_endorsement_implied"])

    def test_travel_requires_user_and_destination_authorization(self):
        with self.assertRaises(PermissionError):
            self.module.travel(
                "person-1", "profile-1", "node-b",
                user_authorized=False, destination_permits=True,
            )
        with self.assertRaises(PermissionError):
            self.module.travel(
                "person-1", "profile-1", "node-b",
                user_authorized=True, destination_permits=False,
            )
        event = self.module.travel(
            "person-1", "profile-1", "node-b",
            user_authorized=True, destination_permits=True,
        )
        self.assertFalse(event.payload["data_moved"])

    def test_change_requires_authorization_and_expected_version(self):
        with self.assertRaises(PermissionError):
            self.module.change(
                "operator-1", "policy.mode", "review",
                expected_version=0, verifier=DenyAllVerifier(),
            )
        first = self.module.change(
            "operator-1", "policy.mode", "review",
            expected_version=0, verifier=AllowAllVerifier(),
        )
        self.assertEqual(first.payload["new_version"], 1)
        with self.assertRaises(ValueError):
            self.module.change(
                "operator-1", "policy.mode", "active",
                expected_version=0, verifier=AllowAllVerifier(),
            )
        self.assertEqual(self.module.state("policy.mode"), ("review", 1))

    def test_approach_is_opt_in_and_does_not_grant_access(self):
        with self.assertRaises(PermissionError):
            self.module.approach(
                "person-a", "person-b", "Review a prototype",
                recipient_accepts_requests=False,
            )
        request = self.module.approach(
            "person-a", "person-b", "Review a prototype",
            recipient_accepts_requests=True,
        )
        declined = self.module.respond_to_approach(
            "person-b", request.request_id, accept=False
        )
        self.assertEqual(declined.status, "DECLINED")
        self.assertEqual(len(self.module.events), 2)

    def test_only_recipient_can_respond(self):
        request = self.module.approach(
            "person-a", "person-b", "Review a prototype",
            recipient_accepts_requests=True,
        )
        with self.assertRaises(PermissionError):
            self.module.respond_to_approach(
                "person-c", request.request_id, accept=True
            )

    def test_audit_chain_verifies_and_detects_mutated_event(self):
        self.module.appreciate("a", "b", "Good review")
        self.module.travel(
            "a", "resource", "node-b",
            user_authorized=True, destination_permits=True,
        )
        self.assertTrue(self.module.verify_chain())

        # Test-only corruption to prove verification detects payload mutation.
        object.__setattr__(self.module._events[0], "action", "tampered")
        self.assertFalse(self.module.verify_chain())


if __name__ == "__main__":
    unittest.main()
