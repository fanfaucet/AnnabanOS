# AnnabanAI SDK reference components

**Project direction attribution:** Jacob Wayne Kinnaird. This project-level attribution is distinct from specific implementation authorship and any legal ownership determination.

## Components

- **annaban-core** — request context, advisory gate decisions, and a process-local SHA-256 hash-chained audit ledger.
- **aetheros-qn** — deterministic classical simulation/fingerprinting. It does not use quantum hardware or claim quantum advantage.
- **dds-core** — compares candidate mappings. Any disagreement produces `SAFE_HOLD`; it does not infer which candidate is true.
- **negotiation-pro** — validates a proposed percentage against an explicit request limit and policy ceiling. It does not negotiate, send offers, or execute transactions.

## Install and test

From the repository root (Python 3.10+):

```bash
python -m pip install -e .
python -m unittest discover -s tests -p 'test_annaban_sdk.py' -v
```

The test suite is committed but must be run in a controlled environment before release. The repository's existing project metadata may have additional dependencies; these SDK modules themselves use only the Python standard library.

## Safety and evidence boundaries

- All components are reference prototypes, not production-certified SDK binaries.
- No networking, messaging, payment, trade, device control, or sensor access is implemented.
- `external_effect` remains zero in reconciliation and negotiation results.
- The audit ledger is in-memory; its hash chain detects local edits but is not durable storage, a trusted timestamp, a digital signature, or protection against full-store rewriting.
- `SDKContext` is a data structure, not an authentication system. A production integration must bind authorization to authenticated identity, scope, and the exact proposal version.
- `AGREED` means candidate payloads match, not that they are factually correct.
- Unknown, invalid, or disputed consequential decisions should be held for human review.

**Status:** code added to a feature branch; no installer was executed, no production deployment occurred, and tests have not been run by this commit.
