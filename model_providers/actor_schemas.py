"""Typed actor contracts for role-stable, provider-swappable threads."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ModelMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    context_window: int | None = Field(default=None, gt=0)
    temperature: float | None = Field(default=None, ge=0, le=2)
    system_prompt_hash: str | None = Field(default=None, pattern=r"^sha256:[0-9a-fA-F]{64}$")
    model_version: str | None = Field(default=None, max_length=160)


class Provider(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["human", "model", "service"]
    id: str = Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")
    model_meta: ModelMeta | None = None

    @model_validator(mode="after")
    def model_metadata_only_for_models(self) -> "Provider":
        if self.kind != "model" and self.model_meta is not None:
            raise ValueError("model_meta is only valid when provider.kind='model'.")
        return self


class Actor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: str = Field(min_length=1, max_length=120, pattern=r"^[a-z][a-z0-9-]*$")
    provider: Provider
    dba: str | None = Field(default=None, max_length=160)


class InputCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(min_length=1, max_length=100_000)
    context: dict[str, Any] = Field(default_factory=dict)
    actor: Actor
    parent_id: str | None = None


class InputRecord(BaseModel):
    input_id: str
    version_id: str
    parent_id: str | None
    content: str
    context: dict[str, Any]
    actor_snapshot: Actor
    audit_hash: str
    status: Literal["validated", "needs_clarification", "routed", "responded"] = "validated"


class ProviderRecord(BaseModel):
    provider_id: str
    kind: Literal["human", "model", "service"]
    current_dba: str
    active: bool = True
    capabilities: list[str] = Field(default_factory=list)
    model_meta: ModelMeta | None = None


class RoleBindingUpdate(BaseModel):
    provider_id: str = Field(min_length=1, max_length=200)
    dba: str = Field(min_length=1, max_length=160)
