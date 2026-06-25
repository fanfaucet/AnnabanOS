from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATASETS_ROOT = Path(__file__).resolve().parents[2] / "datasets"
DEFAULT_DATASET = DATASETS_ROOT / "logistics_tasks.jsonl"


def discover_datasets(root: str | Path | None = None) -> list[Path]:
    dataset_root = Path(root) if root else DATASETS_ROOT
    if not dataset_root.exists():
        return []
    return sorted(dataset_root.glob("*.jsonl"))


def load_dataset(path: str | Path | None = None) -> list[dict[str, Any]]:
    dataset_path = Path(path) if path else DEFAULT_DATASET
    tasks: list[dict[str, Any]] = []
    with dataset_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            task = json.loads(stripped)
            task.setdefault("id", f"{dataset_path.stem}-{line_number}")
            task.setdefault("type", dataset_path.stem)
            tasks.append(task)
    return tasks
