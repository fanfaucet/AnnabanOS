import os
import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def api(tmp_path, monkeypatch):
    db = tmp_path / "test-events.sqlite3"
    monkeypatch.setenv("ANNABAN_INTERNAL_API_TOKEN", "test-token-please-rotate")
    monkeypatch.setenv("ANNABAN_EVENT_DB", str(db))
    import internal_api.app as module
    importlib.reload(module)
    with TestClient(module.app) as client:
        yield client
    if db.exists():
        db.unlink()


def auth():
    return {"Authorization": "Bearer test-token-please-rotate"}


def sample_event(record_id="test-event-001", **overrides):
    body = {
        "record_id": record_id,
        "event_type": "handshake",
        "sender_role": "Grok (simulated role)",
        "receiver_role": "Gemini (simulated role)",
        "payload": {"simulation_label": "INTERNAL_SIMULATION"},
        "simulation": True,
        "source_status": "synthetic",
        "acknowledgment_status": "ack_simulated",
        "actuation_authority": "NONE",
    }
    body.update(overrides)
    return body


def test_authentication_required(api):
    assert api.get("/internal/v1/health").status_code == 401
    assert api.get("/internal/v1/health", headers=auth()).status_code == 200


def test_append_read_and_chain_check(api):
    response = api.post("/internal/v1/events", headers=auth(), json=sample_event())
    assert response.status_code == 201, response.text
    event = response.json()
    assert event["record_id"] == "test-event-001"
    assert event["sequence"] == 1
    assert event["actuation_authority"] == "NONE"
    assert len(event["event_digest"]) == 64

    read = api.get("/internal/v1/events/test-event-001", headers=auth())
    assert read.status_code == 200
    assert read.json()["event_digest"] == event["event_digest"]

    listing = api.get("/internal/v1/events", headers=auth())
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    check = api.get("/internal/v1/audit/chain-check", headers=auth())
    assert check.status_code == 200
    assert check.json()["valid"] is True
    assert check.json()["event_count"] == 1


def test_duplicate_record_id_rejected(api):
    first = api.post("/internal/v1/events", headers=auth(), json=sample_event())
    second = api.post("/internal/v1/events", headers=auth(), json=sample_event())
    assert first.status_code == 201
    assert second.status_code == 409


def test_client_cannot_forge_previous_chain_head(api):
    response = api.post(
        "/internal/v1/events",
        headers=auth(),
        json=sample_event(previous_event_digest="not-the-current-head"),
    )
    assert response.status_code == 409


def test_unknown_fields_rejected(api):
    response = api.post(
        "/internal/v1/events",
        headers=auth(),
        json=sample_event(unexpected_admin_flag=True),
    )
    assert response.status_code == 422


def test_no_actuation_route(api):
    response = api.post("/internal/v1/actuate", headers=auth(), json={"command": "run"})
    assert response.status_code == 404


def test_chain_check_detects_database_tampering(api, tmp_path, monkeypatch):
    response = api.post("/internal/v1/events", headers=auth(), json=sample_event())
    assert response.status_code == 201

    import internal_api.app as module
    db_path = Path(os.environ["ANNABAN_EVENT_DB"])
    import sqlite3
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE events SET event_json = ? WHERE record_id = ?",
            ('{"event_type":"observation","sender_role":"tampered","receiver_role":"x","payload":{},"simulation":true,"source_status":"synthetic","acknowledgment_status":"none","previous_event_digest":null,"actuation_authority":"NONE","record_id":"test-event-001"}', "test-event-001"),
        )
        conn.commit()

    check = api.get("/internal/v1/audit/chain-check", headers=auth())
    assert check.status_code == 200
    assert check.json()["valid"] is False
    assert check.json()["first_invalid_sequence"] == 1
