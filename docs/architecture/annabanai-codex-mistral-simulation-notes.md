# Code Notes: AnnabanAI Observing Annaban–Codex Work with a Simulated Mistral Peer

**Originator:** Jacob Wayne Kinnaird  
**Related implementation:** [AnnabanAI observation contract](./annabana-observing-codex.md), [Printful mock-up MVD](../integrations/printful-faucet-fan-mockup-mvd.md), [prototype client](../../mvd/printful_mockup_client.py)  
**Status:** Design and simulation notes only. No live AnnabanAI–Codex runtime bridge or Mistral API session is established by this document.

## Purpose

Cross-reference the implementation path in which Annaban is observed using AnnabanAI to coordinate a coding task with Codex. Add a simulated Mistral AI peer interaction to the code notes so the proposed multi-model review can be discussed and tested without implying that Mistral was actually contacted.

Annaban is the observed interaction/communication layer in this scenario; AnnabanAI supplies bounded coordination and governance; Codex is the coding agent whose actual actions must be confirmed through repository/tool evidence. The Mistral participant is a **simulation fixture**, not a live provider response.

## Example observation sequence

1. **Human request recorded:** Jacob Wayne Kinnaird requests a scoped code or documentation change.
2. **AnnabanAI frames the task:** It records the request summary, repository/branch scope, expected artifact, and the approval boundary.
3. **Codex interaction observed:** The observer records a Codex request and then separately records returned tool evidence, such as a file diff, test output, commit SHA, or pull request URL.
4. **Simulated Mistral review:** A deterministic fixture emits a clearly labeled hypothetical review with fields such as:
   - simulation_only: true
   - provider: Mistral (simulated)
   - review_role: independent design critique
   - claims_live_provider_contact: false
   - evidence_refs: empty unless actual repository evidence is attached by the caller
5. **AnnabanAI arbitration:** Compare the simulated review against the request, policy, and available evidence. Record disagreements and unresolved questions; do not treat model agreement as human approval.
6. **Human decision:** A consequential repository write, merge, publication, or commerce action requires its own correctly scoped authorization.
7. **Evidence-backed result:** Mark a code change as confirmed only when the Git provider returns a verifiable change reference. If evidence is missing, use RESULT_UNKNOWN rather than success.

## Suggested event record

Illustrative JSON record shape (not an implemented schema):

    {
      "interaction_id": "example-correlation-id",
      "observer": "AnnabanAI",
      "coordinator": "AnnabanAI",
      "observed_agent": "Codex",
      "peer_review": {
        "provider_label": "Mistral",
        "simulation_only": true,
        "claims_live_provider_contact": false,
        "result": "hypothetical critique"
      },
      "authorization_state": "pending",
      "observed_result": "unknown",
      "evidence_refs": [],
      "human_approval_required_for_write": true
    }

Do not populate the record with invented commit IDs, test results, approvals, or provider responses.

## Connection to the Printful MVD

The existing Printful prototype is a bounded example of a governed operation: it checks a supplied approval record against design/version/product/variant fields before making a task-creation request. Its operator-name check is not authentication, and the prototype does not provide the full observer, durable approval ledger, Codex bridge, or Mistral adapter described here.

The same boundary should apply across the code workflow:
- code suggestions and simulated peer reviews are advisory;
- repository writes require scoped authorization and provider confirmation;
- generated mock-ups require the mock-up approval scope;
- Shopify publication and paid orders remain separate actions requiring separate approval;
- simulation records must not be presented as live Mistral, Codex, or AnnabanAI runtime telemetry.

## Implementation follow-up

1. Define typed event models and a correlation ID shared by the observer and repository adapter.
2. Implement a deterministic Mistral simulation fixture with explicit provenance fields.
3. Keep simulation fixtures separate from live provider adapters and label all fixture output.
4. Test missing evidence, simulated/live provenance confusion, mismatched action scopes, tool failure, and confirmed repository changes.
5. Add real provider adapters only after authentication, secret handling, data-retention, and authorization controls are reviewed.

## Non-claims

These notes do not establish a deployed AnnabanAI observer, a live Codex connection, a Mistral API call, a completed code change, or independent validation. They describe a proposed observation and simulation contract.
