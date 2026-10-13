import unittest
from unittest.mock import patch

from model_providers.registry import CommunityProviderRegistry, _validate_endpoint_url


class CommunityProviderRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = CommunityProviderRegistry()

    def test_register_returns_public_metadata_only(self):
        with patch("model_providers.registry._assert_public_dns"):
            record = self.registry.register(
                display_name="My Model",
                endpoint_url="https://models.example.com",
                model_name="community-v1",
                api_key="private-api-key",
                owner_token="x" * 40,
            )
        self.assertEqual(record["display_name"], "My Model")
        self.assertNotIn("api_key", record)
        self.assertNotIn("owner_token_hash", record)
        self.assertEqual(len(self.registry.list_public()), 1)

    def test_owner_token_required_to_unregister(self):
        with patch("model_providers.registry._assert_public_dns"):
            record = self.registry.register(
                display_name="My Model",
                endpoint_url="https://models.example.com",
                model_name="community-v1",
                owner_token="x" * 40,
            )
        self.assertFalse(self.registry.remove(record["provider_id"], "wrong-token"))
        self.assertTrue(self.registry.remove(record["provider_id"], "x" * 40))
        self.assertEqual(self.registry.list_public(), [])

    def test_rejects_plain_http_and_local_endpoints(self):
        for endpoint in ("http://models.example.com", "https://127.0.0.1", "https://printer.local"):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                _validate_endpoint_url(endpoint)

    def test_rejects_endpoint_credentials_and_query(self):
        for endpoint in ("https://user:pass@models.example.com", "https://models.example.com?token=secret"):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                _validate_endpoint_url(endpoint)


if __name__ == "__main__":
    unittest.main()
