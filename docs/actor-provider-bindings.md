# Role-stable actors and swappable providers

The thread contract distinguishes three concepts:

- **role**: the stable functional slot, such as `database-expert`
- **provider**: the concrete human, model, or service identity
- **DBA**: “doing business as,” a display label that can change without changing role routing

Input records freeze an `actor_snapshot` at creation. Later role-binding changes affect future resolution only; they do not rewrite the actor, provider ID, DBA label, or model metadata on existing records. Parent links are input IDs and are independent of provider binding.

## Register providers

```http
PUT /actor-providers/user_9f2a
Content-Type: application/json

{
  "provider_id": "user_9f2a",
  "kind": "human",
  "current_dba": "Alice Chen (DBA)",
  "active": true,
  "capabilities": ["database-review"]
}
```

Model example:

```http
PUT /actor-providers/openai:gpt-4o
Content-Type: application/json

{
  "provider_id": "openai:gpt-4o",
  "kind": "model",
  "current_dba": "OpenAI GPT-4o",
  "active": true,
  "capabilities": ["database-review", "incident-analysis"],
  "model_meta": {
    "context_window": 128000,
    "temperature": 0.2,
    "system_prompt_hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "model_version": "gpt-4o"
  }
}
```

The model metadata hash is a caller-supplied provenance value, not independently verified by this prototype. No secrets, prompts, or API keys belong in this catalog record.

## Bind a role to a provider

```http
PATCH /role-bindings/database-expert
Content-Type: application/json

{
  "provider_id": "openai:gpt-4o",
  "dba": "OpenAI GPT-4o (acting as DBA)"
}
```

Change the binding to `user_9f2a` or another registered provider to change the current slot occupant. Existing inputs remain untouched. The role binding is in-memory and the PATCH operation is not yet authenticated; place this behind trusted administrative authorization before deployment.

## Create an input with a frozen actor snapshot

```http
POST /inputs
Content-Type: application/json

{
  "content": "Replica lag detected. Recommend investigation before failover.",
  "actor": {
    "role": "database-expert",
    "provider": {
      "kind": "model",
      "id": "openai:gpt-4o",
      "model_meta": {
        "context_window": 128000,
        "temperature": 0.2,
        "system_prompt_hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "model_version": "gpt-4o"
      }
    },
    "dba": "OpenAI GPT-4o (acting as DBA)"
  },
  "context": {"severity": "high"},
  "parent_id": null
}
```

The returned record includes `input_id`, `version_id`, `parent_id`, `actor_snapshot`, `status`, and a canonical SHA-256 audit hash. The hash detects changes only if the stored record is protected; it is not a signature or external tamper-proof ledger. Records are in memory for this prototype.

## Important boundaries

- Routing policy should key off `actor_snapshot.role`, never the DBA label.
- Provider IDs are stable identifiers; re-registering an ID with a different provider kind is rejected.
- Provider bindings only change future resolution. They do not alter an existing thread's parent chain.
- This prototype does not execute provider inference as part of role binding. It models the contract and registry; dispatch integration is a separate step.
- The current registry is process-local, and the binding mutation endpoint requires authentication/authorization, durable storage, concurrency review, and audit logging before production use.
