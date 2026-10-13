"""Printful mock-up API prototype with an explicit human-approval precondition.

This module uses the Python standard library only. It is a local MVD, not a
production integration. Callers must supply an approval record bound to the
exact design/product request before any network request is made.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlparse

API_BASE = "https://api.printful.com"
REQUIRED_OPERATOR = "Jacob Wayne Kinnaird"
_ALLOWED_DOWNLOAD_SUFFIXES = (".printful.com", ".printful.me")
Transport = Callable[[str, str, Mapping[str, str], bytes | None], tuple[int, Mapping[str, str], bytes]]


class PrintfulAPIError(RuntimeError):
    """Raised when Printful returns an error or an unexpected response."""


class ApprovalRequired(PermissionError):
    """Raised before network access if a valid matching approval is absent."""


def _urllib_transport(
    method: str, url: str, headers: Mapping[str, str], body: bytes | None
) -> tuple[int, Mapping[str, str], bytes]:
    request = urllib.request.Request(url, data=body, headers=dict(headers), method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, dict(response.headers.items()), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers.items()), exc.read()


@dataclass(frozen=True)
class MockupApproval:
    approval_id: str
    status: str
    operator: str
    design_id: str
    design_version: str
    product_id: str
    variant_ids: tuple[int, ...]


class PrintfulMockupClient:
    """Small v2 client. API response shapes should be verified against current docs."""

    def __init__(
        self,
        token: str | None = None,
        *,
        transport: Transport = _urllib_transport,
        api_base: str = API_BASE,
    ) -> None:
        self.token = token or os.getenv("PRINTFUL_STORE_TOKEN", "")
        if not self.token:
            raise ValueError("PRINTFUL_STORE_TOKEN is required")
        parsed = urlparse(api_base)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("api_base must be an HTTPS URL")
        self.api_base = api_base.rstrip("/")
        self._transport = transport

    @staticmethod
    def _check_approval(approval: MockupApproval, request: Mapping[str, Any]) -> None:
        """Fail closed unless the approval binds the exact request and named operator."""
        if approval.status != "APPROVED":
            raise ApprovalRequired("Human Authority Gate status must be APPROVED")
        if approval.operator != REQUIRED_OPERATOR:
            raise ApprovalRequired("Approval operator does not match the configured sovereign operator")
        if not approval.approval_id.strip():
            raise ApprovalRequired("Approval ID is required")
        if approval.design_id != request.get("design_id"):
            raise ApprovalRequired("Approval design_id does not match request")
        if approval.design_version != request.get("design_version"):
            raise ApprovalRequired("Approval design_version does not match request")
        if approval.product_id != str(request.get("product_id")):
            raise ApprovalRequired("Approval product_id does not match request")
        try:
            variants = tuple(int(value) for value in request.get("variant_ids", ()))
        except (TypeError, ValueError) as exc:
            raise ApprovalRequired("Request variant_ids are invalid") from exc
        if not variants or variants != approval.variant_ids:
            raise ApprovalRequired("Approval variant_ids do not match request")

    def _request(
        self, method: str, path: str, payload: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        url = self.api_base + path
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        status, _response_headers, raw = self._transport(method, url, headers, body)
        if status < 200 or status >= 300:
            # Do not echo response bodies; they may contain provider or user data.
            raise PrintfulAPIError(f"Printful API returned HTTP {status}")
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PrintfulAPIError("Printful API returned invalid JSON") from exc
        if not isinstance(parsed, dict):
            raise PrintfulAPIError("Printful API response must be a JSON object")
        return parsed

    def create_mockup_task(
        self, request: Mapping[str, Any], approval: MockupApproval
    ) -> dict[str, Any]:
        """Create a v2 mock-up task only after checking a matching approval."""
        self._check_approval(approval, request)
        payload = request.get("payload")
        if not isinstance(payload, dict) or not payload:
            raise ValueError("request.payload must contain the version-specific Printful task payload")
        response = self._request("POST", "/v2/mockup-tasks", payload)
        task_id = self._extract_task_id(response)
        if not task_id:
            raise PrintfulAPIError("Printful response did not include a task ID")
        return {"task_id": task_id, "response": response, "approval_id": approval.approval_id}

    def get_mockup_task(self, task_id: str) -> dict[str, Any]:
        """Fetch a task result; this method does not create or publish products."""
        if not task_id or not task_id.strip():
            raise ValueError("task_id is required")
        query = urllib.parse.urlencode({"id": task_id})
        return self._request("GET", f"/v2/mockup-tasks?{query}")

    def wait_for_mockup_task(
        self,
        task_id: str,
        *,
        timeout_seconds: float = 120,
        initial_interval: float = 1,
        max_interval: float = 10,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> dict[str, Any]:
        """Poll with bounded exponential backoff until a terminal state or timeout."""
        deadline = clock() + timeout_seconds
        interval = max(0.1, initial_interval)
        while clock() < deadline:
            result = self.get_mockup_task(task_id)
            state = self._extract_state(result)
            if state in {"completed", "succeeded", "finished", "failed", "error"}:
                return result
            sleep(min(interval, max(0.0, deadline - clock())))
            interval = min(max_interval, interval * 2)
        raise TimeoutError(f"Printful mock-up task {task_id!r} did not finish before timeout")

    @staticmethod
    def _extract_task_id(response: Mapping[str, Any]) -> str | None:
        candidates = [response, response.get("data"), response.get("result")]
        for candidate in candidates:
            if isinstance(candidate, dict):
                value = candidate.get("id") or candidate.get("task_id") or candidate.get("task_key")
                if value is not None:
                    return str(value)
        return None

    @staticmethod
    def _extract_state(response: Mapping[str, Any]) -> str:
        candidates = [response, response.get("data"), response.get("result")]
        for candidate in candidates:
            if isinstance(candidate, dict):
                value = candidate.get("status") or candidate.get("state")
                if isinstance(value, str):
                    return value.lower()
        return "unknown"

    def download_mockup(self, url: str, destination: str | Path) -> str:
        """Download a temporary mock-up image from a recognized Printful host.

        Downloads do not send the API bearer token. Production deployments should
        also use hardened egress controls and validate redirects at the transport.
        """
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not any(
            host.endswith(suffix) and host != suffix.lstrip(".")
            for suffix in _ALLOWED_DOWNLOAD_SUFFIXES
        ):
            raise ValueError("Mock-up URL must use HTTPS on an approved Printful host")
        status, headers, data = self._transport("GET", url, {"Accept": "image/*"}, None)
        if status < 200 or status >= 300:
            raise PrintfulAPIError(f"Mock-up download returned HTTP {status}")
        content_type = next(
            (value for key, value in headers.items() if key.lower() == "content-type"), ""
        ).split(";", 1)[0].strip().lower()
        if not content_type.startswith("image/"):
            raise PrintfulAPIError("Mock-up response is not an image")
        if not data:
            raise PrintfulAPIError("Mock-up image response was empty")
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        import hashlib
        return hashlib.sha256(data).hexdigest()
