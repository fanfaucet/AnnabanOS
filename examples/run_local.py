import asyncio

from annaban_benchmark.orchestrator import AnnabanOrchestrator


async def main():
    orchestrator = AnnabanOrchestrator()
    result = await orchestrator.run("Summarize logistics constraints for a port delay.")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
