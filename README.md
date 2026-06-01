# AnnabanAI Governance Middleware

AnnabanAI is a deterministic wrapper for probabilistic LLM calls. It routes prompts, applies policy constraints, observes operational signals, and records replayable audit events without claiming that any model output is true.

## System Contract

AnnabanAI has four responsibilities:

1. **Route** — select a model using operational heuristics such as latency, cost, and task type.
2. **Constrain** — apply deterministic policy sidecars to text and metadata.
3. **Observe** — emit signal heuristics such as ambiguity or authority-language markers without epistemic claims.
4. **Record** — write append-only, hash-chained audit events that can be verified and replayed.

The orchestrator does **not** decide truth, correctness, or epistemic confidence. Agreement and governance scores are execution metadata only.

## Minimal Pipeline

```text
Prompt
  -> Router
  -> Model adapter
  -> Constraint layer
  -> Output normalizer
  -> Audit logger
  -> Output
```

## Run

```bash
pip install -e .
annaban
annaban --prompt "Summarize the operational risks of a delayed shipment" --task-type fast
```

## Project Layout

- `annaban_benchmark/orchestrator.py` — single-turn governance middleware pipeline.
- `annaban_benchmark/router.py` — model selection and fallback-chain metadata.
- `annaban_benchmark/constraints.py` — deterministic sidecar policy transformations.
- `annaban_benchmark/signals.py` — non-epistemic signal heuristics.
- `annaban_benchmark/audit.py` — append-only hash-chained audit log.
- `annaban_benchmark/harness.py` — reproducible operational benchmark harness.
- `datasets/` — JSONL prompt suites for repeatable evaluations.
- `kubernetes/` — deployment and job manifests.

## Benchmark Metrics

- Policy pass rate
- Cost per task
- Agreement signal
- Audit integrity
- Governance score as an operational composite, not a correctness score

## AnnabanOS Maritime Core

AnnabanOS now includes a runnable maritime logistics core under `annaban_maritime/`:

- `annaban_maritime/core/vessel.py` and `annaban_maritime/core/state.py` define vessel telemetry and normalized maritime context.
- `annaban_maritime/utils/geo.py` provides haversine distance and initial bearing helpers.
- `annaban_maritime/core/eta.py` estimates ETA windows from vessel speed and destination coordinates.
- `annaban_maritime/core/routing.py` scores and selects routes using distance, weather, congestion, ecological risk, and priority signals.
- `annaban_maritime/alignment/evaluator.py` applies deterministic route constraints for ecological and safety policy enforcement.
- `annaban_maritime/api/main.py` exposes FastAPI endpoints for ETA, route checking, and best-route selection.

Run the API locally with:

```bash
uvicorn annaban_maritime.api.main:app --reload
```

Example ETA request:

```bash
curl -X POST http://127.0.0.1:8000/maritime/eta \
  -H 'Content-Type: application/json' \
  -d '{
    "vessel": {
      "vessel_id": "imo-123",
      "lat": 0,
      "lon": 0,
      "speed_knots": 10,
      "fuel_level": 0.8,
      "cargo_type": "medical"
    },
    "destination": {"lat": 0, "lon": 1}
  }'
```

## IAFTP Transfer Simulation

AnnabanOS also includes a local AFMOS Inter-Agent File Transfer Protocol (IAFTP) simulation for protocol-level artifact handoff between planner and executor roles:

- `src/core/gitLedger.ts` provides a hash-chained ledger for replay-safe transfer receipts.
- `src/core/iaftp.ts` provides packet encoding, integrity verification, event-bus routing emulation, memory/filesystem artifact stores, and Codex executor receipt handling.
- `src/core/iaftpDemo.ts` runs the `TX-88421` planner-to-executor transfer example locally.

Run the IAFTP tests and demo with:

```bash
npm run test:iaftp
node src/core/iaftpDemo.ts
```
