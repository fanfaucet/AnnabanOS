import asyncio
import unittest
from unittest.mock import patch

from fastapi.responses import JSONResponse, StreamingResponse

from aggregator import stream_aggregate
from api.stream_endpoints import stream_business_events


async def chunks(*items: str):
    for item in items:
        await asyncio.sleep(0)
        yield item


class StreamingAggregatorTests(unittest.IsolatedAsyncioTestCase):
    async def test_merges_concurrent_simulated_participants(self):
        # Scenario labels only: neither named person is represented as an actual participant.
        streams = {
            "scenario_molly_oshea": chunks("Molly scenario A", "Molly scenario B"),
            "scenario_alysa_liu": chunks("Alysa scenario A", "Alysa scenario B"),
        }

        events = [event async for event in stream_aggregate(streams)]

        self.assertCountEqual(
            [(event["agent"], event["text"]) for event in events],
            [
                ("scenario_molly_oshea", "Molly scenario A"),
                ("scenario_molly_oshea", "Molly scenario B"),
                ("scenario_alysa_liu", "Alysa scenario A"),
                ("scenario_alysa_liu", "Alysa scenario B"),
            ],
        )
        self.assertTrue(all("error" not in event for event in events))

    async def test_provider_failure_is_sanitized_and_other_stream_continues(self):
        async def broken():
            yield "partial output"
            raise RuntimeError("secret-token=must-not-leak")

        events = [
            event
            async for event in stream_aggregate(
                {"broken_provider": broken(), "healthy_provider": chunks("still works")}
            )
        ]

        errors = [event for event in events if "error" in event]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["error"]["type"], "provider_error")
        self.assertNotIn("secret-token", repr(errors[0]))
        self.assertIn(
            {"agent": "healthy_provider", "text": "still works"},
            events,
        )
        self.assertIn(
            {"agent": "broken_provider", "text": "partial output"},
            events,
        )

    async def test_closing_aggregate_cancels_and_closes_active_provider(self):
        started = asyncio.Event()
        closed = asyncio.Event()

        async def blocked():
            started.set()
            try:
                await asyncio.Event().wait()
                yield "unreachable"
            finally:
                closed.set()

        aggregate = stream_aggregate(
            {"blocked_provider": blocked(), "fast_provider": chunks("first")}
        )
        first = await anext(aggregate)
        self.assertEqual(first, {"agent": "fast_provider", "text": "first"})
        await asyncio.wait_for(started.wait(), timeout=1)
        await aggregate.aclose()
        self.assertTrue(closed.is_set())

    async def test_empty_provider_set_finishes_cleanly(self):
        self.assertEqual([item async for item in stream_aggregate({})], [])

    async def test_endpoint_rejects_missing_or_blank_prompt(self):
        for payload in ({}, {"prompt": ""}, {"prompt": "   "}, {"prompt": 123}):
            response = await stream_business_events(payload)
            self.assertIsInstance(response, JSONResponse)
            self.assertEqual(response.status_code, 422)

    async def test_endpoint_returns_sse_error_when_no_provider_is_configured(self):
        with patch("api.stream_endpoints._build_agents", return_value={}):
            response = await stream_business_events({"prompt": "simulated test"})
            self.assertIsInstance(response, StreamingResponse)
            self.assertEqual(response.media_type, "text/event-stream")
            body = "".join([chunk async for chunk in response.body_iterator])

        self.assertIn("configuration_error", body)
        self.assertTrue(body.endswith("\n\n"))


if __name__ == "__main__":
    unittest.main()
