from typing import Any

import pytest

from llm_agents.base_agent import BaseAgent
from llm_agents.openai_agent import OpenAIAgent


class DummyAgent(BaseAgent):
    provider = "test"

    def send_request(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        return {"text": prompt}

    async def stream_request(self, prompt: str, **kwargs: Any):
        yield prompt

    def estimate_cost(self, tokens: int) -> float:
        if tokens < 0:
            raise ValueError("tokens must be non-negative.")
        return float(tokens)


def test_base_agent_rejects_empty_credentials():
    with pytest.raises(ValueError):
        DummyAgent("test", "")


def test_base_agent_rejects_empty_name():
    with pytest.raises(ValueError):
        DummyAgent("   ", "key")


def test_base_agent_preserves_model():
    assert DummyAgent("test", "key", "test-model").model == "test-model"


def test_negative_token_estimate_is_rejected():
    with pytest.raises(ValueError):
        DummyAgent("test", "key").estimate_cost(-1)


def test_openai_adapter_uses_responses_interface():
    agent = OpenAIAgent("openai", "test-key", "test-model")

    class FakeResponse:
        id = "resp_test"
        output_text = "hello"

    class FakeResponses:
        def create(self, **kwargs):
            assert kwargs["model"] == "test-model"
            assert kwargs["input"] == "hello"
            assert kwargs["max_output_tokens"] == 32
            return FakeResponse()

    class FakeClient:
        responses = FakeResponses()

    agent.client = FakeClient()
    result = agent.send_request("hello", max_output_tokens=32)

    assert result == {
        "text": "hello",
        "response_id": "resp_test",
        "provider": "openai",
        "model": "test-model",
    }


def test_openai_cost_rejects_negative_tokens():
    with pytest.raises(ValueError):
        OpenAIAgent("openai", "test-key").estimate_cost(-1)
