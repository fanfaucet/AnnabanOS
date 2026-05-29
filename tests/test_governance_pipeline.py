import asyncio
import tempfile
import unittest

from annaban_benchmark.audit import AuditLogger
from annaban_benchmark.orchestrator import AnnabanOrchestrator


class GovernancePipelineTests(unittest.TestCase):
    def test_audit_hash_chain_verifies(self):
        logger = AuditLogger()
        logger.record("route", {"model": "gpt"})
        logger.record("normalize", {"answer": "unchanged"})
        self.assertTrue(logger.verify())

    def test_audit_log_reloads_from_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/audit.jsonl"
            logger = AuditLogger(path)
            logger.record("route", {"model": "gpt"})
            reloaded = AuditLogger(path)
            self.assertTrue(reloaded.verify())
            self.assertEqual(logger.last_hash, reloaded.last_hash)

    def test_orchestrator_returns_normalized_audited_output(self):
        result = asyncio.run(AnnabanOrchestrator().run("Maybe route this quickly", {"task_type": "fast"}))
        self.assertTrue(result["audit_verified"])
        self.assertEqual(result["output"]["metadata"]["model"], "grok")
        self.assertIn("answer", result["output"])


if __name__ == "__main__":
    unittest.main()
