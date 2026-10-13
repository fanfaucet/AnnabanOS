import unittest

from llm_agents.annaban_demo_agent import AnnabanDemoAgent
from api.stream_endpoints import _build_agents


class AnnabanDemoAgentTests(unittest.TestCase):
    def test_is_local_and_marks_advisory_constraints(self):
        agent = AnnabanDemoAgent()
        result = agent.send_request("Review this proposal.")
        self.assertEqual(result["provider"], "annaban-demo")
        self.assertEqual(result["developer_attribution"], "Jacob Wayne Kinnaird")
        self.assertEqual(result["mode"], "SIMULATION_ONLY")
        self.assertTrue(result["advisory_only"])
        self.assertFalse(result["external_effects"])
        self.assertIn("Human decision", result["text"])

    def test_annaban_selection_is_solo_even_if_other_keys_are_configured(self):
        agents = _build_agents(["annaban-demo"])
        self.assertEqual(list(agents), ["annaban-demo"])
        self.assertIsInstance(agents["annaban-demo"], AnnabanDemoAgent)

    def test_empty_prompt_is_handled(self):
        self.assertIn("(No task supplied.)", AnnabanDemoAgent().send_request("")["text"])


if __name__ == "__main__":
    unittest.main()
