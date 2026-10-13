"""Self-service API for people offering a hosted model."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, SecretStr

from model_providers.registry import community_provider_registry

router = APIRouter(prefix="/providers", tags=["community-model-providers"])


class ProviderRegistration(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)
    endpoint_url: str = Field(description="Public HTTPS base URL for an OpenAI-compatible chat-completions API.")
    model_name: str = Field(min_length=1, max_length=160)
    api_key: SecretStr = Field(default=SecretStr(""))
    owner_token: SecretStr = Field(min_length=32, description="Generate a random secret and store it securely.")


class ProviderPublicRecord(BaseModel):
    provider_id: str
    display_name: str
    model_name: str
    protocol: str
    status: str


@router.post("/register", response_model=ProviderPublicRecord, status_code=201)
def register_provider(request: ProviderRegistration) -> dict[str, str]:
    """Register a provider without returning credentials."""
    try:
        return community_provider_registry.register(
            display_name=request.display_name,
            endpoint_url=request.endpoint_url,
            model_name=request.model_name,
            api_key=request.api_key.get_secret_value(),
            owner_token=request.owner_token.get_secret_value(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("", response_model=list[ProviderPublicRecord])
def list_providers() -> list[dict[str, str]]:
    return community_provider_registry.list_public()


@router.delete("/{provider_id}", status_code=204)
def unregister_provider(
    provider_id: str,
    owner_token: Annotated[str | None, Header(alias="X-Provider-Owner-Token")] = None,
) -> None:
    if not owner_token or not community_provider_registry.remove(provider_id, owner_token):
        raise HTTPException(status_code=404, detail="Provider not found or owner token invalid.")
