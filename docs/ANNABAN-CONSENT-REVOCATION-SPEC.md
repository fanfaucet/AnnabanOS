# AnnabanOS Consent Revocation and Expiration

**Record ID:** `ANNABAN-CONSENT-REVOCATION-001`  
**Revision:** `0.1-draft`  
**Classification:** Proposed design; implementation status is limited to the reference evaluator and unit tests in this branch.

## Principle

A signature records a specific authorization event. It does not create permanent, unlimited permission. Authorization is constrained by purpose, identity, resources, operations, duration, and applicable law.

## Expiration and suspension triggers

| Trigger | Required response |
|---|---|
| Consent withdrawn | Deny covered future operations and transition the order to revoked. |
| Expiry reached | Deny execution and mark expired. |
| Relationship context changes for relationship-dependent processing | Suspend pending fresh, purpose-specific review. |
| Purpose completed | Close the work order; no silent reactivation. |
| Identity or signature validation fails | Deny and suspend for review. |
| Operation or resource falls outside scope | Deny the request. |
| Required audit service unavailable | Deny operations that require durable audit. |
| Independent authorization absent for sensitive third-party processing | Deny. |
| Terminal order presented again | Deny; require a new work order for any new authorization. |

A relationship change does not automatically invalidate unrelated lawful authorizations or justify destroying records subject to valid retention requirements. It suspends relationship-dependent processing pending review.

## Dual authorization

A requesting user's signature alone does not establish another person's consent. Sensitive third-party processing requires independently validated authorization where consent is the legal basis. A second credential is not, by itself, proof of voluntary consent or lawful authority.

## Transparency and retention

Audit records should minimally capture the work-order ID, purpose, authorization state, resource and operation, policy decision, reason code, and timestamps. Do not expose unrelated private information to another party. Revocation disables authorization and triggers deletion of data no longer needed, subject to defined legal and audit-retention obligations.

## Implementation

- `annaban_policy/consent.py`: reference evaluator.
- `tests/test_consent_revocation.py`: unit tests for valid scope, expiry, revocation, terminal states, contextual suspension, third-party authorization, identity failure, scope escalation, and audit outage.

Run from the repository root:

```bash
python -m unittest discover -s tests -v
```

## Limitations

This is not production identity verification, a durable revocation service, a legal determination, secure deletion, or operating-system enforcement. The evaluator returns a decision; the caller must enforce it before each protected operation. The tests cover specified cases only and do not prove the absence of all bypasses. Independent security review has not been established.
