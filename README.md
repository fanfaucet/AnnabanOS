# AnthropicAI MVP

Production-ready scaffold for an AnthropicAI MVP with FastAPI streaming endpoints, multi-LLM agent hooks, Heritage Stack business modules, and deployment-friendly structure for AetherOS.

## Structure

```text
anthropicai-mvp/
├─ api/
│  ├─ __init__.py
│  └─ stream_endpoints.py
├─ llm_agents/
│  ├─ __init__.py
│  ├─ anthropic_agent.py
│  ├─ base_agent.py
│  └─ openai_agent.py
├─ heritage/
│  └─ modules/
│     ├─ analyticsModule.js
│     ├─ archiveModule.js
│     └─ subscriptionModule.js
├─ aggregator.py
├─ main.py
└─ requirements.txt
```

## Features

- FastAPI app entrypoint wired to streaming routes.
- Async stream aggregator that merges responses from multiple LLM providers.
- OpenAI Responses API streaming support.
- Placeholder Anthropic agent for future extension.
- Heritage Stack JavaScript modules for analytics, quotas, and archive milestones.
- Environment-variable-driven provider configuration for immediate deployment hardening.

## Quickstart

1. Create and activate a Python virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Export provider credentials:

   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export ANTHROPIC_API_KEY="your-anthropic-key"  # optional
   ```

4. Run the API locally:

   ```bash
   uvicorn main:app --reload --port 8000
   ```

5. Open the local interface:

   ```bash
   open http://127.0.0.1:8000/
   ```

6. Test the SSE endpoint directly:

   ```bash
   curl -N -X POST http://127.0.0.1:8000/stream/business \
     -H 'Content-Type: application/json' \
     -d '{"prompt":"Summarize the AnthropicAI MVP status"}'
   ```

## Notes

- The `/stream/business` route emits Server-Sent Events (`text/event-stream`).
- If no provider keys are configured, the stream returns an SSE error payload instead of failing the request.
- The Anthropic agent currently returns placeholder content and should be swapped for the official SDK before production traffic.
