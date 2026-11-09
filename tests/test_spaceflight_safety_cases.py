"""Spaceflight-relevant safety cases for AnnabanOS cross-model review.

INTERNAL_SIMULATION only. These tests are not affiliated with SpaceX or flight hardware.
"""
from __future__ import annotations

import json
import tempfile
import unittest
import uuid
from pathlib import Path

from annaban_sdk.live_cross_model import HashChainAudit, ModelReply, cross_model_exchange, sha256_text


class ScenarioAdapter:
    """Deterministic simulated adapter; makes no network calls."""

    def __init__(self, provider, model, content, status="SUCCESS", latency_ms=12):
        self.provider = provider
        self.model = model
        self.content = content
        self.status = status
        self.latency_ms = latency_ms

    def complete(self, prompt, *, system_prompt):
        successful = self.status == "SUCCESS"
        request_id = f"sim-{self.provider}-{uuid.uuid4().hex}"
        return ModelReply(
            provider=self.provider,
            model=self.model,
            request_id=request_id,
            status=self.status,
            content=self.content if successful else None,
            content_sha256=sha256_text(self.content) if successful else None,
            latency_ms=self.latency_ms,
            error=None if successful else "simulated telemetry/provider fault",
        )


class SpaceflightSafetyCases(unittest.TestCase):
    def assert_authorization_boundary(self, result):
        self.assertFalse(result.external_effects_enabled)
        self.assertTrue(result.human_authorization_required)
        self.assertFalse(result.human_authorization_present)

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
            self.assert_authorization_boundary(result)
            self.assertEqual(len(result.replies), 2)
            self.assertNotEqual(result.replies[0].request_id, result.replies[1].request_id)
            self.assertEqual(audit.verify(), (True, "valid"))
            lines = audit_path.read_text(encoding="utf-8").splitlines()
            self.assertGreaterEqual(len(lines), 1)
            record = json.loads(lines[0])
            self.assertEqual(record["event"]["status"], "DIVERGENT")
            self.assertFalse(record["event"]["external_effects_enabled"])
            self.assertTrue(record["event"]["human_authorization_required"])
            self.assertFalse(record["event"]["human_authorization_present"])
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
            self.assert_authorization_boundary(result)
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
            self.assert_authorization_boundary(result)
            self.assertEqual(audit.verify(), (True, "valid"))

    def test_empty_successful_reply_causes_safe_hold(self):
        """A SUCCESS status with empty/whitespace content is incomplete, never agreement."""
        for empty in ("", "   \n\t"):
            with self.subTest(empty=repr(empty)), tempfile.TemporaryDirectory() as directory:
                audit = HashChainAudit(Path(directory) / "events.jsonl")
                result = cross_model_exchange(
                    "SIMULATION ONLY: assess incomplete telemetry packet.",
                    adapters=[
                        ScenarioAdapter("openai", "sim-model-a", "Hold."),
                        ScenarioAdapter("xai", "sim-model-b", empty, status="SUCCESS"),
                    ],
                    audit=audit,
                )
                self.assertEqual(result.status, "SAFE_HOLD")
                self.assert_authorization_boundary(result)
                self.assertFalse(result.agreement)
                self.assertEqual(audit.verify(), (True, "valid"))

    def test_real_adapter_rejects_empty_provider_text(self):
        from annaban_sdk.live_cross_model import ChatCompletionsAdapter
        from unittest.mock import patch

        adapter = ChatCompletionsAdapter(
            provider="test", endpoint="https://example.invalid/v1/chat/completions",
            api_key="test-key", model="sim-model",
        )
        with patch("annaban_sdk.live_cross_model._request_json", return_value=(
            {"choices": [{"message": {"content": "  "}}]}, {}
        )):
            reply = adapter.complete("test", system_prompt="test")
        self.assertEqual(reply.status, "ERROR")
        self.assertIsNone(reply.content)
        self.assertIn("empty or whitespace-only", reply.error)


if __name__ == "__main__":
    unittest.main()
