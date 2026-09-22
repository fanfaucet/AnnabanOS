# Jacob Wayne Kinnaird Business Integration

This repository now carries a single local business context for Jacob Wayne Kinnaird's AnnabanAI / SparkAI+ stack. The goal is to connect each runnable demonstrator back to the same product/business narrative without hard-coding private contact details or relying on external account state.

## Canonical profile

The Python profile lives in `annaban_business/profile.py` and identifies:

- Owner/operator: Jacob Wayne Kinnaird
- Organization: AnnabanAI
- Orchestration platform: SparkAI+
- Operating layer: AnnabanOS
- Domains: AI governance middleware, agent orchestration, simulation systems, logistics intelligence, audit and safety tooling

## Connected modules

- `annaban_benchmark`: governance, routing, constraints, signals, and audit ledger.
- `annaban_maritime`: logistics demonstrator for ETA, route scoring, route generation, and alignment checks.
- `src/core/iaftp.ts`: planner/executor artifact-transfer emulation with business-tagged ledger metadata.
- `src/core/sparkIntegration.ts`: fictional SparkAI+ safety simulation with business-tagged session output and audit entries.

## API surface

The maritime API exposes the profile at:

```bash
curl http://127.0.0.1:8000/business/profile
```

Use this endpoint when integrating demos, dashboards, or deployment metadata so the business identity is sourced from code rather than duplicated in clients.
