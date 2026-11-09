#!/usr/bin/env python3
"""Run a live OpenAI/xAI exchange and print outputs with provenance."""
import argparse, json, os, sys
from pathlib import Path
from annaban_sdk.live_cross_model import HashChainAudit, configured_adapters, cross_model_exchange

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", help="Prompt sent independently to both configured providers")
    parser.add_argument("--audit", default=os.getenv("ANNABAN_AUDIT_PATH", "var/cross_model_audit.jsonl"))
    parser.add_argument("--timeout", type=float, default=45.0)
    args = parser.parse_args()
    try:
        adapters = configured_adapters(timeout=args.timeout)
        audit = HashChainAudit(Path(args.audit))
        result = cross_model_exchange(args.prompt, adapters=adapters, audit=audit, timeout=args.timeout + 5)
    except (ValueError, OSError, TimeoutError) as exc:
        print(json.dumps({"status": "SAFE_HOLD", "error": str(exc), "external_effects_enabled": False}, indent=2))
        return 2
    print(json.dumps({
        "classification": "LIVE_PROVIDER_CALLS", "exchange_id": result.exchange_id,
        "status": result.status, "agreement": result.agreement,
        "agreement_meaning": result.agreement_meaning,
        "external_effects_enabled": result.external_effects_enabled,
        "replies": [{"provider": r.provider, "model": r.model, "request_id": r.request_id,
            "status": r.status, "content": r.content, "content_sha256": r.content_sha256,
            "latency_ms": r.latency_ms, "error": r.error} for r in result.replies],
        "audit_path": str(Path(args.audit)), "audit_integrity": audit.verify(),
    }, indent=2, ensure_ascii=False))
    return 0 if result.status == "AGREED_TEXT" else 1

if __name__ == "__main__":
    sys.exit(main())
