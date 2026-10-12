"""Unit tests for power_retrieval.py. Run: python -m unittest discover -s examples/kardashev_ii -v"""
import unittest

from power_retrieval import (
    GovernanceState,
    Scenario,
    calculate_power,
    governance_gate,
    hypothetical_review_lenses,
)


class PowerRetrievalTests(unittest.TestCase):
    def test_reference_scenario(self):
        result = calculate_power(
            Scenario("mature", 0.10, 0.80, 0.95)
        )
        self.assertAlmostEqual(result.delivered_power_w, 2.911e25, delta=1e20)
        self.assertEqual(result.governance_state, GovernanceState.SIMULATION_ONLY)
        self.assertFalse(result.external_effects_enabled)

    def test_full_capture_reference(self):
        result = calculate_power(Scenario("full", 1.0, 0.90, 1.0))
        self.assertAlmostEqual(result.delivered_power_w, 3.447e26, delta=1e21)

    def test_invalid_fraction_rejected(self):
        with self.assertRaises(ValueError):
            calculate_power(Scenario("invalid", 1.01, 0.8, 0.95))

    def test_non_finite_input_rejected(self):
        with self.assertRaises(ValueError):
            calculate_power(Scenario("nan", float("nan"), 0.8, 0.95))

    def test_negative_stellar_output_rejected(self):
        with self.assertRaises(ValueError):
            calculate_power(Scenario("negative", 0.1, 0.8, 0.95), -1.0)

    def test_power_estimate_does_not_authorize_action(self):
        self.assertEqual(
            governance_gate(
                evidence_validated=True,
                human_authorized=True,
                simulation_mode=True,
            ),
            GovernanceState.SIMULATION_ONLY,
        )

    def test_missing_evidence_fails_closed(self):
        self.assertEqual(
            governance_gate(
                evidence_validated=False,
                human_authorized=True,
                simulation_mode=False,
            ),
            GovernanceState.BLOCKED,
        )

    def test_missing_human_authorization_requires_review(self):
        self.assertEqual(
            governance_gate(
                evidence_validated=True,
                human_authorized=False,
                simulation_mode=False,
            ),
            GovernanceState.REVIEW_REQUIRED,
        )

    def test_public_figure_lens_is_explicitly_hypothetical(self):
        budget = calculate_power(Scenario("mature", 0.1, 0.8, 0.95))
        lens = hypothetical_review_lenses(budget)
        self.assertFalse(lens["actual_participation_or_endorsement"])
        self.assertFalse(lens["economics"]["valuation_assigned"])


if __name__ == "__main__":
    unittest.main()
