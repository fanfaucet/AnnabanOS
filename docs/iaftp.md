# AFMOS Inter-Agent File Transfer Protocol (IAFTP)

IAFTP is a protocol-level emulation for moving code artifacts between cognitive roles in a local AnnabanOS workspace. It models a planner node producing an artifact, an event bus routing the packet, and an executor node validating and integrating the artifact.

IAFTP is intentionally local and deterministic. It does not perform real network transfer, cross-model memory sharing, or remote GitHub writes.

## Packet lifecycle

1. **Packet encoding** computes a SHA-256 integrity hash over the artifact payload.
2. **Transmission emulation** records event-bus routing, destination resolution, channel selection, and simulated latency.
3. **Executor reception** verifies payload integrity before writing the artifact to the configured artifact store.
4. **Ledger recording** appends a hash-chained `FILE_TRANSFER_COMPLETE` entry for replay and audit checks.

## Runnable demo

```bash
node src/core/iaftpDemo.ts
```

## Core modules

- `src/core/gitLedger.ts` implements a replay-safe hash-chained ledger.
- `src/core/iaftp.ts` implements packet encoding, event-bus emulation, artifact stores, and executor-node receipt handling.
- `tests/test_iaftp.mjs` covers successful transfer and integrity-failure behavior.
