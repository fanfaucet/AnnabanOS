"""In-memory provider catalog and role-to-provider bindings for the prototype."""
from __future__ import annotations

from copy import deepcopy
from threading import RLock

from model_providers.actor_schemas import Actor, ProviderRecord, RoleBindingUpdate


class ActorProviderRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._providers: dict[str, ProviderRecord] = {}
        self._role_bindings: dict[str, dict[str, str]] = {}

    def register(self, record: ProviderRecord) -> ProviderRecord:
        with self._lock:
            existing = self._providers.get(record.provider_id)
            if existing is not None and existing.kind != record.kind:
                raise ValueError("A provider ID is immutable and cannot change kind.")
            self._providers[record.provider_id] = record.model_copy(deep=True)
            return record.model_copy(deep=True)

    def get_provider(self, provider_id: str) -> ProviderRecord | None:
        with self._lock:
            record = self._providers.get(provider_id)
            return record.model_copy(deep=True) if record else None

    def list_providers(self) -> list[ProviderRecord]:
        with self._lock:
            return [item.model_copy(deep=True) for item in self._providers.values()]

    def bind_role(self, role: str, update: RoleBindingUpdate) -> dict[str, str]:
        with self._lock:
            provider = self._providers.get(update.provider_id)
            if provider is None or not provider.active:
                raise KeyError("Provider not found or inactive.")
            self._role_bindings[role] = {
                "role": role,
                "provider_id": provider.provider_id,
                "dba": update.dba,
            }
            return deepcopy(self._role_bindings[role])

    def get_binding(self, role: str) -> dict[str, str] | None:
        with self._lock:
            binding = self._role_bindings.get(role)
            return deepcopy(binding) if binding else None

    def resolve_actor(self, role: str) -> Actor | None:
        with self._lock:
            binding = self._role_bindings.get(role)
            if not binding:
                return None
            provider = self._providers.get(binding["provider_id"])
            if not provider or not provider.active:
                return None
            meta = provider.model_meta
            model_meta = meta.model_copy(deep=True) if meta else None
            return Actor(
                role=role,
                provider={"kind": provider.kind, "id": provider.provider_id, "model_meta": model_meta},
                dba=binding["dba"],
            )


actor_provider_registry = ActorProviderRegistry()
