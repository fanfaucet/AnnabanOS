import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlparse

from mvd.printful_mockup_client import (
    ApprovalRequired,
    MockupApproval,
    PrintfulAPIError,
    PrintfulMockupClient,
)


def approved():
    return MockupApproval(
        approval_id="approval-001",
        status="APPROVED",
        operator="Jacob Wayne Kinnaird",
        design_id="ff-tee-001",
        design_version="v1",
        product_id="71",
        variant_ids=(4011,),
    )


def request():
    return {
        "design_id": "ff-tee-001",
        "design_version": "v1",
        "product_id": "71",
        "variant_ids": [4011],
        "payload": {"catalog_product_id": 71, "variant_ids": [4011]},
    }


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, method, url, headers, body):
        self.calls.append((method, url, dict(headers), body))
        status, response_headers, response_body = self.responses.pop(0)
        return status, response_headers, response_body


class PrintfulMockupClientTests(unittest.TestCase):
    def test_non_approved_request_never_calls_api(self):
        transport = FakeTransport([])
        client = PrintfulMockupClient("test-token", transport=transport)
        for status in ("PENDING", "REJECTED", "REVOKED"):
            with self.subTest(status=status):
                invalid = MockupApproval(
                    approval_id="a", status=status, operator="Jacob Wayne Kinnaird",
                    design_id="ff-tee-001", design_version="v1", product_id="71",
                    variant_ids=(4011,),
                )
                with self.assertRaises(ApprovalRequired):
                    client.create_mockup_task(request(), invalid)
        self.assertEqual(transport.calls, [])

    def test_mismatched_operator_or_payload_fails_closed(self):
        transport = FakeTransport([])
        client = PrintfulMockupClient("test-token", transport=transport)
        wrong_operator = MockupApproval(
            approval_id="a", status="APPROVED", operator="Someone Else",
            design_id="ff-tee-001", design_version="v1", product_id="71",
            variant_ids=(4011,),
        )
        with self.assertRaises(ApprovalRequired):
            client.create_mockup_task(request(), wrong_operator)
        changed = request()
        changed["design_version"] = "v2"
        with self.assertRaises(ApprovalRequired):
            client.create_mockup_task(changed, approved())
        changed_payload = request()
        changed_payload["payload"]["variant_ids"] = [9999]
        with self.assertRaises(ApprovalRequired):
            client.create_mockup_task(changed_payload, approved())
        self.assertEqual(transport.calls, [])

    def test_approved_request_creates_task(self):
        transport = FakeTransport([
            (200, {"content-type": "application/json"}, json.dumps({"data": {"id": "task-123"}}).encode())
        ])
        client = PrintfulMockupClient("test-token", transport=transport)
        result = client.create_mockup_task(request(), approved())
        self.assertEqual(result["task_id"], "task-123")
        self.assertEqual(result["approval_id"], "approval-001")
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(transport.calls[0][0], "POST")
        self.assertEqual(urlparse(transport.calls[0][1]).path, "/v2/mockup-tasks")
        self.assertNotIn("test-token", json.dumps(result))

    def test_polling_returns_terminal_task(self):
        transport = FakeTransport([
            (200, {}, json.dumps({"data": {"status": "completed"}}).encode())
        ])
        client = PrintfulMockupClient("test-token", transport=transport)
        result = client.wait_for_mockup_task("task-123", timeout_seconds=2)
        self.assertEqual(result["data"]["status"], "completed")

    def test_non_image_download_rejected(self):
        transport = FakeTransport([(200, {"Content-Type": "text/html"}, b"<html>no</html>")])
        client = PrintfulMockupClient("test-token", transport=transport)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PrintfulAPIError):
                client.download_mockup("https://files.printful.com/mockup.png", Path(tmp) / "mock.png")

    def test_untrusted_download_host_rejected_before_network(self):
        transport = FakeTransport([])
        client = PrintfulMockupClient("test-token", transport=transport)
        with self.assertRaises(ValueError):
            client.download_mockup("https://example.com/mockup.png", "/tmp/mock.png")
        self.assertEqual(transport.calls, [])

    def test_image_download_persists_and_returns_checksum(self):
        image_bytes = b"fake-image-bytes"
        transport = FakeTransport([(200, {"Content-Type": "image/png"}, image_bytes)])
        client = PrintfulMockupClient("test-token", transport=transport)
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "assets" / "mock.png"
            digest = client.download_mockup("https://files.printful.com/mockup.png", destination)
            self.assertTrue(destination.exists())
            self.assertEqual(destination.read_bytes(), image_bytes)
            self.assertEqual(len(digest), 64)


if __name__ == "__main__":
    unittest.main()
