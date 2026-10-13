"""Self-service registry for community-hosted OpenAI-compatible model endpoints.

Prototype note: records and provider credentials are process-local. Production requires
encrypted durable storage, authenticated accounts, and outbound network restrictions.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import ipaddress
import socket
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

import httpx


@dataclass
class CommunityProvider:
    provider_id: str
    display_name: str
    endpoint_url: str
    model_name: str
    api_key: str
    owner_token_hash: str

    def public_record(self) -> dict[str, str]:
        return {
            "provider_id": self.provider_id,
            "display_name": self.display_name,
            "model_name": self.model_name,
            "protocol": "openai-compatible",
            "status": "registered",
        }


def _owner_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _validate_endpoint_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Provider endpoints must use an https:// URL.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Endpoint URLs must not contain credentials, query strings, or fragments.")
    if parsed.port not in (None, 443):
        raise ValueError("Provider endpoints must use HTTPS on port 443.")
    host = parsed.hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain"} or host.endswith((".local", ".internal", ".localhost")):
        raise ValueError("Local and internal hostnames are not allowed.")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        if not ip.is_global:
            raise ValueError("Provider endpoint must use a public IP address.")
        raise ValueError("Use a public DNS hostname rather than an IP literal.")
    return value.strip().rstrip("/")


def _assert_public_dns(host: str) -> None:
    """Reject DNS names resolving to private, loopback, link-local, or reserved IPs."""
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError("Provider hostname did not resolve.") from exc
    if not addresses:
        raise ValueError("Provider hostname did not resolve.")
    for item in addresses:
        if not ipaddress.ip_address(item[4][0]).is_global:
            raise ValueError("Provider hostname must resolve only to public IP addresses.")


class CommunityProviderRegistry:
    """In-memory registry; users explicitly opt in to each provider per request."""

    def __init__(self) -> None:
        self._providers: dict[str, CommunityProvider] = {}

    def register(self, *, display_name: str, endpoint_url: str, model_name: str,
                 owner_token: str, api_key: str = "") -> dict[str, str]:
        if len(owner_token) < 32:
            raise ValueError("owner_token must be at least 32 characters.")
        name, model = display_name.strip(), model_name.strip()
        if not name or len(name) > 80:
            raise ValueError("display_name must contain 1–80 characters.")
        if not model or len(model) > 160:
            raise ValueError("model_name must contain 1–160 characters.")
        endpoint = _validate_endpoint_url(endpoint_url)
        host = urlparse(endpoint).hostname
        assert host is not None
        _assert_public_dns(host)
        provider = CommunityProvider(
            provider_id=str(uuid4()), display_name=name, endpoint_url=endpoint,
            model_name=model, api_key=api_key.strip(),
            owner_token_hash=_owner_hash(owner_token),
        )
        self._providers[provider.provider_id] = provider
        return provider.public_record()

    def list_public(self) -> list[dict[str, str]]:
        return [provider.public_record() for provider in self._providers.values()]

    def remove(self, provider_id: str, owner_token: str) -> bool:
        provider = self._providers.get(provider_id)
        if provider is None or not hmac.compare_digest(provider.owner_token_hash, _owner_hash(owner_token)):
            return False
        del self._providers[provider_id]
        return True

    def get(self, provider_id: str) -> CommunityProvider | None:
        return self._providers.get(provider_id)

    async def complete(self, provider_id: str, prompt: str, timeout_seconds: float = 20.0) -> str:
        provider = self._providers.get(provider_id)
        if provider is None:
            raise KeyError("Unknown community provider.")
        host = urlparse(provider.endpoint_url).hostname
        if not host:
            raise ValueError("Invalid provider endpoint.")
        # Production still needs network egress controls against DNS rebinding.
        await asyncio.to_thread(_assert_public_dns, host)
        headers = {"Content-Type": "application/json"}
        if provider.api_key:
            headers["Authorization"] = f"Bearer {provider.api_key}"
        async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=False) as client:
            response = await client.post(
                f"{provider.endpoint_url}/v1/chat/completions",
                headers=headers,
                json={"model": provider.model_name,
                      "messages": [{"role": "user", "content": prompt}],
                      "stream": False},
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
        try:
            answer = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("Provider returned an invalid OpenAI-compatible response.") from exc
        if not isinstance(answer, str):
            raise ValueError("Provider response content must be text.")
        return answer


community_provider_registry = CommunityProviderRegistry()
