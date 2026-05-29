from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ModelSelection:
    """Operational model routing decision, not a truth or confidence judgment."""

    model: str
    reason: str
    fallback_chain: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class NormalizedOutput:
    """Schema wrapper that preserves the model answer verbatim."""

    answer: str
    uncertainty_tags: List[str]
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class AuditEvent:
    """Versioned event stored in the append-only audit chain."""

    event_version: str
    event_type: str
    sequence: int
    payload: Dict[str, Any]
    previous_hash: Optional[str]
    event_hash: str
