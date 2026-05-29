from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import AuditEvent


class AuditLogger:
    """Append-only, hash-chained logger for deterministic LLM execution events."""

    def __init__(self, path: str | None = None, event_version: str = "annaban.audit.v0.1"):
        self.path = Path(path) if path else None
        self.event_version = event_version
        self.events: List[AuditEvent] = []
        self._last_hash: Optional[str] = None
        if self.path and self.path.exists():
            self._load_existing_events()

    def record(self, event_type: str, payload: Dict[str, Any]) -> AuditEvent:
        sequence = len(self.events) + 1
        canonical = self._canonical_payload(event_type, sequence, payload, self._last_hash)
        event_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        event = AuditEvent(
            event_version=self.event_version,
            event_type=event_type,
            sequence=sequence,
            payload=payload,
            previous_hash=self._last_hash,
            event_hash=event_hash,
        )
        self.events.append(event)
        self._last_hash = event_hash
        if self.path:
            self._append_to_disk(event)
        return event

    @property
    def last_hash(self) -> Optional[str]:
        return self._last_hash

    def verify(self) -> bool:
        previous_hash: Optional[str] = None
        for event in self.events:
            canonical = self._canonical_payload(
                event.event_type,
                event.sequence,
                event.payload,
                previous_hash,
            )
            expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            if event.previous_hash != previous_hash or event.event_hash != expected:
                return False
            previous_hash = event.event_hash
        return True

    def _canonical_payload(
        self,
        event_type: str,
        sequence: int,
        payload: Dict[str, Any],
        previous_hash: Optional[str],
    ) -> str:
        return json.dumps(
            {
                "event_version": self.event_version,
                "event_type": event_type,
                "sequence": sequence,
                "payload": payload,
                "previous_hash": previous_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def _append_to_disk(self, event: AuditEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.__dict__, sort_keys=True) + "\n")

    def _load_existing_events(self) -> None:
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)
                event = AuditEvent(**raw)
                self.events.append(event)
                self._last_hash = event.event_hash
        if not self.verify():
            raise ValueError("Audit log hash chain verification failed")
