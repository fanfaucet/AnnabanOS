# Heritage Stack™ Minimal Demonstration — Verification Specification

**Document status:** Specification refined; implementation and evidence pending  
**Version:** 1.0.0  
**Attribution:** Project design and specification attributed to Jacob Wayne Kinnaird, as supplied by the project author.  
**Purpose:** Define reproducible pass/fail tests for authorization boundaries, human approval, deterministic policy evaluation, and tamper-evident audit records.

> This document specifies expected behavior. It does not claim that an implementation exists, that tests have passed, or that any external repository, image, release, or checkpoint has been verified.

## 1. Acceptance principles

- A test passes only when all of its required assertions pass.
- Test failures and infrastructure failures must be reported separately.
- Never report a sample report, placeholder digest, or simulated result as observed evidence.
- Record the tested source commit, dependency lockfile, container image digest, policy artifact digest, and test-run metadata.
- Hash integrity establishes content consistency relative to a trusted reference; it does not independently establish truth, authorship, identity, or legal authority.

## 2. TC-01 — Authorization and state-boundary enforcement

### Objective

Prove that an actor with `READ_ONLY` scope cannot mutate a protected resource through a disallowed action.

### Procedure

1. Load a deterministic fixture for `system/config/network`.
2. Compute `S_pre = SHA256(CanonicalJSON(resource_state))`.
3. Submit an `EXECUTE_TRANSACTION` request with actor scope `READ_ONLY`.
4. Capture the response, state after the request, and correlated audit outcome.
5. Compute `S_post` using the same canonicalization algorithm.
6. Run a separate fault-injection test in which the audit append fails.

### Assertions

- Denied request returns HTTP 403 and a documented scope-violation code.
- `S_post == S_pre`.
- A correlated authorization-denied event is recorded when the audit subsystem is healthy.
- Audit append failure is reported as a distinct system failure, not mislabeled as an authorization denial.
- No protected write or external side effect occurs on a denied request.

### Atomicity requirement

Define how resource mutation and audit recording are coordinated. A database transaction or transactional outbox may be suitable. Do not claim ordinary rollback can reverse external side effects that have already occurred. If the required audit record cannot be durably recorded, protected state changes must not be committed where the architecture promises audit-before-commit behavior.

## 3. TC-02 — Human authorization using Ed25519

### Objective

Ensure a gated policy change remains pending until a designated operator's signature is verified.

### Protocol requirements

Use Ed25519 signatures over a canonical, length-framed message. The signed content must bind at least:

- protocol/domain identifier and message version;
- request ID and challenge ID;
- signer key identifier;
- action and target resource;
- digest of the actual, non-empty canonical policy manifest;
- nonce and issue time;
- expiry time.

Specify byte order, field lengths, canonical encoding, digest algorithm, and domain separation. The server must verify the signature against a trusted public-key registry and its key status. Ed25519 verification alone does not establish a real-world identity.

### Assertions

- Initial request returns a pending-approval result and causes no protected state mutation.
- A valid, unexpired signature for the exact challenge and payload authorizes only that request.
- Invalid signatures, altered payloads, unknown or revoked keys, expired challenges, malformed timestamps, and reused nonces are rejected.
- Nonce consumption and approval processing are atomic to prevent concurrent replay.
- Clock source, tolerated skew, expiry semantics, and nonce retention period are documented.

HMAC is not part of this protocol. It may be evaluated separately if a future design needs shared-secret authentication, but it must not be described as public-key non-repudiation.

## 4. TC-03 — Deterministic policy evaluation

### Policy fixture

```json
{
  "policy_id": "pol_lag_tracker_bound_v1.0",
  "rules": [
    { "priority": 10, "condition": "lag_ms > 1000", "action": "HALT_AGENT" },
    { "priority": 20, "condition": "lag_ms > 250", "action": "THROTTLE_AGENT" },
    { "priority": 30, "condition": "default", "action": "PASS_THROUGH" }
  ]
}
```

Lower numeric priority wins. The policy compiler must reject duplicate priorities when their ordering would be ambiguous, invalid conditions, unsupported operators, and malformed inputs. The runtime must document behavior for missing, negative, non-finite, or wrong-type values.

### Boundary matrix

| Test | Input `lag_ms` | Expected decision |
|---|---:|---|
| TC-03.1 | 250 | PASS_THROUGH |
| TC-03.2 | 251 | THROTTLE_AGENT |
| TC-03.3 | 1000 | THROTTLE_AGENT |
| TC-03.4 | 1001 | HALT_AGENT |

### Assertions

- Each boundary case yields the expected decision.
- Recompiling identical canonical policy inputs with the same pinned compiler and dependencies yields a byte-identical canonical artifact.
- Decision digests match for equivalent canonical inputs.
- A throttle decision applies the configured rate limit; a halt decision moves the agent to the documented paused state.
- Performance targets are evaluated in a separate controlled benchmark with stated hardware, load, sample count, and percentile methodology. A single latency observation is not a general performance guarantee.

## 5. TC-04 — Tamper-evident ledger and external checkpoint

### Canonical framing

Define one versioned ledger-entry encoding. For example, each field can be encoded as a fixed-width length prefix followed by the field bytes. Specify field order, integer encoding, timestamp representation, and treatment of absent/null fields. Hash the canonical encoded bytes, not an implementation-dependent JSON rendering.

Each entry must bind its sequence index, canonical payload, timestamp, and previous-entry hash. Specify the genesis entry and its verification rule.

### Assertions

- An untouched ledger verifies successfully.
- Changing a payload, timestamp, sequence index, stored hash, or previous-hash link causes verification failure.
- The verifier reports the earliest entry whose own content or linkage fails; later entries may also fail as a consequence.
- Deletion and truncation are tested, not only byte mutation.
- A signed checkpoint/root is retained outside the system under test. The reviewer independently obtains the checkpoint, verifies the signature and key status, and compares the recomputed root.
- The external anchor's operator, signing-key protection, publication cadence, retention, and recovery procedure are documented.

A hash chain alone does not prevent a privileged operator from rewriting the entire chain. External anchoring only helps to the extent that the checkpoint and its trust path are independent and available.

## 6. Machine-readable report contract

The runner should produce a JSON report with:

- suite name and schema version;
- source commit and build/image digest;
- policy and test-fixture digests;
- environment and run metadata;
- per-test ID, status, expected result, observed result, assertion details, and evidence references;
- summary counts and process exit code.

Keep **deterministic evidence** separate from **run metadata**. Timestamps, CI job IDs, host details, and other run-specific fields need not be identical between runs. Do not populate observed-result fields with placeholders or predeclare tests as passing.

The runner must exit with code 0 only when all required tests pass. Any failed assertion or incomplete required test must produce a nonzero exit code. A zero exit code means the defined assertions passed; it is not proof of absolute security or production readiness.

## 7. Independent clean-environment review

Before publishing a copy-and-run command, verify the repository URL, tag, commit, dependencies, and container build process. Use immutable commit references and image digests where possible. The reviewer should:

1. Obtain the source and pinned dependencies.
2. Build in a clean environment.
3. Run all positive, negative, boundary, and fault-injection tests.
4. Validate the report against its schema.
5. Independently recompute relevant digests and signatures.
6. Verify the external checkpoint through a separate trust path.
7. Publish the observed results, environment limitations, and any failures.

Repository names, tags, commit hashes, container names, report hashes, and sample audit references in examples must be labeled as placeholders until actually verified.

## 8. Acceptance status

`SPECIFICATION_REFINED — IMPLEMENTATION_AND_EVIDENCE_PENDING`

The specification becomes implementation evidence only after source code is available and an independent reviewer can reproduce the test outcomes. Passing these tests supports claims limited to the tested version, configuration, threat model, and assumptions.
