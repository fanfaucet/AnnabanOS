"""Canonical evidence envelope used by local AnnabanOS subsystem outputs."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Literal
from uuid import uuid4

AuthorizationStatus = Literal["NOT_AUTHORIZED", "AUTHORIZED", "DENIED"]
HumanReviewStatus = Literal["REQUIRED", "NOT_REQUIRED", "COMPLETED"]


@dataclass(frozen=True)
class AnnabanEvidenceEnvelope:
    """Wrap a local result without promoting it into execution authority.

    The integrity hash establishes evidence integrity for this serialized
    envelope. It does not independently verify the payload or its provenance.
    """

    evidence_id: str
    source: str
    source_type: str
    provenance: str
    timestamp: str
    payload: dict[str, Any]
    integrity_hash: str
    interpretation_status: str
    authorization_status: AuthorizationStatus
    human_review_status: HumanReviewStatus

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation of the envelope."""

        return asdict(self)


def create_evidence_envelope(
    *,
    source: str,
    source_type: str,
    provenance: str,
    payload: dict[str, Any],
    interpretation_status: str,
    authorization_status: AuthorizationStatus = "NOT_AUTHORIZED",
    human_review_status: HumanReviewStatus = "REQUIRED",
    evidence_id: str | None = None,
    timestamp: str | None = None,
) -> AnnabanEvidenceEnvelope:
    """Create a tamper-evident, explicitly non-authorizing result envelope."""

    evidence_id = evidence_id or f"evidence-{uuid4()}"
    timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    material = {
        "evidence_id": evidence_id,
        "source": source,
        "source_type": source_type,
        "provenance": provenance,
        "timestamp": timestamp,
        "payload": payload,
        "interpretation_status": interpretation_status,
        "authorization_status": authorization_status,
        "human_review_status": human_review_status,
    }
    integrity_hash = f"sha256:{sha256(json.dumps(material, sort_keys=True, separators=(',', ':')).encode()).hexdigest()}"
    return AnnabanEvidenceEnvelope(integrity_hash=integrity_hash, **material)
