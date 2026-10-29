import json
import os
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from aggregator import stream_aggregate
from llm_agents.openai_agent import OpenAIAgent

router = APIRouter(prefix="/stream", tags=["streaming"])


def _build_agents() -> dict[str, Any]:
    """Build only provider integrations that are implemented and configured."""
    agents: dict[str, Any] = {}
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        agents["openai"] = OpenAIAgent(name="openai", api_key=openai_api_key)
    # AnthropicAgent is currently a placeholder, so it must not be advertised
    # as a live provider merely because ANTHROPIC_API_KEY is present.
    return agents


@router.post("/business")
async def stream_business_events(task: dict[str, Any]) -> StreamingResponse | JSONResponse:
    prompt = task.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": "invalid_request",
                    "message": "A non-empty string 'prompt' is required",
                }
            },
        )

    agents = _build_agents()

    async def merged_stream() -> AsyncIterator[str]:
        if not agents:
            yield f"data: {json.dumps({'error': {'type': 'configuration_error', 'message': 'No supported LLM providers configured'}})}\n\n"
            return

        agent_streams = {
            name: agent.stream_request(prompt) for name, agent in agents.items()
        }
        async for chunk in stream_aggregate(agent_streams):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        merged_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
