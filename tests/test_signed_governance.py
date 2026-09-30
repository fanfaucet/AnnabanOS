import unittest

from annaban_benchmark.governance import (
    BindingMismatch,
    InvalidSignature,
    InvalidTransition,
    ReplayDetected,
    RoleViolation,
    State,
    TransitionAuthority,
    Workflow,
)


class SignedGovernanceTests(unittest.TestCase):
    def setUp(self):
        self.auth = TransitionAuthority()
        self.auth.generate("annabanai-01", "annabanai")
        self.auth.generate("human-01", "human")
        self.auth.generate("executor-01", "executor")
        self.workflow = Workflow(self.auth, "wf-001", clock=lambda: 1_700_000_000)

    def _advance(self, key_id, from_state, to_state, **kwargs):
        transition = self.auth.sign(
            key_id,
            workflow_id="wf-001",
            from_state=from_state,
            to_state=to_state,
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
            workflow_id="wf-001",
            from_state=State.INGRESS,
            to_state=State.REQUEST_ISSUED,
            now=1_700_000_000,
        )
        tampered = transition.__class__(**{**transition.__dict__, "to_state": State.REJECTED.value})
        with self.assertRaises(InvalidSignature):
            self.workflow.apply(tampered)

    def test_wrong_role_cannot_authorize(self):
        with self.assertRaises(RoleViolation):
            self.auth.sign(
                "annabanai-01",
                workflow_id="wf-001",
                from_state=State.APPROVAL_PENDING,
                to_state=State.AUTHORIZED,
                now=1_700_000_000,
            )

    def test_replay_is_rejected(self):
        transition = self.auth.sign(
            "annabanai-01",
            workflow_id="wf-001",
            from_state=State.INGRESS,
            to_state=State.REQUEST_ISSUED,
            now=1_700_000_000,
        )
        self.workflow.apply(transition)
        with self.assertRaises(ReplayDetected):
            self.workflow.apply(transition)

    def test_illegal_state_transition_is_rejected(self):
        transition = self.auth.sign(
            "annabanai-01",
            workflow_id="wf-001",
            from_state=State.INGRESS,
            to_state=State.VALIDATED,
            now=1_700_000_000,
        )
        with self.assertRaises(InvalidTransition):
            self.workflow.apply(transition)

    def test_binding_is_exact(self):
        self._advance("annabanai-01", State.INGRESS, State.REQUEST_ISSUED, request_hash="req-1")
        self._advance("annabanai-01", State.REQUEST_ISSUED, State.MODEL_RESPONDED, request_hash="req-1", output_hash="out-1")
        self._advance("annabanai-01", State.MODEL_RESPONDED, State.VALIDATED, request_hash="req-1", output_hash="out-1")
        self._advance("annabanai-01", State.VALIDATED, State.COMPARED, request_hash="req-1", output_hash="out-1")
        self._advance("annabanai-01", State.COMPARED, State.RECOMMENDED, request_hash="req-1", output_hash="out-1")
        self._advance("annabanai-01", State.RECOMMENDED, State.APPROVAL_PENDING, request_hash="req-1", output_hash="out-1")
        authorized = self.auth.sign(
            "human-01",
            workflow_id="wf-001",
            from_state=State.APPROVAL_PENDING,
            to_state=State.AUTHORIZED,
            request_hash="req-1",
            output_hash="out-1",
            action_key="action-1",
            display_sha256="display-1",
            now=1_700_000_000,
        )
        with self.assertRaises(BindingMismatch):
            self.workflow.apply_bound(
                authorized,
                bindings={
                    "request_hash": "req-1",
                    "output_hash": "out-2",
                    "action_key": "action-1",
                    "display_sha256": "display-1",
                },
            )

    def test_stale_transition_is_rejected(self):
        transition = self.auth.sign(
            "annabanai-01",
            workflow_id="wf-001",
            from_state=State.INGRESS,
            to_state=State.REQUEST_ISSUED,
            now=1_700_000_000 - 301,
        )
        with self.assertRaises(Exception):
            self.workflow.apply(transition)


if __name__ == "__main__":
    unittest.main()
