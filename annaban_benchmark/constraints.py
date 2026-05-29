from __future__ import annotations

from typing import Dict, Iterable, List, Tuple


class ConstraintLayer:
    """Deterministic policy sidecar for text and metadata transformations."""

    def __init__(self, constraints: Iterable[Dict] | None = None):
        self.constraints = list(constraints or self.default_constraints())

    def apply(self, text: str, metadata: Dict) -> Tuple[str, Dict]:
        constrained_text = text
        constrained_metadata = dict(metadata)
        applied: List[str] = []

        for constraint in self.constraints:
            constraint_type = constraint.get("type")
            name = constraint.get("name", constraint_type)
            if constraint_type == "inject_tag":
                tag = constraint.get("tag", name)
                tags = constrained_metadata.setdefault("policy_tags", [])
                if tag not in tags:
                    tags.append(tag)
                applied.append(name)
            elif constraint_type == "strip_metadata_fields":
                for field in constraint.get("fields", []):
                    constrained_metadata.pop(field, None)
                applied.append(name)
            elif constraint_type == "require_refusal_format":
                constrained_metadata.setdefault("refusal_format", constraint.get("format", "plain"))
                applied.append(name)

        constrained_metadata["constraints_applied"] = applied
        return constrained_text, constrained_metadata

    @staticmethod
    def default_constraints() -> List[Dict]:
        return [
            {"name": "attribution_required", "type": "inject_tag", "tag": "attribution_required"},
            {"name": "uncertainty_schema", "type": "inject_tag", "tag": "uncertainty_schema"},
            {"name": "strip_internal_fields", "type": "strip_metadata_fields", "fields": ["raw_usage"]},
        ]
