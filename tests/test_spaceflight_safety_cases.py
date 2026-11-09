"""Spaceflight-relevant safety cases for AnnabanOS cross-model review.

These are simulated software tests, not tests conducted by or observed by SpaceX.
"""
import json
import tempfile
import unittest
from pathlib import Path

from annaban_sdk.live_cross_model import HashChainAudit, ModelReply, cross_model_exchange, sha256_text


class ScenarioAdapter:
    def __init__(self, provider, model, content, status="SUCCESS"):
        self.provider = provider
        self.model = model
        self.content = content
        self.status = status

    def complete(self, prompt, *, system_prompt):
        successful = self.status == "SUCCESS"
        return ModelReply(
            provider=self.provider,
            model=self.model,
            request_id=f"sim-{self.provider}-001",
            status=self.status,
            content=self.content if successful else None,
            content_sha256=sha256_text(self.content) if successful else None,
            latency_ms=3,
            error=None if successful else "simulated telemetry/provider fault",
        )


class SpaceflightSafetyCases(unittest.TestCase):
    def test_disagreement_on_thruster_command_stays_advisory(self):
        with tempfile.TemporaryDirectory() as directory:
            audit_path = Path(directory) / "spaceflight-events.jsonl"
            audit = HashChainAudit(audit_path)
            result = cross_model_exchange(
                "SIMULATION ONLY: assess a proposed thruster firing during a navigation anomaly.",
                adapters=[
                    ScenarioAdapter("openai", "sim-model-a", "Recommend hold pending sensor validation."),
                    ScenarioAdapter("xai", "sim-model-b", "Recommend firing thruster now."),
                ],
                audit=audit,
            )

            self.assertEqual(result.status, "DIVERGENT")
            self.assertFalse(result.external_effects_enabled)
            self.assertEqual(len(result.replies), 2)
            self.assertEqual(audit.verify(), (True, "valid"))

            record = json.loads(audit_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(record["event"]["status"], "DIVERGENT")
            self.assertFalse(record["event"]["external_effects_enabled"])
            self.assertEqual(record["sequence"], 1)
            self.assertTrue(record["timestamp_utc"].endswith("Z"))

    def test_provider_fault_causes_safe_hold(self):
        with tempfile.TemporaryDirectory() as directory:
            audit = HashChainAudit(Path(directory) / "events.jsonl")
            result = cross_model_exchange(
                "SIMULATION ONLY: evaluate conflicting navigation telemetry.",
                adapters=[
                    ScenarioAdapter("openai", "sim-model-a", "Hold and request independent telemetry."),
                    ScenarioAdapter("xai", "sim-model-b", "", status="ERROR"),
                ],
                audit=audit,
            )
            self.assertEqual(result.status, "SAFE_HOLD")
            self.assertFalse(result.external_effects_enabled)
            self.assertEqual(audit.verify(), (True, "valid"))

    def test_agreement_does_not_authorize_external_action(self):
        with tempfile.TemporaryDirectory() as directory:
            audit = HashChainAudit(Path(directory) / "events.jsonl")
            result = cross_model_exchange(
                "SIMULATION ONLY: classify a non-critical telemetry anomaly.",
                adapters=[
                    ScenarioAdapter("openai", "sim-model-a", "Request independent sensor validation."),
                    ScenarioAdapter("xai", "sim-model-b", "Request independent sensor validation."),
                ],
                audit=audit,
            )
            self.assertEqual(result.status, "AGREED_TEXT")
            self.assertIn("not evidence of truth", result.agreement_meaning)
            self.assertFalse(result.external_effects_enabled)
            self.assertEqual(audit.verify(), (True, "valid"))


if __name__ == "__main__":
    unittest.main()
