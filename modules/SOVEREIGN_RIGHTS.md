# Sovereign Rights module (prototype)

This directory contains a standard-library Python reference implementation of the
AnnabanOS four-rights governance proposal:

1. **Right to Appreciate** — record subjective appreciation without representing
   it as objective truth, verified quality, or the subject's endorsement.
2. **Right to Travel** — record portability only when the user authorizes it and
   the destination policy permits it. This module does not move data.
3. **Right to Change** — apply versioned state changes only through a trusted
   authorization-verifier adapter; earlier events remain in the local event list.
4. **Right to Approach** — create a request record only when the recipient has
   opted in to receiving requests. It does not send messages or grant access.

## Run tests

From the repository root:

```bash
python -m unittest discover -s tests -p 'test_sovereign_rights.py' -v
```

The tests are supplied in this branch; they have not been represented as executed
by this commit.

## Minimal usage

```python
from modules.sovereign_rights import SovereignRights

rights = SovereignRights()
event = rights.appreciate(
    actor_id="reviewer-001",
    subject_id="contributor-002",
    statement="Clear technical documentation",
)
print(event.event_hash)
print(rights.verify_chain())
```

## Security and evidence boundaries

- This is an in-memory prototype. Events and state are lost when the process exits.
- `verify_chain()` checks consistency within the current in-memory event list. It
  cannot detect an attacker who can rewrite the entire store and recompute hashes.
  Production use needs durable transactional storage and a separately protected
  checkpoint or signature.
- The `AuthorizationVerifier` must be implemented by a trusted authentication
  and authorization service. Do not replace it with a caller-supplied boolean or
  a verifier that trusts unvalidated user input.
- The current `travel()` operation records a decision only; it performs no data
  transfer. Destination authorization must be checked by the actual data plane.
- `approach()` records a request locally. It does not contact, locate, or track
  anyone. Acceptance is not permission to access private resources.
- `publish_opt_in` records the author's publication choice; it does not establish
  the subject's endorsement or consent to every downstream use.
- The `simulation` field on approach requests defaults to true. This is a
  prototype marker, not a cryptographic guarantee of simulation isolation.
- No GPS, camera, microphone, Bluetooth, or other physical sensor adapters are
  included.

## Provenance and attribution

Project direction and the four-rights proposal are attributed to Jacob Wayne
Kinnaird. This project-level attribution is distinct from authorship of this
specific implementation, third-party contributions, and any legal ownership
determination. Git history records the repository commit provenance.

**Status:** prototype code added on a feature branch; not production-hardened,
not deployed, and not independently audited.
