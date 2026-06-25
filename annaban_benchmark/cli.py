from __future__ import annotations

import argparse
import asyncio
import json
from typing import Sequence

from annaban_benchmark.harness import BenchmarkHarness


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Annaban Benchmark Suite.")
    parser.add_argument("--dataset", help="Path to a JSONL dataset file", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = asyncio.run(BenchmarkHarness(dataset_path=args.dataset).run_benchmark())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
