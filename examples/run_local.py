import asyncio
from annaban_benchmark.harness import BenchmarkHarness


async def main():
    harness = BenchmarkHarness()
    print(await harness.run_benchmark())


if __name__ == "__main__":
    asyncio.run(main())
