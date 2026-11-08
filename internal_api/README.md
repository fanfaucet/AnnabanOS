# AnnabanOS Internal Event API

**Status:** implementation committed; runtime tests have not been executed by this repository action.  
**Classification:** internal service scaffold. No external model provider is called.

## Routes

Every route requires `Authorization: Bearer $ANNABAN_INTERNAL_API_TOKEN`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/internal/v1/health` | Authenticated service health |
| POST | `/internal/v1/events` | Append an event to the SQLite audit log |
| GET | `/internal/v1/events?limit=100` | List recent events (limit 1–500) |
| GET | `/internal/v1/events/{record_id}` | Read one event |
| GET | `/internal/v1/audit/chain-check` | Recompute and check event hash links |
| GET | `/internal/v1/openapi-boundary` | State the service's execution boundary |

There is deliberately no actuation route. Event records always report `actuation_authority: NONE`.

## Local run

Python 3.10+:

```bash
python -m venv .venv
. .venv/bin/activate
pip install 'fastapi>=0.115,<1.0' 'uvicorn[standard]>=0.30,<1.0'
export ANNABAN_INTERNAL_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ANNABAN_EVENT_DB="./annaban-events.sqlite3"
uvicorn internal_api.app:app --host 127.0.0.1 --port 8000
```

Keep the bind address at loopback for local development. For remote internal deployment, use TLS, private networking, secret management, access controls, backups, and operational monitoring. Do not expose this service publicly as-is.

## Example request

```bash
curl -sS http://127.0.0.1:8000/internal/v1/events \
  -H "Authorization: Bearer $ANNABAN_INTERNAL_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "record_id": "ANNABAN-MULTIMODEL-HANDSHAKE-001-H1",
    "event_type": "handshake",
    "sender_role": "Grok (simulated role)",
    "receiver_role": "Gemini (simulated role)",
    "payload": {
      "summary": "Receipt is distinct from agreement.",
      "simulation_label": "INTERNAL_SIMULATION"
    },
    "simulation": true,
    "source_status": "synthetic",
    "acknowledgment_status": "ack_simulated",
    "actuation_authority": "NONE"
  }'
```

Check the chain:

```bash
curl -sS http://127.0.0.1:8000/internal/v1/audit/chain-check \
  -H "Authorization: Bearer $ANNABAN_INTERNAL_API_TOKEN"
```

## Event integrity and limits

- Events are stored in SQLite with WAL and synchronous writes; this is not a write-once medium and does not prevent a privileged host administrator from rewriting the database.
- SHA-256 digests are computed from canonical JSON and chained to the previous event digest. A digest detects some changes relative to the stored chain but does not prove author identity, creation time, external origin, or factual truth.
- The chain-check route verifies the current database contents. For stronger tamper evidence, export signed checkpoints to an independently controlled system and test backup/restore and concurrent-writer behavior.
- The bearer token is a shared secret. Rotate it, keep it outside source control, and prefer an identity-aware gateway for production.
- This scaffold has not yet been covered by automated tests, load tests, or an independent security review. Do not represent it as production-ready.
- Synthetic Grok/Gemini/Claude dialogue remains simulated unless actual provider responses and independently checkable request/response receipts are captured.
