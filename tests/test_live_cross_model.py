import json
import tempfile
import unittest
from pathlib import Path
from annaban_sdk.live_cross_model import HashChainAudit, ModelReply, cross_model_exchange, sha256_text

class FakeAdapter:
    def __init__(self, provider, content, status="SUCCESS"):
        self.provider, self.model, self.content, self.status = provider, provider + "-test-model", content, status
    def complete(self, prompt, *, system_prompt):
        ok = self.status == "SUCCESS"
        return ModelReply(self.provider, self.model, self.provider + "-req", self.status,
            self.content if ok else None, sha256_text(self.content) if ok else None, 1,
            None if ok else "test provider failure")

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

if __name__ == "__main__":
    unittest.main()
