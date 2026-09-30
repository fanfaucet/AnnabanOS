# Simulation Negotiations

Simulation artifacts may be committed to Git when they are explicitly marked as simulations.

## Rules

- Every negotiation artifact must carry `simulation_only: true`.
- Simulated participants must be identified as simulated.
- Real participants must not be represented as having made statements they did not make.
- Simulation output is evidence for testing, not operational authority.
- Simulated negotiations cannot authorize, execute, or create external effects.
- No simulation artifact may contain production credentials, private keys, access tokens, or other secrets.
- Provenance must distinguish `claimed_origin` from `verified_origin`.
- A simulated agreement is not a cryptographic authorization.

Recommended structure:

```text
simulations/
  negotiations/
    <scenario>/
      negotiation.json
      transcript.md
      expected.json
```
