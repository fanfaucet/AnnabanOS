# AnnabanAI / AetherOS Repository Guidance

Scope: entire repository.

- Preserve the advisory-only, sovereignty-preserving design: code must not issue binding operational commands or imply centralized authority.
- Keep protected datasets segmented by jurisdiction; interfaces should carry jurisdiction and visibility scope metadata.
- All recommendation-producing code must include rationale, confidence, affected constraints, projected tradeoffs, and audit metadata.
- Prefer deterministic, inspectable logic over opaque optimization.
- Tests should avoid live external APIs; use synthetic data and deterministic fixtures.
