# Jacob Wayne Kinnaird Business Integration

This repository now carries a single local business context for Jacob Wayne Kinnaird's AnnabanAI / SparkAI+ stack. The goal is to connect each runnable demonstrator back to the same product/business narrative without hard-coding private contact details or relying on external account state.

## Canonical profile

The Python profile lives in `annaban_business/profile.py` and identifies:

- Owner/operator: Jacob Wayne Kinnaird
- Organization: AnnabanAI
- Orchestration platform: SparkAI+
- Operating layer: AnnabanOS
- Profile version: `0.2.0`
- Provenance: `local-project-declaration`
- Verification status: `UNVERIFIED`
- Domains: AI governance middleware, agent orchestration, simulation systems, logistics intelligence, audit and safety tooling

These fields are local project metadata. They do not independently verify
ownership, corporate status, third-party affiliation, authorization, or any
external-system relationship.

## Evidence and authority boundary

The local maritime evaluator and TypeScript simulations wrap outputs in an
`AnnabanEvidenceEnvelope`. The envelope identifies source, provenance,
timestamp, interpretation status, integrity hash, authorization status, and
human-review status. An integrity hash demonstrates that a serialized local
record has not changed; it does not establish that the payload is true.

Telemetry and simulation output are not execution authority. Maritime policy
responses remain `NOT_AUTHORIZED` and require human review. IAFTP success
records transfer evidence only, while the fictional Spark simulation records an
explicit policy result before its safe haptic mapping.

Maritime route inputs are strict: undeclared route fields are rejected rather
than silently retained as opaque metadata. When an ecological-crossing signal is
missing, it stays `MISSING` and requires review. When `risk_score` is absent,
the evaluator records a named `DERIVED` calculation and its inputs instead of
equating route risk with weather risk implicitly.

## Connected modules

- `annaban_benchmark`: governance, routing, constraints, signals, and audit ledger.
- `annaban_maritime`: logistics demonstrator for ETA, route scoring, route generation, and alignment checks.
- `src/core/iaftp.ts`: planner/executor artifact-transfer emulation with business-tagged transfer evidence and ledger metadata.
- `src/core/sparkIntegration.ts`: fictional SparkAI+ safety simulation with business-tagged policy evidence, session output, and audit entries.

## API surface

The maritime API exposes the profile at:

```bash
curl http://127.0.0.1:8000/business/profile
```

Use this endpoint when integrating demos, dashboards, or deployment metadata so the business identity is sourced from code rather than duplicated in clients.
