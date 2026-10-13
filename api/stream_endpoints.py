import json
import os
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from aggregator import stream_aggregate
from llm_agents.anthropic_agent import AnthropicAgent
from llm_agents.community_provider_agent import CommunityProviderAgent
from llm_agents.openai_agent import OpenAIAgent
from model_providers.registry import community_provider_registry

router = APIRouter(prefix="/stream", tags=["streaming"])


def _build_agents(provider_ids: list[str] | None = None) -> dict[str, object]:
    agents: dict[str, object] = {}

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        agents["openai"] = OpenAIAgent(name="openai", api_key=openai_api_key)

    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_api_key:
        agents["anthropic"] = AnthropicAgent(name="anthropic", api_key=anthropic_api_key)

    # Community endpoints receive prompts only when the caller explicitly opts in.
    for provider_id in dict.fromkeys(provider_ids or []):
        provider = community_provider_registry.get(provider_id)
        if provider is not None:
            agents[f"community:{provider.provider_id}"] = CommunityProviderAgent(
                provider_id=provider.provider_id,
                display_name=provider.display_name,
            )
    return agents


@router.post("/business")
async def stream_business_events(task: dict) -> StreamingResponse:
    prompt = task.get("prompt", "")
    requested_ids = task.get("provider_ids", [])
    if not isinstance(requested_ids, list) or not all(isinstance(item, str) for item in requested_ids):
        requested_ids = []
    agents = _build_agents(requested_ids)

    async def merged_stream() -> AsyncIterator[str]:
        if not agents:
            yield f"data: {json.dumps({'error': 'No LLM providers configured or selected'})}\n\n"
            return

        agent_streams = {name: agent.stream_request(prompt) for name, agent in agents.items()}
        async for chunk in stream_aggregate(agent_streams):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(merged_stream(), media_type="text/event-stream")
