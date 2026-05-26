from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


DEFAULT_DATASET = Path(__file__).resolve().parent.parent / "datasets" / "logistics_tasks.jsonl"


def load_dataset(path: str | None = None) -> List[Dict]:
    dataset_path = Path(path) if path else DEFAULT_DATASET
    tasks: List[Dict] = []
    with dataset_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))
    return tasks
