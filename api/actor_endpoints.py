"""Provider catalog and stable role-slot bindings."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from model_providers.actor_registry import actor_provider_registry
from model_providers.actor_schemas import ProviderRecord, RoleBindingUpdate

router = APIRouter(tags=["actor-provider-bindings"])


@router.get("/actor-providers", response_model=list[ProviderRecord])
def list_actor_providers() -> list[ProviderRecord]:
    return actor_provider_registry.list_providers()


@router.put("/actor-providers/{provider_id}", response_model=ProviderRecord)
def upsert_actor_provider(provider_id: str, record: ProviderRecord) -> ProviderRecord:
    if provider_id != record.provider_id:
        raise HTTPException(status_code=422, detail="Path provider_id must match record.provider_id.")
    try:
        return actor_provider_registry.register(record)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/providers/{provider_id}/record", response_model=ProviderRecord)
def get_actor_provider(provider_id: str) -> ProviderRecord:
    record = actor_provider_registry.get_provider(provider_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Provider not found.")
    return record


@router.get("/role-bindings/{role}")
def get_role_binding(role: str) -> dict[str, str]:
    binding = actor_provider_registry.get_binding(role)
    if binding is None:
        raise HTTPException(status_code=404, detail="Role has no provider binding.")
    return binding


@router.patch("/role-bindings/{role}")
def patch_role_binding(role: str, update: RoleBindingUpdate) -> dict[str, str]:
    """Swap the provider filling a role without rewriting existing input records."""
    try:
        return actor_provider_registry.bind_role(role, update)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
