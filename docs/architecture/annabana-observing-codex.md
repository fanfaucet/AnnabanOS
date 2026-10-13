# Cross-Reference: AnnabanA* Observing Annaban–Codex Interaction

**Owner / Lead Originator:** Jacob Wayne Kinnaird  
**Framework:** AnnabanOS / AnnabanAI / Heritage Stack™  
**Related work:** PR #12 Human Authority Gate MVD; PR #13 Faucet Fan × Printful mock-up integration MVD  
**Status:** Architecture cross-reference and observation contract; not evidence that a live AnnabanA*–Codex runtime connection is deployed.

## 1. Purpose

Describe how AnnabanA* may observe and record a coding session in which Annaban interacts with Codex, while preserving the distinction between observation, recommendation, authorization, and repository mutation.

AnnabanA* is treated here as an observation/orchestration layer in the proposed architecture. Codex is treated as a coding agent that can inspect or change code when explicitly given the relevant tool access. The integration must not infer that an action occurred merely because a prompt requested it; it should use verifiable tool results, repository events, diffs, test output, and commit identifiers.

## 2. Reference flow

```text
Jacob Wayne Kinnaird (human authority)
                |
                v
Annaban / AnnabanAI (request framing and bounded coordination)
                |
                v
AnnabanA* (observation, correlation, policy checks, audit events)
                |
                v
Codex (code analysis or proposed repository changes)
                |
                v
Tool / Git provider result (diff, checks, commit, PR state)
                |
                v
AnnabanA* observation record + AnnabanOS audit trail
                |
                v
Human review and explicit approval for consequential changes
```

The diagram is a proposed interaction model, not a claim that these components currently communicate through a live shared bus or API.

## 3. Observation contract

For each coding turn, capture only information needed to explain what happened:

- `interaction_id`: unique correlation identifier for the session or task.
- `request_summary`: concise, redacted summary of the human request.
- `agent_identity`: tool/agent name as actually reported by the integration.
- `requested_action`: read, propose, edit, test, commit, open PR, or merge.
- `authorization_state`: pending, approved, rejected, revoked, or not required for read-only inspection.
- `evidence_refs`: repository URL, branch, commit SHA, pull request, diff reference, or test run reference when available.
- `observed_result`: success, failure, partial result, or unknown, based on tool output rather than intention.
- `timestamp`: timestamp supplied by the trusted runtime.
- `integrity_fields`: previous-event hash and current-event hash if the configured audit store implements them.
- `redaction_notes`: indication of secrets or personal data omitted from the record.

Do not store API tokens, private keys, session cookies, or unrelated customer data. Prompts and model outputs should not be copied wholesale into durable logs by default; prefer summaries and explicit evidence references.

## 4. Action boundaries

| Action | Default handling |
|---|---|
| Read repository files or inspect a diff | May be observed and summarized under configured read permissions |
| Propose code or produce a patch | Mark as proposal until a repository tool confirms a change |
| Create/update a branch or commit | Require the configured repository authorization and record the returned SHA |
| Open or update a pull request | Record the confirmed PR URL, state, head SHA, and draft status |
| Merge a pull request | Separate, explicit human authorization; never infer permission from approval to create a draft PR |
| Change production configuration, publish products, or submit paid orders | Separate authorization scope and explicit approval; out of scope for this observer |
| Revoke or disable access | Must use the real provider's supported control surface; AnnabanA* cannot revoke permissions it does not control |

An approval is scoped to a specific action and payload. Approval to generate a Printful mock-up does not authorize a Shopify listing, paid order, Git merge, or unrelated code change.

## 5. Cross-reference to PR #13

PR #13 provides a practical example of a staged workflow:

1. Human-approved Faucet Fan design/product/variant details.
2. A bounded request to Printful's mock-up task API.
3. Task status retrieval and durable mock-up asset storage.
4. Human review of the generated preview.
5. A separate approval for any later Shopify publication.

AnnabanA* could observe this workflow by correlating approval IDs, task IDs, asset checksums, repository commits, and pull request status. It must not claim the Printful or Shopify steps occurred unless the corresponding provider response or audit evidence exists.

Repository cross-reference: https://github.com/fanfaucet/AnnabanOS/pull/13

## 6. Cross-reference to PR #12

The Human Authority Gate MVD in PR #12 is the policy boundary to integrate with. Its actual authentication, persistence, replay protection, and audit integrity must be inspected and tested before treating it as a production authority service. A string field containing an operator name is attribution metadata, not proof of authenticated identity.

Repository cross-reference: https://github.com/fanfaucet/AnnabanOS/pull/12

## 7. Suggested event sequence

```text
REQUEST_OBSERVED
  -> POLICY_EVALUATED
  -> HUMAN_APPROVAL_RECORDED (if required)
  -> CODEX_ACTION_REQUESTED
  -> TOOL_RESULT_OBSERVED
  -> DIFF_OR_TEST_EVIDENCE_CAPTURED
  -> HUMAN_REVIEW
  -> REPOSITORY_CHANGE_CONFIRMED (only if provider confirms)
```

Failure paths include `APPROVAL_DENIED`, `TOOL_FAILED`, `EVIDENCE_MISSING`, `RESULT_UNKNOWN`, and `ACTION_REVOKED`. Unknown outcomes must remain unknown rather than being rewritten as success.

## 8. Implementation plan

1. Define a typed event schema and a correlation ID shared across the AnnabanA* observer and repository adapter.
2. Add a read-only observer first: consume tool results and Git provider metadata without changing repositories.
3. Add policy evaluation that maps each requested action to a permission scope and approval requirement.
4. Record sanitized, append-oriented audit events with stable evidence references.
5. Add tests for missing approval, mismatched action scope, tool failure, duplicate events, missing evidence, and successful confirmed commits.
6. Enable repository writes only through explicit, separately scoped provider permissions.
7. Keep merge, release, commerce publication, and paid-order authority separate from code-generation approval.

## 9. Non-claims

This cross-reference does not establish that AnnabanA* is a deployed service, that Codex has been connected to AnnabanOS, that the audit log is immutable, or that any external vendor has endorsed the architecture. Those claims require implementation evidence and independent verification.
