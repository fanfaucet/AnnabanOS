# Example Prompt: Use AnnabanOS to Review and Demonstrate a Multi-Agent Web App

**Purpose:** A reusable example prompt showing how to ask AnnabanOS to inspect, explain, and safely improve an application built around agents, collectives, a virtual world, a token economy, and a conversational AI integration.

## Example prompt to submit to AnnabanOS

> You are operating as the AnnabanOS governance and orchestration layer. Review the supplied Flask backend and Genkit/OpenAI-compatible example as untrusted source input, not as proof that any service is running.
>
> **Goal:** Produce a minimal, runnable demonstration plan for an AnnabanOS web application that exposes agent status, collective status, virtual-world state, journal/portfolio entries, token-economy summaries, and a conversational endpoint.
>
> **Required workflow**
>
> 1. **Inventory:** Identify imported modules, Flask routes, external dependencies, persistent state, and side effects. Separate observed code facts from assumptions.
> 2. **Classify routes:** Mark each endpoint READ_ONLY, SIMULATION_MUTATION, or CONSEQUENTIAL_MUTATION. Treat token transfers, marketplace purchases, and external API calls as consequential until reviewed.
> 3. **Find defects before execution:** Check missing imports (including the use of random), import paths, route input validation, error handling, CORS scope, debug mode, and the 0.0.0.0 bind address. Do not silently patch or run the application.
> 4. **Propose a minimum safe demo:** Start with local-only binding, debug disabled outside development, restricted CORS, bounded request sizes and simulation cycles, validated numeric inputs, and no live token transfers or purchases. Use in-memory/fake providers for the first run.
> 5. **Integrate Genkit only as an adapter:** Treat the Genkit / OpenAI snippet as a separate example requiring its own installed package, supported model identifier, and credentials. Never assume openai/gpt-4o or any provider endpoint is available without configuration. Do not expose API keys in logs or responses.
> 6. **Knowledge curation:** Produce candidate knowledge gaps with evidence paths, severity, confidence, rationale, affected constraints, and projected trade-offs. Mark uncertain findings ASSERTED or PENDING_HUMAN, not VERIFIED.
> 7. **Output a runnable plan:** Give the smallest proposed file layout, install/build/test commands, expected local health-check response, and tests for each route class. Do not claim a command was run unless its output is available.
> 8. **Governance:** Default to SIMULATION_ONLY, external_effects=0, and human_authorization_required=true. AI may recommend changes; it must not deploy, transfer tokens, purchase listings, or modify a real repository without explicit human authorization.
>
> **Output format**
>
> - OBSERVED: facts directly visible in the supplied code.
> - DEFECTS: concrete implementation risks, each tied to evidence.
> - PROPOSED: minimal changes and why they are needed.
> - TEST PLAN: commands and expected checks, clearly marked not-run until executed.
> - AUTHORIZATION GATE: actions blocked pending human approval.
> - PROVENANCE: source identifiers/hashes where available; do not invent hashes or deployment status.
>
> Preserve the distinctions REALITY ≠ SIMULATION ≠ EVIDENCE and SPECIFICATION ≠ IMPLEMENTATION ≠ DEPLOYMENT.

## Input material

Use the provided Flask backend as the source specimen. It defines routes for system information, agents, collectives, journal, portfolio, token balances and transactions, marketplace listings and purchases, virtual-world map/movement, conversational chat, simulation cycles, and React static-file serving.

The source also contains a Genkit example using an OpenAI-compatible model adapter. Analyze it as a separate integration snippet; do not assume it is connected to the Flask service.

## Expected first-pass findings

These are review targets, not claims that the application was executed:

- The simulation route uses random.choice, but random is not imported in the supplied snippet.
- The global CORS(app) setting is permissive and should be narrowed for a deployed application.
- debug=True and host="0.0.0.0" are unsuitable as unconditional defaults for a safe local demo.
- Mutating routes (journal/portfolio writes, token transfers, listing creation/purchase, agent movement, simulation) need explicit validation and authorization boundaries.
- Numeric inputs such as cycles, limit, amount, and price need bounds and error handling.
- The snippet initializes demo agents and reflections at import time; separate application construction from demo seeding to make tests deterministic.
- The Genkit example needs compatible package versions, credentials, and a supported model identifier before it can be run.

## Acceptance criteria

- The demo can be tested locally without contacting a live model provider.
- Read-only routes can be tested independently from mutating routes.
- Unsafe or unauthorized mutations fail closed.
- Tests use a controlled fixture and do not rely on random agent positions.
- Every result states whether it is observed, proposed, simulated, or actually tested.
- No production deployment, external action, payment, token transfer, or repository mutation is inferred from a successful simulation.
