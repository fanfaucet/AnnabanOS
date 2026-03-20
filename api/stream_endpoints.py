import json
import os
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from aggregator import stream_aggregate
from llm_agents.anthropic_agent import AnthropicAgent
from llm_agents.openai_agent import OpenAIAgent

router = APIRouter(prefix="/stream", tags=["streaming"])


def _build_agents() -> dict[str, object]:
    agents: dict[str, object] = {}

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        agents["openai"] = OpenAIAgent(name="openai", api_key=openai_api_key)

    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_api_key:
        agents["anthropic"] = AnthropicAgent(name="anthropic", api_key=anthropic_api_key)

    return agents


@router.post("/business")
async def stream_business_events(task: dict) -> StreamingResponse:
    prompt = task.get("prompt", "")
    agents = _build_agents()

    async def merged_stream() -> AsyncIterator[str]:
        if not agents:
            yield f"data: {json.dumps({'error': 'No LLM providers configured'})}\n\n"
            return

        agent_streams = {name: agent.stream_request(prompt) for name, agent in agents.items()}
        async for chunk in stream_aggregate(agent_streams):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(merged_stream(), media_type="text/event-stream")
