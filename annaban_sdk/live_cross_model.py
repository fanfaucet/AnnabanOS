"""Live OpenAI/xAI cross-model exchange with fail-closed tool-call proposals.

Tool calls returned by models are parsed, validated against caller-supplied schemas,
audited, and returned as proposals. This module NEVER executes model-requested tools.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import hashlib, json, os, time, uuid, urllib.error, urllib.request
from pathlib import Path
from typing import Any, Mapping, Sequence

DEFAULT_ENDPOINTS = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "xai": "https://api.x.ai/v1/chat/completions",
}
TOOL_CALLS_PROPOSED = "TOOL_CALLS_PROPOSED"

class ProviderError(RuntimeError):
    """A provider request failed or returned an unusable response."""

@dataclass(frozen=True)
class ToolCallProposal:
    provider: str
    call_id: str | None
    name: str
    arguments: dict[str, Any]
    arguments_json: str
    arguments_sha256: str
    schema_valid: bool
    validation_error: str | None = None

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
    tool_calls: tuple[ToolCallProposal, ...] = ()

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
    tool_execution_enabled: bool = False

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

def _normalise_tool_schemas(tools: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    normalized = []
    seen = set()
    for item in tools or ():
        if not isinstance(item, Mapping) or item.get("type") != "function":
            raise ValueError("each tool must use OpenAI-compatible {'type':'function','function':...} schema")
        fn = item.get("function")
        if not isinstance(fn, Mapping) or not isinstance(fn.get("name"), str) or not fn["name"].strip():
            raise ValueError("each tool requires a non-empty function.name")
        name = fn["name"]
        if name in seen:
            raise ValueError(f"duplicate tool name: {name}")
        seen.add(name)
        params = fn.get("parameters", {"type": "object", "properties": {}})
        if not isinstance(params, Mapping) or params.get("type") != "object":
            raise ValueError(f"tool {name} parameters must be a JSON Schema object")
        normalized.append({"type": "function", "function": {
            "name": name,
            "description": str(fn.get("description", "")),
            "parameters": dict(params),
            "strict": bool(fn.get("strict", False)),
        }})
    return normalized

def _validate_arguments(arguments: Any, schema: Mapping[str, Any]) -> str | None:
    if not isinstance(arguments, dict):
        return "tool arguments must decode to a JSON object"
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    missing = [key for key in required if key not in arguments]
    if missing:
        return "missing required argument(s): " + ", ".join(missing)
    if schema.get("additionalProperties") is False:
        extra = [key for key in arguments if key not in properties]
        if extra:
            return "unexpected argument(s): " + ", ".join(extra)
    # Conservative lightweight type checking; provider schema enforcement is not trusted alone.
    type_map = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "object": dict, "array": list}
    for key, value in arguments.items():
        rule = properties.get(key, {})
        expected = rule.get("type") if isinstance(rule, Mapping) else None
        py_type = type_map.get(expected)
        if py_type and (not isinstance(value, py_type) or (expected in ("integer", "number") and isinstance(value, bool))):
            return f"argument {key!r} must be {expected}"
        if expected == "string" and isinstance(rule, Mapping):
            if "enum" in rule and value not in rule["enum"]:
                return f"argument {key!r} is outside the allowed enum"
            if isinstance(rule.get("maxLength"), int) and len(value) > rule["maxLength"]:
                return f"argument {key!r} exceeds maxLength"
    return None

def _parse_tool_calls(provider: str, raw_calls: Any, tools: Sequence[Mapping[str, Any]] | None) -> tuple[ToolCallProposal, ...]:
    if raw_calls is None:
        return ()
    if not isinstance(raw_calls, list):
        raise ProviderError("provider tool_calls must be a list")
    schemas = {item["function"]["name"]: item["function"]["parameters"] for item in _normalise_tool_schemas(tools)}
    proposals = []
    for raw in raw_calls:
        if not isinstance(raw, dict):
            raise ProviderError("malformed tool call")
        function = raw.get("function", {})
        name = function.get("name")
        arg_text = function.get("arguments", "{}")
        if not isinstance(name, str) or not isinstance(arg_text, str):
            raise ProviderError("malformed tool call function or arguments")
        try:
            args = json.loads(arg_text)
        except json.JSONDecodeError as exc:
            raise ProviderError(f"invalid JSON arguments for tool {name}") from exc
        if not isinstance(args, dict):
            raise ProviderError(f"arguments for tool {name} must be an object")
        schema = schemas.get(name)
        validation_error = "tool name is not in caller-supplied allowlist" if schema is None else _validate_arguments(args, schema)
        canonical = json.dumps(args, sort_keys=True, separators=(",", ":"), allow_nan=False)
        proposals.append(ToolCallProposal(
            provider=provider, call_id=raw.get("id"), name=name, arguments=args,
            arguments_json=canonical, arguments_sha256=sha256_text(canonical),
            schema_valid=validation_error is None, validation_error=validation_error,
        ))
    return tuple(proposals)

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

    def complete(self, prompt: str, *, system_prompt: str,
                 tools: Sequence[Mapping[str, Any]] | None = None,
                 tool_choice: str | Mapping[str, Any] = "auto") -> ModelReply:
        started = time.monotonic()
        try:
            normalized_tools = _normalise_tool_schemas(tools)
            if not normalized_tools and tool_choice != "auto":
                raise ValueError("tool_choice requires at least one tool")
            if isinstance(tool_choice, str) and tool_choice not in ("auto", "none", "required"):
                raise ValueError("tool_choice must be auto, none, required, or a named function choice")
            payload: dict[str, Any] = {
                "model": self.model,
                "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                "stream": False,
            }
            if normalized_tools:
                payload["tools"] = normalized_tools
                payload["tool_choice"] = tool_choice
            data, headers = _request_json(self.endpoint, self.api_key, payload, self.timeout)
            choices = data.get("choices")
            if not isinstance(choices, list) or not choices:
                raise ProviderError("provider response has no choices")
            message = choices[0].get("message", {})
            if not isinstance(message, dict):
                raise ProviderError("provider response message is malformed")
            calls = _parse_tool_calls(self.provider, message.get("tool_calls"), normalized_tools)
            content = message.get("content")
            if content is not None and not isinstance(content, str):
                raise ProviderError("provider response content is not text")
            if not calls and (not isinstance(content, str) or not content.strip()):
                raise ProviderError("provider returned empty text and no tool calls")
            return ModelReply(self.provider, self.model, headers.get("x-request-id") or data.get("id"),
                              "SUCCESS", content, sha256_text(content) if isinstance(content, str) else None,
                              int((time.monotonic() - started) * 1000), None, calls)
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
    ), timeout: float = 50.0,
    tools: Sequence[Mapping[str, Any]] | None = None,
    tool_choice: str | Mapping[str, Any] = "auto") -> CrossModelResult:
    if not prompt.strip():
        raise ValueError("prompt must not be empty")
    if len(adapters) < 2:
        raise ValueError("at least two independently configured adapters are required")
    normalized_tools = _normalise_tool_schemas(tools)
    exchange_id, replies = str(uuid.uuid4()), []
    with ThreadPoolExecutor(max_workers=len(adapters)) as pool:
        futures = {pool.submit(adapter.complete, prompt, system_prompt=system_prompt,
                               tools=normalized_tools, tool_choice=tool_choice): adapter for adapter in adapters}
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
    if any(reply.tool_calls for reply in successful):
        status, agreement = TOOL_CALLS_PROPOSED, False
    else:
        complete = [item for item in successful if isinstance(item.content, str) and item.content.strip()]
        all_complete = len(complete) == len(adapters) and len(successful) == len(adapters)
        agreement = all_complete and len({item.content_sha256 for item in complete}) == 1
        status = "AGREED_TEXT" if agreement else ("SAFE_HOLD" if not all_complete else "DIVERGENT")
    result = CrossModelResult(exchange_id, status, tuple(replies), agreement,
                              external_effects_enabled=False, human_authorization_required=True,
                              human_authorization_present=False, tool_execution_enabled=False)
    audit.append({"event_type": "cross_model_exchange", "exchange_id": exchange_id, "status": status,
        "prompt_sha256": sha256_text(prompt), "providers": [
            {"provider": r.provider, "model": r.model, "request_id": r.request_id, "status": r.status,
             "content_sha256": r.content_sha256, "latency_ms": r.latency_ms, "error": r.error,
             "tool_calls": [{"call_id": c.call_id, "name": c.name, "arguments_sha256": c.arguments_sha256,
                             "schema_valid": c.schema_valid, "validation_error": c.validation_error}
                            for c in r.tool_calls]} for r in replies],
        "agreement_meaning": "exact text equality only; not evidence of truth",
        "external_effects_enabled": False, "human_authorization_required": True,
        "human_authorization_present": False, "tool_execution_enabled": False})
    return result
