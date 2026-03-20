import asyncio
from collections.abc import AsyncIterator
from contextlib import suppress
from typing import Any


async def _forward_stream(name: str, stream: AsyncIterator[str], queue: asyncio.Queue[dict[str, Any] | None]) -> None:
    try:
        async for chunk in stream:
            await queue.put({"agent": name, "text": chunk})
    finally:
        await queue.put(None)


async def stream_aggregate(agent_streams: dict[str, AsyncIterator[str]]) -> AsyncIterator[dict[str, Any]]:
    queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
    tasks = [asyncio.create_task(_forward_stream(name, stream, queue)) for name, stream in agent_streams.items()]

    completed = 0
    try:
        while completed < len(tasks):
            item = await queue.get()
            if item is None:
                completed += 1
                continue
            yield item
    finally:
        for task in tasks:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
