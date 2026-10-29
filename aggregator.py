import asyncio
from collections.abc import AsyncIterator
from contextlib import suppress
from typing import Any


async def _forward_stream(
    name: str,
    stream: AsyncIterator[str],
    queue: asyncio.Queue[dict[str, Any] | None],
) -> None:
    try:
        async for chunk in stream:
            await queue.put({"agent": name, "text": chunk})
    except asyncio.CancelledError:
        raise
    except Exception:
        # Do not forward raw provider exceptions: they can contain prompts,
        # credentials, or other sensitive request details.
        await queue.put(
            {
                "agent": name,
                "error": {
                    "type": "provider_error",
                    "message": "Provider stream failed",
                },
            }
        )
    finally:
        with suppress(Exception):
            await stream.aclose()
        # The queue is unbounded, so completion signaling cannot block here.
        await queue.put(None)


async def stream_aggregate(
    agent_streams: dict[str, AsyncIterator[str]],
) -> AsyncIterator[dict[str, Any]]:
    """Merge provider streams while isolating provider failures.

    Each provider emits text events, or one sanitized error event on failure.
    Cancelling/closing this generator cancels outstanding provider tasks.
    """
    if not agent_streams:
        return

    queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
    tasks = [
        asyncio.create_task(_forward_stream(name, stream, queue))
        for name, stream in agent_streams.items()
    ]
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
            if not task.done():
                task.cancel()
        for task in tasks:
            with suppress(asyncio.CancelledError):
                await task
