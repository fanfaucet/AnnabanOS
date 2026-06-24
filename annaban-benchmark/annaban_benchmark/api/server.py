from fastapi import FastAPI
from pydantic import BaseModel
from annaban_benchmark.harness import BenchmarkHarness

app = FastAPI(title="Annaban Benchmark API")
harness = BenchmarkHarness()


class BenchmarkRequest(BaseModel):
    dataset: str | None = None


@app.post("/benchmark")
async def run_benchmark(req: BenchmarkRequest):
    return await harness.run_benchmark(req.dataset or "reasoning_tasks")
