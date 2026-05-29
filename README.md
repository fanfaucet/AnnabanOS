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
