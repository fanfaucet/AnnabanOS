#!/usr/bin/env python3
"""Run a live OpenAI/xAI exchange; model tool calls are proposals, never executed."""
import argparse
import json
import os
import sys
from pathlib import Path

from annaban_sdk.live_cross_model import (
    HashChainAudit, configured_adapters, cross_model_exchange,
)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", help="Prompt sent independently to both configured providers")
    parser.add_argument("--audit", default=os.getenv("ANNABAN_AUDIT_PATH", "var/cross_model_audit.jsonl"))
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--tools-json", help="Path to a JSON array of OpenAI-compatible function tool schemas")
    parser.add_argument("--tool-choice", choices=("auto", "none", "required"), default="auto")
    args = parser.parse_args()
    try:
        tools = None
        if args.tools_json:
            tools = json.loads(Path(args.tools_json).read_text(encoding="utf-8"))
            if not isinstance(tools, list):
                raise ValueError("--tools-json must contain a JSON array")
        adapters = configured_adapters(timeout=args.timeout)
        audit = HashChainAudit(Path(args.audit))
        result = cross_model_exchange(args.prompt, adapters=adapters, audit=audit,
                                      timeout=args.timeout + 5, tools=tools, tool_choice=args.tool_choice)
    except (ValueError, OSError, TimeoutError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "SAFE_HOLD", "error": str(exc),
                          "external_effects_enabled": False, "tool_execution_enabled": False}, indent=2))
        return 2
    print(json.dumps({
        "classification": "LIVE_PROVIDER_CALLS",
        "exchange_id": result.exchange_id,
        "status": result.status,
        "agreement": result.agreement,
        "agreement_meaning": result.agreement_meaning,
        "external_effects_enabled": result.external_effects_enabled,
        "human_authorization_required": result.human_authorization_required,
        "human_authorization_present": result.human_authorization_present,
        "tool_execution_enabled": result.tool_execution_enabled,
        "replies": [{
            "provider": r.provider, "model": r.model, "request_id": r.request_id,
            "status": r.status, "content": r.content, "content_sha256": r.content_sha256,
            "latency_ms": r.latency_ms, "error": r.error,
            "tool_calls": [{
                "call_id": c.call_id, "name": c.name, "arguments": c.arguments,
                "arguments_sha256": c.arguments_sha256, "schema_valid": c.schema_valid,
                "validation_error": c.validation_error, "executed": False,
            } for c in r.tool_calls],
        } for r in result.replies],
        "audit_path": str(Path(args.audit)),
        "audit_integrity": audit.verify(),
    }, indent=2, ensure_ascii=False))
    return 0 if result.status == "AGREED_TEXT" else 1

if __name__ == "__main__":
    sys.exit(main())
