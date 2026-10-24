# AnnabanAI Sidecar Simulation

A standard-library-only Python reference module for testing AnnabanAI's proposed
code-review governance sidecar. It models proposal intake, canonical JSON hashing,
diff-bound human approval, and an in-memory hash-linked audit ledger.

## Safety and scope

- `SIMULATION_ONLY`, `authority_level=0`, `external_effect=0`.
- No network calls, GitHub API calls, filesystem mutation, subprocesses, or code execution.
- An approval is bound to both a proposal ID and the exact diff SHA-256.
- Even a matching simulated approval returns `authorized=false`; it does not grant
  real repository-write or merge permission.
- The ledger is in-memory only. This module does not claim a persistent commit,
  signed identity, trusted timestamp, or tamper-proof storage.

## Run

Python 3.10+; no third-party dependencies:

```bash
python -m unittest discover -s tests -v
python annabanai_sidecar_sim.py
```

## Integration contract

Treat the module as an advisory/test adapter. Production integration must separately
authenticate source identity, protect keys and storage, enforce repository permissions,
and require a real human authorization gate immediately before any external effect.
Never interpret model confidence as authority.

## Record format

Each ledger event contains a sequence number, previous record hash, governance boundary
fields, and a SHA-256 hash of its canonical JSON representation. This detects accidental
or unsophisticated edits when the chain is checked against a trusted copy; it does not
prove who created the record or prevent an attacker from rewriting the entire chain.
