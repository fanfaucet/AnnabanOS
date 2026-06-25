from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from annaban_benchmark.harness import BenchmarkHarness


class BenchmarkRequest(BaseModel):
    dataset_path: str | None = Field(default=None, description="Optional local JSONL dataset path")


app = FastAPI(title="Annaban Benchmark API", version="0.1.0")


@app.post("/benchmark")
async def run_benchmark(request: BenchmarkRequest | None = None) -> dict[str, Any]:
    harness = BenchmarkHarness(dataset_path=request.dataset_path if request else None)
    return await harness.run_benchmark()
