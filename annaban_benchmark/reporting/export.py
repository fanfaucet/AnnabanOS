import json
from pathlib import Path


def export_json(result: dict, path: str = "annaban_report.json") -> None:
    Path(path).write_text(json.dumps(result, indent=2), encoding="utf-8")
