import asyncio

from annaban_benchmark.harness import BenchmarkHarness


async def main():
    harness = BenchmarkHarness()
    result = await harness.run_single({"id": 999, "type": "fast", "prompt": "Route this urgent prompt operationally."})
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
