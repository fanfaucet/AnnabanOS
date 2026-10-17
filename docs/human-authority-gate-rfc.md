# RFC: AnnabanOS Human Authority Gate MVD v0.1

**Status:** Proposed implementation / minimum viable demonstration  
**Originator:** Jacob Wayne Kinnaird  
**Scope:** Local in-memory demonstration; not production security software

## Problem

AI systems can propose actions that affect state. A governance layer should keep a proposal distinct from authorization and should not change protected state while a proposal is pending.

## Protocol

1. An agent submits a unique proposal ID, actor label, allowlisted state key, and proposed value.
2. The gate records the proposal as pending. Pending proposals do not change state.
3. A human decision must identify a non-empty human label and explicitly approve or reject the proposal.
4. Approval applies the bounded key/value update. Rejection leaves state unchanged.
5. A second decision for the same proposal is denied.
6. Each event is recorded in a hash-linked sequence. Verification detects edits to the recorded event payloads.

## Event record

Each event contains a sequence number, UTC timestamp, event type, event-specific details, previous hash, and event hash. The first previous hash is 64 zeroes. The event hash is SHA-256 over canonical JSON fields excluding the event-hash field itself.

## Security and limitations

This MVD is intentionally small. The human_id field is an asserted label, not authentication. State and logs are in memory and are not durable across process restarts. Hash chaining can reveal edits when a trusted head hash is retained, but it does not by itself prevent rewriting the entire log. There is no identity provider, cryptographic signature, concurrency control, network API, persistence layer, or independent audit.

Do not connect this demonstration to physical devices, financial systems, production infrastructure, or other consequential systems.

## Acceptance tests

- A pending proposal does not change state.
- An approved allowlisted proposal changes state.
- A rejected proposal does not change state.
- A key outside the allowlist is denied.
- Missing human identity is denied.
- A proposal cannot receive a second decision.
- The event chain verifies before tampering and fails after an event payload is edited.

## Next steps

1. Add durable storage and transaction semantics.
2. Replace asserted human labels with authenticated identities and signed approvals.
3. Add concurrency and replay protections.
4. Define a versioned event schema and compatibility policy.
5. Commission independent security review before any deployment claim.
