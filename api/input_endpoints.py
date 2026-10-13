"""Input thread endpoint that freezes actor identity at write time."""
from __future__ import annotations

import hashlib
import json
from threading import RLock
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from model_providers.actor_schemas import InputCreate, InputRecord

router = APIRouter(prefix="/inputs", tags=["thread-inputs"])
_records: dict[str, InputRecord] = {}
_lock = RLock()


def _canonical_hash(record: dict) -> str:
    encoded = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@router.post("", response_model=InputRecord, status_code=201)
def create_input(request: InputCreate) -> InputRecord:
    with _lock:
        if request.parent_id is not None and request.parent_id not in _records:
            raise HTTPException(status_code=404, detail="parent_id does not identify an existing input.")
        input_id = "inp_" + uuid4().hex
        version_id = "ver_" + uuid4().hex
        # Actor is copied and serialized into the record; later DBA/binding changes
        # cannot rewrite this snapshot.
        snapshot = request.actor.model_copy(deep=True)
        payload = {
            "input_id": input_id,
            "version_id": version_id,
            "parent_id": request.parent_id,
            "content": request.content,
            "context": request.context,
            "actor_snapshot": snapshot.model_dump(mode="json"),
            "status": "validated",
        }
        record = InputRecord(**payload, audit_hash=_canonical_hash(payload))
        _records[input_id] = record
        return record.model_copy(deep=True)


@router.get("/{input_id}", response_model=InputRecord)
def get_input(input_id: str) -> InputRecord:
    with _lock:
        record = _records.get(input_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Input not found.")
        return record.model_copy(deep=True)
