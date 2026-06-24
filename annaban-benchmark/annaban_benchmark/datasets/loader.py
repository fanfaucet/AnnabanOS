from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable

DATASET_DIR = Path(__file__).resolve().parent


def load_dataset(name: str) -> list[dict]:
    path = DATASET_DIR / f"{name}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def available_datasets() -> Iterable[str]:
    for p in DATASET_DIR.glob("*.jsonl"):
        yield p.stem
