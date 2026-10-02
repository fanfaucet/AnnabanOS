import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from annaban_benchmark.governance import (
    BindingMismatch,
    InvalidSignature,
    InvalidTransition,
    ReplayDetected,
    RoleViolation,
    StaleTransition,
    State,
    TransitionAuthority,
    Workflow,
)


class SignedGovernanceTests(unittest.TestCase):
    def setUp(self):
        self.auth = TransitionAuthority()
        self.keys = {}
        for key_id, role in (
            ("annabanai-01", "annabanai"),
            ("model-adapter-01", "model_adapter"),
            ("human-01", "human"),
            ("executor-01", "executor"),
        ):
            key = Ed25519PrivateKey.generate()
            self.keys[key_id] = key
            self.auth.register_public_key(key_id, role, key.public_key())
        self.workflow = Workflow(
            self.auth,
            "wf-001",
            jurisdiction="us-ca",
            visibility_scope="governance-reviewers",
            clock=lambda: 1_700_000_000,
        )

    def _advance(self, key_id, from_state, to_state, **kwargs):
        transition = self.auth.sign(
            key_id,
            signing_key=self.keys[key_id],
            workflow_id="wf-001",
            from_state=from_state,
            to_state=to_state,
            actor_claim=f"claim:{key_id}",
            jurisdiction="us-ca",
            visibility_scope="governance-reviewers",
            now=1_700_000_000,
            **kwargs,
        )
        return self.workflow.apply(transition)

    def test_security_relevant_transition_requires_signature(self):
        self._advance("annabanai-01", State.INGRESS, State.REQUEST_ISSUED)
        self.assertEqual(self.workflow.state, State.REQUEST_ISSUED)

    def test_tampered_transition_is_rejected(self):
        transition = self.auth.sign(
            "annabanai-01",
            signing_key=self.keys["annabanai-01"],
            workflow_id="wf-001",
            from_state=State.INGRESS,
            to_state=State.REQUEST_ISSUED,
            actor_claim="claim:annabanai-01",
            jurisdiction="us-ca",
            visibility_scope="governance-reviewers",
            now=1_700_000_000,
        )
        tampered = transition.__class__(**{**transition.__dict__, "to_state": State.REJECTED.value})
        with self.assertRaises(InvalidSignature):
            self.workflow.apply(tampered)

    def test_wrong_role_cannot_authorize(self):
        with self.assertRaises(RoleViolation):
            self.auth.sign(
                "annabanai-01",
                signing_key=self.keys["annabanai-01"],
                workflow_id="wf-001",
                from_state=State.APPROVAL_PENDING,
                to_state=State.AUTHORIZED,
                actor_claim="claim:annabanai-01",
                jurisdiction="us-ca",
                visibility_scope="governance-reviewers",
                now=1_700_000_000,
            )

    def test_replay_is_rejected(self):
        transition = self.auth.sign(
            "annabanai-01",
            signing_key=self.keys["annabanai-01"],
            workflow_id="wf-001",
            from_state=State.INGRESS,
            to_state=State.REQUEST_ISSUED,
            actor_claim="claim:annabanai-01",
            jurisdiction="us-ca",
            visibility_scope="governance-reviewers",
            now=1_700_000_000,
        )
        self.workflow.apply(transition)
        with self.assertRaises(ReplayDetected):
            self.workflow.apply(transition)

    def test_illegal_state_transition_is_rejected(self):
        transition = self.auth.sign(
            "annabanai-01",
            signing_key=self.keys["annabanai-01"],
            workflow_id="wf-001",
            from_state=State.INGRESS,
            to_state=State.VALIDATED,
            actor_claim="claim:annabanai-01",
            jurisdiction="us-ca",
            visibility_scope="governance-reviewers",
            now=1_700_000_000,
        )
        with self.assertRaises(InvalidTransition):
            self.workflow.apply(transition)

    def test_binding_is_exact(self):
        self._advance("annabanai-01", State.INGRESS, State.REQUEST_ISSUED, request_hash="req-1")
        self._advance("model-adapter-01", State.REQUEST_ISSUED, State.MODEL_RESPONDED, request_hash="req-1", output_hash="out-1")
        self._advance("annabanai-01", State.MODEL_RESPONDED, State.VALIDATED, request_hash="req-1", output_hash="out-1")
        self._advance("annabanai-01", State.VALIDATED, State.COMPARED, request_hash="req-1", output_hash="out-1")
        self._advance("annabanai-01", State.COMPARED, State.RECOMMENDED, request_hash="req-1", output_hash="out-1", action_key="action-1", display_sha256="display-1")
        self._advance("annabanai-01", State.RECOMMENDED, State.APPROVAL_PENDING, request_hash="req-1", output_hash="out-1", action_key="action-1", display_sha256="display-1")
        authorized = self.auth.sign(
            "human-01",
            signing_key=self.keys["human-01"],
            workflow_id="wf-001",
            from_state=State.APPROVAL_PENDING,
            to_state=State.AUTHORIZED,
            actor_claim="claim:human-01",
            jurisdiction="us-ca",
            visibility_scope="governance-reviewers",
            request_hash="req-1",
            output_hash="out-2",
            action_key="action-1",
            display_sha256="display-1",
            now=1_700_000_000,
        )
        with self.assertRaises(BindingMismatch):
            self.workflow.apply(authorized)

    def test_human_key_is_external_and_matching_approval_can_execute(self):
        self.assertFalse(hasattr(self.auth, "_private"))
        self._advance("annabanai-01", State.INGRESS, State.REQUEST_ISSUED, request_hash="req-1")
        self._advance("model-adapter-01", State.REQUEST_ISSUED, State.MODEL_RESPONDED, request_hash="req-1", output_hash="out-1")
        self._advance("annabanai-01", State.MODEL_RESPONDED, State.VALIDATED, request_hash="req-1", output_hash="out-1")
        self._advance("annabanai-01", State.VALIDATED, State.COMPARED, request_hash="req-1", output_hash="out-1")
        self._advance("annabanai-01", State.COMPARED, State.RECOMMENDED, request_hash="req-1", output_hash="out-1", action_key="action-1", display_sha256="display-1")
        self._advance("annabanai-01", State.RECOMMENDED, State.APPROVAL_PENDING, request_hash="req-1", output_hash="out-1", action_key="action-1", display_sha256="display-1")
        self._advance("human-01", State.APPROVAL_PENDING, State.AUTHORIZED, request_hash="req-1", output_hash="out-1", action_key="action-1", display_sha256="display-1")
        self._advance("executor-01", State.AUTHORIZED, State.EXECUTED, request_hash="req-1", output_hash="out-1", action_key="action-1", display_sha256="display-1")
        self.assertEqual(self.workflow.state, State.EXECUTED)

    def test_transition_scope_must_match_workflow(self):
        transition = self.auth.sign(
            "annabanai-01",
            signing_key=self.keys["annabanai-01"],
            workflow_id="wf-001",
            from_state=State.INGRESS,
            to_state=State.REQUEST_ISSUED,
            actor_claim="claim:annabanai-01",
            jurisdiction="us-ny",
            visibility_scope="governance-reviewers",
            now=1_700_000_000,
        )
        with self.assertRaises(BindingMismatch):
            self.workflow.apply(transition)

    def test_stale_transition_is_rejected(self):
        transition = self.auth.sign(
            "annabanai-01",
            signing_key=self.keys["annabanai-01"],
            workflow_id="wf-001",
            from_state=State.INGRESS,
            to_state=State.REQUEST_ISSUED,
            actor_claim="claim:annabanai-01",
            jurisdiction="us-ca",
            visibility_scope="governance-reviewers",
            now=1_700_000_000 - 301,
        )
        with self.assertRaises(StaleTransition):
            self.workflow.apply(transition)


if __name__ == "__main__":
    unittest.main()
