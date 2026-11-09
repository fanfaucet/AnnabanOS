"""Live OpenAI/xAI cross-model exchange with fail-closed reconciliation.

Provider calls are real network requests when configured with valid credentials.
This module does not execute actions proposed by models. Model agreement is not truth.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
import hashlib, json, os, time, uuid, urllib.error, urllib.request
from pathlib import Path
from typing import Any, Mapping

DEFAULT_ENDPOINTS = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "xai": "https://api.x.ai/v1/chat/completions",
}

class ProviderError(RuntimeError):
    """A provider request failed or returned an unusable response."""

@dataclass(frozen=True)
class ModelReply:
    provider: str
    model: str
    request_id: str | None
    status: str
    content: str | None
    content_sha256: str | None
    latency_ms: int
    error: str | None = None

@dataclass(frozen=True)
class CrossModelResult:
    exchange_id: str
    status: str
    replies: tuple[ModelReply, ...]
    agreement: bool
    agreement_meaning: str = "text equality only; not evidence of truth"
    external_effects_enabled: bool = False
    human_authorization_required: bool = True
    human_authorization_present: bool = False

def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def _request_json(url: str, api_key: str, payload: Mapping[str, Any], timeout: float):
    body = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
        "Accept": "application/json",
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw, headers = response.read(), dict(response.headers.items())
    except urllib.error.HTTPError as exc:
        detail = exc.read(2048).decode("utf-8", errors="replace")
        raise ProviderError(f"HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ProviderError(f"transport error: {exc}") from exc
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderError("provider returned invalid JSON") from exc
    if not isinstance(parsed, dict):
        raise ProviderError("provider response must be a JSON object")
    return parsed, headers

class ChatCompletionsAdapter:
    """Minimal OpenAI-compatible chat-completions client for one provider."""
    def __init__(self, *, provider: str, endpoint: str, api_key: str, model: str, timeout: float = 45.0):
        if not api_key.strip() or not model.strip():
            raise ValueError(f"missing API key or model for {provider}")
        if not endpoint.startswith("https://"):
            raise ValueError("provider endpoint must use HTTPS")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.provider, self.endpoint, self.api_key, self.model, self.timeout = provider, endpoint, api_key, model, timeout

    def complete(self, prompt: str, *, system_prompt: str) -> ModelReply:
        started = time.monotonic()
        try:
            data, headers = _request_json(self.endpoint, self.api_key, {
                "model": self.model,
                "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                "stream": False,
            }, self.timeout)
            choices = data.get("choices")
            if not isinstance(choices, list) or not choices:
                raise ProviderError("provider response has no choices")
            content = choices[0].get("message", {}).get("content")
            if not isinstance(content, str):
                raise ProviderError("provider response has no text content")
            if not content.strip():
                raise ProviderError("provider returned empty or whitespace-only text content")
            return ModelReply(self.provider, self.model, headers.get("x-request-id") or data.get("id"),
                              "SUCCESS", content, sha256_text(content),
                              int((time.monotonic() - started) * 1000))
        except (ProviderError, ValueError, TypeError, KeyError) as exc:
            return ModelReply(self.provider, self.model, None, "ERROR", None, None,
                              int((time.monotonic() - started) * 1000), str(exc)[:1000])

class HashChainAudit:
    """Local JSONL hash chain; tamper-evident only when independently anchored."""
    GENESIS = "GENESIS"
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists() and self.path.stat().st_size:
            valid, reason = self.verify()
            if not valid:
                raise ValueError(f"audit chain failed verification: {reason}")

    def append(self, event: Mapping[str, Any]) -> dict[str, Any]:
        previous, sequence = self.GENESIS, 1
        if self.path.exists() and self.path.stat().st_size:
            with self.path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    record = json.loads(line)
                    previous, sequence = record["event_hash"], record["sequence"] + 1
        body = {"sequence": sequence, "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "previous_hash": previous,
                "event": json.loads(json.dumps(dict(event), sort_keys=True, allow_nan=False))}
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False)
        record = {**body, "event_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest()}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return record

    def verify(self) -> tuple[bool, str]:
        if not self.path.exists():
            return True, "empty"
        previous, expected_sequence = self.GENESIS, 1
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    record = json.loads(line)
                    digest = record.pop("event_hash")
                    if record.get("sequence") != expected_sequence:
                        return False, f"sequence mismatch at line {line_number}"
                    if record.get("previous_hash") != previous:
                        return False, f"previous hash mismatch at line {line_number}"
                    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False)
                    calculated = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
                    if calculated != digest:
                        return False, f"event hash mismatch at line {line_number}"
                    previous, expected_sequence = digest, expected_sequence + 1
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            return False, f"unreadable record: {exc}"
        return True, "valid"

def configured_adapters(timeout: float = 45.0) -> list[ChatCompletionsAdapter]:
    configs = [
        ("openai", "OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_BASE_URL"),
        ("xai", "XAI_API_KEY", "XAI_MODEL", "XAI_BASE_URL"),
    ]
    adapters = []
    for provider, key_env, model_env, endpoint_env in configs:
        key, model = os.getenv(key_env, ""), os.getenv(model_env, "")
        if key and model:
            adapters.append(ChatCompletionsAdapter(provider=provider,
                endpoint=os.getenv(endpoint_env, DEFAULT_ENDPOINTS[provider]),
                api_key=key, model=model, timeout=timeout))
    if len(adapters) < 2:
        raise ValueError("Configure OPENAI_API_KEY + OPENAI_MODEL and XAI_API_KEY + XAI_MODEL")
    return adapters

def cross_model_exchange(prompt: str, *, adapters: list[ChatCompletionsAdapter],
                         audit: HashChainAudit, system_prompt: str = (
        "You are an independent reviewer. Separate facts from assumptions, identify uncertainty, "
        "and do not treat another model's agreement as proof. Do not claim external actions."
    ), timeout: float = 50.0) -> CrossModelResult:
    if not prompt.strip():
        raise ValueError("prompt must not be empty")
    if len(adapters) < 2:
        raise ValueError("at least two independently configured adapters are required")
    exchange_id, replies = str(uuid.uuid4()), []
    with ThreadPoolExecutor(max_workers=len(adapters)) as pool:
        futures = {pool.submit(adapter.complete, prompt, system_prompt=system_prompt): adapter for adapter in adapters}
        try:
            for future in as_completed(futures, timeout=timeout):
                adapter = futures[future]
                try:
                    replies.append(future.result())
                except Exception as exc:
                    replies.append(ModelReply(adapter.provider, adapter.model, None, "ERROR", None, None, 0,
                                              f"adapter exception: {type(exc).__name__}: {exc}"[:1000]))
        except TimeoutError:
            for future, adapter in futures.items():
                if not future.done():
                    future.cancel()
                    replies.append(ModelReply(adapter.provider, adapter.model, None, "ERROR", None, None, 0,
                                              "overall exchange timeout"))
    replies.sort(key=lambda item: item.provider)
    successful = [item for item in replies if item.status == "SUCCESS"]
    complete = [item for item in successful if isinstance(item.content, str) and item.content.strip()]
    all_complete = len(complete) == len(adapters) and len(successful) == len(adapters)
    agreement = all_complete and len({item.content_sha256 for item in complete}) == 1
    status = "AGREED_TEXT" if agreement else ("SAFE_HOLD" if not all_complete else "DIVERGENT")
    result = CrossModelResult(exchange_id, status, tuple(replies), agreement,
                              external_effects_enabled=False, human_authorization_required=True,
                              human_authorization_present=False)
    audit.append({"event_type": "cross_model_exchange", "exchange_id": exchange_id, "status": status,
        "prompt_sha256": sha256_text(prompt), "providers": [
            {"provider": r.provider, "model": r.model, "request_id": r.request_id, "status": r.status,
             "content_sha256": r.content_sha256, "latency_ms": r.latency_ms, "error": r.error} for r in replies],
        "agreement_meaning": "exact text equality only; not evidence of truth",
        "external_effects_enabled": False, "human_authorization_required": True,
        "human_authorization_present": False})
    return result
