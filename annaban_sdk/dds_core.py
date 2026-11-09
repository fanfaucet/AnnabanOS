"""DDS-Core: reconcile candidate records without asserting truth."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping
import hashlib
import json


@dataclass(frozen=True)
class ReconciliationResult:
    status: str
    candidate_count: int
    agreement_ratio: float
    common_fields: Mapping[str, Any]
    differences: tuple[str, ...]
    external_effect: int = 0


class DDSCore:
    """Compare normalized candidate mappings; disagreement is held, not erased."""
    def reconcile(self, candidates: Iterable[Mapping[str, Any]]) -> ReconciliationResult:
        items = [dict(c) for c in candidates]
        if not items:
            return ReconciliationResult("SAFE_HOLD", 0, 0.0, {}, ("no_candidates",))
        encoded = [
            json.dumps(item, sort_keys=True, separators=(",", ":"), allow_nan=False)
            for item in items
        ]
        counts: dict[str, int] = {}
        for value in encoded:
            counts[value] = counts.get(value, 0) + 1
        most_common = max(counts, key=counts.get)
        ratio = counts[most_common] / len(encoded)
        # Only fields identical across every candidate are promoted to common_fields.
        keys = set(items[0])
        for item in items[1:]:
            keys.intersection_update(item.keys())
        common = {
            key: items[0][key] for key in sorted(keys)
            if all(item[key] == items[0][key] for item in items[1:])
        }
        differences = tuple(sorted({
            key for item in items for key in item
            if any(key not in other or other.get(key) != item.get(key) for other in items)
        }))
        status = "AGREED" if len(counts) == 1 else "SAFE_HOLD"
        return ReconciliationResult(status, len(items), ratio, common, differences, 0)
