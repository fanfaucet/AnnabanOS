# AnnabanOS policy gate prototype

**Status:** experimental reference implementation; not production-ready.

## What is included

- `annaban_policy/gate.py`: signed work-order data model, policy evaluator, in-memory audit sink, and mock-only tool adapter.
- `tests/test_gate.py`: adversarial unit tests for absent authorization, model self-authorization attempts, prompt injection, scope expansion, tampered signatures, expiry, ambiguity, replay, audit failure, and untrusted issuers.

## Run tests

From the repository root:

```bash
python -m unittest discover -s tests -v
```

The test adapter performs no network calls and touches no external resources.

## Security limits

This prototype uses HMAC with a local test secret. It does not provide production identity management, key custody, durable/atomic replay protection, process isolation, OS-level network restrictions, or transactional guarantees. The in-memory audit sink is not tamper-resistant. The implementation has not undergone independent security review. Passing unit tests demonstrate only the tested behaviors in this prototype; they do not prove the absence of all bypasses in a deployed system.
