"""AnnabanAI governance sidecar simulation.

Deterministic, read-only reference implementation. This module records and
evaluates proposed actions; it never executes repository or external actions.
Python 3.10+, standard library only.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Iterable

MODE = "SIMULATION_ONLY"
AUTHORITY_LEVEL = 0
EXTERNAL_EFFECT = 0


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize JSON-compatible data deterministically for hashing."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_hex(value: Any) -> str:
    """Return SHA-256 of canonical JSON bytes (not a signature)."""
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    summary: str
    diff_sha256: str
    source: str = "synthetic-fixture"
    jurisdiction: str = "unspecified"
    visibility: str = "internal"
    confidence: float = 0.5
    rationale: str = "No rationale supplied."
    affected_constraints: tuple[str, ...] = ()
    projected_tradeoffs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.proposal_id.strip():
            raise ValueError("proposal_id must not be empty")
        if len(self.diff_sha256) != 64 or any(
            char not in "0123456789abcdef" for char in self.diff_sha256
        ):
            raise ValueError("diff_sha256 must be a lowercase 64-character SHA-256 hex digest")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class HumanApproval:
    actor: str
    proposal_id: str
    approved_diff_sha256: str
    decision: str
    timestamp_utc: str

    @classmethod
    def create(cls, actor: str, proposal: Proposal, decision: str) -> "HumanApproval":
        if not actor.strip():
            raise ValueError("human actor must not be empty")
        if decision not in {"approve", "reject"}:
            raise ValueError("decision must be 'approve' or 'reject'")
        return cls(
            actor=actor,
            proposal_id=proposal.proposal_id,
            approved_diff_sha256=proposal.diff_sha256,
            decision=decision,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )


@dataclass(frozen=True)
class Evaluation:
    status: str
    authorized: bool
    mode: str = MODE
    authority_level: int = AUTHORITY_LEVEL
    external_effect: int = EXTERNAL_EFFECT
    rationale: str = ""
    proposal_id: str = ""
    diff_sha256: str = ""
    audit_metadata: dict[str, Any] | None = None


def evaluate_proposal(
    proposal: Proposal, approval: HumanApproval | None = None
) -> Evaluation:
    """Evaluate an approval record; never runs or applies the proposed diff."""
    metadata = {
        "source": proposal.source,
        "jurisdiction": proposal.jurisdiction,
        "visibility": proposal.visibility,
        "confidence": proposal.confidence,
        "affected_constraints": list(proposal.affected_constraints),
        "projected_tradeoffs": list(proposal.projected_tradeoffs),
    }
    if approval is None:
        return Evaluation(
            status="PENDING_HUMAN",
            authorized=False,
            rationale="No human approval record supplied; proposal remains advisory.",
            proposal_id=proposal.proposal_id,
            diff_sha256=proposal.diff_sha256,
            audit_metadata=metadata,
        )
    if approval.proposal_id != proposal.proposal_id:
        status, reason = "REJECTED_APPROVAL_BINDING", "Approval references a different proposal."
    elif approval.approved_diff_sha256 != proposal.diff_sha256:
        status, reason = "REJECTED_DIFF_MISMATCH", "Approval does not match the exact proposed diff hash."
    elif approval.decision != "approve":
        status, reason = "HUMAN_REJECTED", "Human reviewer rejected the proposal."
    else:
        status, reason = "SIMULATION_APPROVED", "Human approval matches this proposal and diff; no action was executed."
    return Evaluation(
        status=status,
        authorized=False,  # Simulation approvals never authorize real execution.
        rationale=reason,
        proposal_id=proposal.proposal_id,
        diff_sha256=proposal.diff_sha256,
        audit_metadata=metadata,
    )


class AppendOnlyAuditLedger:
    """In-memory hash-linked audit ledger; persistence is caller-owned."""

    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []

    @property
    def records(self) -> tuple[dict[str, Any], ...]:
        return tuple(dict(record) for record in self._records)

    def append(self, event: dict[str, Any]) -> dict[str, Any]:
        record = dict(event)
        record.setdefault("mode", MODE)
        record.setdefault("authority_level", AUTHORITY_LEVEL)
        record.setdefault("external_effect", EXTERNAL_EFFECT)
        record["sequence"] = len(self._records)
        record["previous_hash"] = self._records[-1]["record_hash"] if self._records else None
        record["record_hash"] = sha256_hex(record)
        self._records.append(record)
        return dict(record)

    @staticmethod
    def verify(records: Iterable[dict[str, Any]]) -> tuple[bool, str]:
        expected_previous = None
        for index, supplied in enumerate(records):
            record = dict(supplied)
            claimed_hash = record.pop("record_hash", None)
            if record.get("sequence") != index:
                return False, f"sequence mismatch at record {index}"
            if record.get("previous_hash") != expected_previous:
                return False, f"previous_hash mismatch at record {index}"
            if claimed_hash != sha256_hex(record):
                return False, f"record_hash mismatch at record {index}"
            if record.get("mode") != MODE or record.get("authority_level") != 0 or record.get("external_effect") != 0:
                return False, f"governance boundary mismatch at record {index}"
            expected_previous = claimed_hash
        return True, "chain verified"


def run_demo() -> dict[str, Any]:
    """Run deterministic synthetic example; no repository or network access."""
    synthetic_diff = "synthetic example: rename variable and add docstring\n"
    diff_hash = hashlib.sha256(synthetic_diff.encode("utf-8")).hexdigest()
    proposal = Proposal(
        proposal_id="SIM-PR-043",
        summary="Synthetic code-quality refactor",
        diff_sha256=diff_hash,
        source="synthetic-fixture",
        jurisdiction="US-TX",
        visibility="internal",
        confidence=0.94,
        rationale="Demonstrates review and provenance handling only.",
        affected_constraints=("read-only", "human-review-required"),
        projected_tradeoffs=("improved-readability", "no-runtime-change-claimed"),
    )
    ledger = AppendOnlyAuditLedger()
    evaluation = evaluate_proposal(proposal)
    ledger.append({"event": "PROPOSAL_RECEIVED", "proposal": asdict(proposal)})
    ledger.append({"event": "EVALUATION", "evaluation": asdict(evaluation)})
    verified, verification_message = ledger.verify(ledger.records)
    return {
        "module": "AnnabanAI Sidecar Simulation",
        "mode": MODE,
        "authority_level": AUTHORITY_LEVEL,
        "external_effect": EXTERNAL_EFFECT,
        "evaluation_status": evaluation.status,
        "authorized": evaluation.authorized,
        "ledger_records": len(ledger.records),
        "ledger_verified": verified,
        "ledger_message": verification_message,
        "proposal_diff_sha256": diff_hash,
        "note": "Synthetic demonstration only; no repository was inspected or modified.",
    }


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2, sort_keys=True))
