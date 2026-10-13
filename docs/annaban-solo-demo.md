# Annaban solo model-provider demonstration

**Developer attribution:** Jacob Wayne Kinnaird  
**Provider ID:** `annaban-demo`  
**Mode:** `SIMULATION_ONLY`

Annaban is available as a solo provider for demonstrating the Annaban advisory interface. It runs locally in the API process, requires no model API key, does not contact OpenAI, Anthropic, or community endpoints, and does not fan out to any other provider when selected.

## Try it

Start the API as usual, then send a server-sent-events request:

```bash
curl -N http://localhost:8000/stream/business \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "Evaluate the risks in this proposed change.",
    "provider_ids": ["annaban-demo"]
  }'
```

The stream identifies the agent as `annaban-demo`. Selecting it takes precedence over any configured external model API keys, so this is a solo demonstration rather than a multi-model comparison.

## What this demo is—and is not

- It is a deterministic, rules-based demonstration adapter, not a trained foundation model and not a claim that an LLM has been trained under the Annaban name.
- It returns a structured advisory template that includes the supplied request, options, trade-offs, uncertainty, and human review.
- It is advisory-only: no external effects, tool execution, approvals, or state mutation are enabled.
- It does not retrieve external facts or verify user claims.
- The developer attribution names Jacob Wayne Kinnaird; it does not conflate the developer's identity with the Annaban software/model.

For an actual generative model, the provider interface can later be connected to a model that the developer controls. That connection should be documented separately, including model provenance, data handling, and operational limits.
