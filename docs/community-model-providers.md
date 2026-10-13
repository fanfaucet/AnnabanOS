# Community model provider onboarding

AnnabanOS supports a prototype self-service registry for people who want to offer a model hosted at a public HTTPS endpoint implementing the OpenAI-compatible `POST /v1/chat/completions` API.

## Register a model

Run the API, then submit:

```bash
curl -X POST http://localhost:8000/providers/register \
  -H 'Content-Type: application/json' \
  -d '{
    "display_name": "My Community Model",
    "endpoint_url": "https://models.example.com",
    "model_name": "my-model-v1",
    "api_key": "YOUR_PROVIDER_API_KEY",
    "owner_token": "REPLACE_WITH_A_RANDOM_SECRET_AT_LEAST_32_CHARACTERS"
  }'
```

Generate a unique owner token with a cryptographically secure password manager or secret generator. Do not reuse an account password. The owner token is required to unregister the model. Provider API keys and owner tokens are never returned by the API.

List public provider metadata with `GET /providers`. Remove a provider with:

```bash
curl -X DELETE http://localhost:8000/providers/PROVIDER_ID \
  -H 'X-Provider-Owner-Token: YOUR_OWNER_TOKEN'
```

## Let a request use a community model

Community providers are **not automatically sent prompts**. A caller must explicitly opt in by including registered IDs in the existing `POST /stream/business` request:

```json
{
  "prompt": "Summarize this public document.",
  "provider_ids": ["PROVIDER_ID"]
}
```

Only send information to a provider when you have permission to share it with that provider. Provider endpoints may retain prompts under their own terms.

## Current prototype limitations

- Registry records and provider credentials are held in process memory and are lost on restart.
- The API uses an owner-generated secret rather than a full account/identity system. Use TLS and rate limiting at the deployment edge.
- Only public HTTPS endpoints on port 443 are accepted; local-only models need a separately secured, publicly reachable gateway.
- DNS is checked during registration and invocation, but production deployment still requires outbound network/egress controls to mitigate DNS rebinding and infrastructure-level SSRF.
- Responses are currently returned as one chunk, not token-by-token streaming.
- No payment, reputation, uptime guarantee, moderation process, or provider verification is implemented.
- Do not treat this prototype as production-ready until durable encrypted secret storage, account authentication, rate limiting, abuse reporting, provider health checks, and operational review are added.

The design is opt-in: registering a model does not grant it access to every user's prompts, and the registry does not imply that a provider is trusted or verified.
