"""AnnabanOS internal event API.

Run:
    pip install fastapi uvicorn
    export ANNABAN_INTERNAL_API_TOKEN='generate-a-long-random-secret'
    export ANNABAN_EVENT_DB='./annaban-events.sqlite3'
    uvicorn internal_api.app:app --host 127.0.0.1 --port 8000

All routes require a bearer token. Bind to loopback or a private network and place
behind TLS/network controls before any remote use. This service records events only;
it does not call external model providers or authorize actuation.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

APP_VERSION = "0.1.0"
DB_PATH = os.getenv("ANNABAN_EVENT_DB", "./annaban-events.sqlite3")
TOKEN_ENV = "ANNABAN_INTERNAL_API_TOKEN"

app = FastAPI(
    title="AnnabanOS Internal Event API",
    version=APP_VERSION,
    description=(
        "Private, append-only event intake and audit-chain inspection. "
        "Simulation labels are data, not external verification."
    ),
)


class EventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: str = Field(default_factory=lambda: f"evt_{uuid4().hex}", min_length=1, max_length=128)
    event_type: Literal["handshake", "observation", "policy_decision", "provenance_note"]
    sender_role: str = Field(min_length=1, max_length=100)
    receiver_role: str = Field(min_length=1, max_length=100)
    payload: dict = Field(default_factory=dict)
    simulation: bool = True
    source_status: Literal["synthetic", "user_supplied", "external_receipt"] = "synthetic"
    acknowledgment_status: Literal["none", "received", "ack_simulated", "ack_external"] = "none"
    previous_event_digest: str | None = None
    actuation_authority: Literal["NONE"] = "NONE"


class EventOut(BaseModel):
    record_id: str
    sequence: int
    created_at: str
    event_type: str
    sender_role: str
    receiver_role: str
    payload: dict
    simulation: bool
    source_status: str
    acknowledgment_status: str
    previous_event_digest: str | None
    event_digest: str
    actuation_authority: Literal["NONE"] = "NONE"


class ChainCheck(BaseModel):
    valid: bool
    event_count: int
    checked_at: str
    first_invalid_sequence: int | None = None
    reason: str | None = None


def _connect() -> sqlite3.Connection:
    path = Path(DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            event_json TEXT NOT NULL,
            previous_event_digest TEXT,
            event_digest TEXT NOT NULL UNIQUE
        )
        """
    )
    return conn


def _canonical(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(event_without_digest: dict) -> str:
    return hashlib.sha256(_canonical(event_without_digest).encode("utf-8")).hexdigest()


def require_internal_token(authorization: str | None = Header(default=None)) -> None:
    expected = os.getenv(TOKEN_ENV)
    if not expected:
        raise HTTPException(status_code=503, detail="Internal API token is not configured")
    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")


@app.get("/internal/v1/health", dependencies=[Depends(require_internal_token)])
def health() -> dict:
    return {"status": "ok", "service": "annabanos-internal-api", "version": APP_VERSION}


@app.post(
    "/internal/v1/events",
    response_model=EventOut,
    status_code=201,
    dependencies=[Depends(require_internal_token)],
)
def append_event(event: EventIn) -> EventOut:
    conn = _connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        previous = conn.execute(
            "SELECT sequence, event_digest FROM events ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        previous_digest = previous["event_digest"] if previous else None
        if event.previous_event_digest is not None and event.previous_event_digest != previous_digest:
            conn.execute("ROLLBACK")
            raise HTTPException(status_code=409, detail="previous_event_digest does not match current chain head")

        created_at = datetime.now(timezone.utc).isoformat()
        body = event.model_dump(mode="json")
        body["previous_event_digest"] = previous_digest
        body["actuation_authority"] = "NONE"
        digest = _digest({"created_at": created_at, **body})
        try:
            cursor = conn.execute(
                """INSERT INTO events
                   (record_id, created_at, event_json, previous_event_digest, event_digest)
                   VALUES (?, ?, ?, ?, ?)""",
                (event.record_id, created_at, _canonical(body), previous_digest, digest),
            )
        except sqlite3.IntegrityError as exc:
            conn.execute("ROLLBACK")
            raise HTTPException(status_code=409, detail="record_id already exists") from exc
        sequence = int(cursor.lastrowid)
        conn.execute("COMMIT")
        return EventOut(
            record_id=event.record_id,
            sequence=sequence,
            created_at=created_at,
            event_type=event.event_type,
            sender_role=event.sender_role,
            receiver_role=event.receiver_role,
            payload=event.payload,
            simulation=event.simulation,
            source_status=event.source_status,
            acknowledgment_status=event.acknowledgment_status,
            previous_event_digest=previous_digest,
            event_digest=digest,
            actuation_authority="NONE",
        )
    finally:
        conn.close()


@app.get(
    "/internal/v1/events",
    response_model=list[EventOut],
    dependencies=[Depends(require_internal_token)],
)
def list_events(limit: int = Query(default=100, ge=1, le=500), before_sequence: int | None = Query(default=None, ge=1)) -> list[EventOut]:
    conn = _connect()
    try:
        if before_sequence is None:
            rows = conn.execute(
                "SELECT * FROM events ORDER BY sequence DESC LIMIT ?", (limit,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM events WHERE sequence < ? ORDER BY sequence DESC LIMIT ?",
                (before_sequence, limit),
            ).fetchall()
        result = []
        for row in reversed(rows):
            body = json.loads(row["event_json"])
            result.append(EventOut(
                record_id=row["record_id"],
                sequence=row["sequence"],
                created_at=row["created_at"],
                event_type=body["event_type"],
                sender_role=body["sender_role"],
                receiver_role=body["receiver_role"],
                payload=body["payload"],
                simulation=body["simulation"],
                source_status=body["source_status"],
                acknowledgment_status=body["acknowledgment_status"],
                previous_event_digest=row["previous_event_digest"],
                event_digest=row["event_digest"],
                actuation_authority="NONE",
            ))
        return result
    finally:
        conn.close()


@app.get(
    "/internal/v1/events/{record_id}",
    response_model=EventOut,
    dependencies=[Depends(require_internal_token)],
)
def get_event(record_id: str) -> EventOut:
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM events WHERE record_id = ?", (record_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Event not found")
        body = json.loads(row["event_json"])
        return EventOut(
            record_id=row["record_id"],
            sequence=row["sequence"],
            created_at=row["created_at"],
            event_type=body["event_type"],
            sender_role=body["sender_role"],
            receiver_role=body["receiver_role"],
            payload=body["payload"],
            simulation=body["simulation"],
            source_status=body["source_status"],
            acknowledgment_status=body["acknowledgment_status"],
            previous_event_digest=row["previous_event_digest"],
            event_digest=row["event_digest"],
            actuation_authority="NONE",
        )
    finally:
        conn.close()


@app.get(
    "/internal/v1/audit/chain-check",
    response_model=ChainCheck,
    dependencies=[Depends(require_internal_token)],
)
def check_chain() -> ChainCheck:
    conn = _connect()
    checked_at = datetime.now(timezone.utc).isoformat()
    try:
        rows = conn.execute("SELECT * FROM events ORDER BY sequence ASC").fetchall()
        previous_digest = None
        for expected_sequence, row in enumerate(rows, start=1):
            body = json.loads(row["event_json"])
            if row["sequence"] != expected_sequence:
                return ChainCheck(valid=False, event_count=len(rows), checked_at=checked_at,
                                  first_invalid_sequence=expected_sequence, reason="sequence_gap_or_reordering")
            if row["previous_event_digest"] != previous_digest or body.get("previous_event_digest") != previous_digest:
                return ChainCheck(valid=False, event_count=len(rows), checked_at=checked_at,
                                  first_invalid_sequence=expected_sequence, reason="previous_digest_mismatch")
            expected_digest = _digest({"created_at": row["created_at"], **body})
            if not hmac.compare_digest(expected_digest, row["event_digest"]):
                return ChainCheck(valid=False, event_count=len(rows), checked_at=checked_at,
                                  first_invalid_sequence=expected_sequence, reason="event_digest_mismatch")
            previous_digest = row["event_digest"]
        return ChainCheck(valid=True, event_count=len(rows), checked_at=checked_at)
    finally:
        conn.close()


@app.get("/internal/v1/openapi-boundary", dependencies=[Depends(require_internal_token)])
def api_boundary() -> dict:
    return {
        "service": "AnnabanOS Internal Event API",
        "scope": "event intake, readback, and hash-chain integrity inspection",
        "external_model_calls": False,
        "actuation_endpoints": False,
        "human_authorization_required_for_external_mutations": True,
        "hashes_prove_integrity_only_not_identity_or_truth": True,
    }
