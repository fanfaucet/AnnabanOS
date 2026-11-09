import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from annaban_sdk.live_cross_model import (
    ChatCompletionsAdapter, HashChainAudit, ModelReply, TOOL_CALLS_PROPOSED,
    cross_model_exchange, sha256_text,
)

TOOL = {"type": "function", "function": {
    "name": "lookup_status",
    "description": "Look up a non-sensitive status label.",
    "parameters": {"type": "object", "properties": {"item": {"type": "string", "maxLength": 40}},
                   "required": ["item"], "additionalProperties": False},
}}

class FakeAdapter:
    def __init__(self, provider, content, status="SUCCESS", tool_calls=()):
        self.provider, self.model, self.content, self.status = provider, provider + "-test-model", content, status
        self.tool_calls = tuple(tool_calls)
    def complete(self, prompt, *, system_prompt, tools=None, tool_choice="auto"):
        ok = self.status == "SUCCESS"
        return ModelReply(self.provider, self.model, self.provider + "-req", self.status,
            self.content if ok else None, sha256_text(self.content) if ok else None, 1,
            None if ok else "test provider failure", self.tool_calls)

class LiveCrossModelTests(unittest.TestCase):
    def test_matching_text_is_not_truth(self):
        with tempfile.TemporaryDirectory() as d:
            audit = HashChainAudit(Path(d) / "audit.jsonl")
            result = cross_model_exchange("prompt", adapters=[FakeAdapter("openai", "same"), FakeAdapter("xai", "same")], audit=audit)
            self.assertEqual(result.status, "AGREED_TEXT")
            self.assertTrue(result.agreement)
            self.assertFalse(result.external_effects_enabled)
            self.assertIn("not evidence of truth", result.agreement_meaning)
            self.assertEqual(audit.verify(), (True, "valid"))

    def test_divergence_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            result = cross_model_exchange("prompt", adapters=[FakeAdapter("openai", "A"), FakeAdapter("xai", "B")],
                                          audit=HashChainAudit(Path(d) / "audit.jsonl"))
            self.assertEqual(result.status, "DIVERGENT")
            self.assertFalse(result.agreement)
            self.assertEqual(len(result.replies), 2)

    def test_provider_error_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            result = cross_model_exchange("prompt", adapters=[FakeAdapter("openai", "A"), FakeAdapter("xai", "", "ERROR")],
                                          audit=HashChainAudit(Path(d) / "audit.jsonl"))
            self.assertEqual(result.status, "SAFE_HOLD")
            self.assertFalse(result.external_effects_enabled)

    def test_audit_mutation_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "audit.jsonl"
            audit = HashChainAudit(path)
            audit.append({"event_type": "test", "payload": "original"})
            row = json.loads(path.read_text(encoding="utf-8"))
            row["event"]["payload"] = "mutated"
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            self.assertFalse(audit.verify()[0])
            with self.assertRaises(ValueError):
                HashChainAudit(path)

    def test_tool_call_is_proposed_not_executed(self):
        from annaban_sdk.live_cross_model import ToolCallProposal
        proposal = ToolCallProposal("xai", "call-1", "lookup_status", {"item": "sensor"},
                                    '{"item":"sensor"}', sha256_text('{"item":"sensor"}'), True)
        with tempfile.TemporaryDirectory() as d:
            result = cross_model_exchange("check sensor", adapters=[
                FakeAdapter("openai", "No call."), FakeAdapter("xai", None, tool_calls=(proposal,))
            ], audit=HashChainAudit(Path(d) / "audit.jsonl"), tools=[TOOL])
            self.assertEqual(result.status, TOOL_CALLS_PROPOSED)
            self.assertFalse(result.tool_execution_enabled)
            self.assertFalse(result.external_effects_enabled)
            self.assertTrue(result.replies[1].tool_calls[0].schema_valid)

    def test_adapter_sends_xai_openai_compatible_tool_schema(self):
        adapter = ChatCompletionsAdapter(provider="xai", endpoint="https://api.x.ai/v1/chat/completions",
                                          api_key="test", model="test-model")
        provider_payload = {"choices": [{"message": {"content": None, "tool_calls": [
            {"id": "call-1", "type": "function", "function": {"name": "lookup_status", "arguments": '{"item":"sensor}'}}
        ]}}]}
        # A malformed provider argument string must be surfaced as ERROR, not executed.
        with patch("annaban_sdk.live_cross_model._request_json", return_value=(provider_payload, {"x-request-id": "req"})) as request:
            reply = adapter.complete("prompt", system_prompt="system", tools=[TOOL])
        self.assertEqual(request.call_args.args[2]["tools"][0]["function"]["name"], "lookup_status")
        self.assertEqual(reply.status, "ERROR")
        self.assertFalse(reply.tool_calls)

    def test_adapter_parses_valid_xai_tool_call_and_schema_checks_args(self):
        adapter = ChatCompletionsAdapter(provider="xai", endpoint="https://api.x.ai/v1/chat/completions",
                                          api_key="test", model="test-model")
        provider_payload = {"choices": [{"message": {"content": None, "tool_calls": [
            {"id": "call-2", "type": "function", "function": {"name": "lookup_status", "arguments": '{"item":"sensor}'}}
        ]}}]}
        provider_payload["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = '{"item":"sensor"}'
        with patch("annaban_sdk.live_cross_model._request_json", return_value=(provider_payload, {"x-request-id": "req"})):
            reply = adapter.complete("prompt", system_prompt="system", tools=[TOOL])
        self.assertEqual(reply.status, "SUCCESS")
        self.assertEqual(reply.tool_calls[0].name, "lookup_status")
        self.assertTrue(reply.tool_calls[0].schema_valid)
        self.assertEqual(reply.request_id, "req")

    def test_unknown_tool_is_not_allowlisted(self):
        from annaban_sdk.live_cross_model import _parse_tool_calls
        proposal = _parse_tool_calls("xai", [{"id": "x", "function": {"name": "shell", "arguments": "{}"}}], [TOOL])[0]
        self.assertFalse(proposal.schema_valid)
        self.assertIn("allowlist", proposal.validation_error)

if __name__ == "__main__":
    unittest.main()
