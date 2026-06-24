from __future__ import annotations
import asyncio
import json
from annaban_benchmark.harness import BenchmarkHarness


def main() -> None:
    result = asyncio.run(BenchmarkHarness().run_benchmark())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
