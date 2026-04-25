"""Pydantic schemas for API key endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class ApiKeyCreate(BaseModel):
    """
    Schema for creating a new API key.

    Attributes:
        name: User-provided label for the key.
    """

    name: str = Field(..., max_length=100)


class ApiKeyResponse(BaseModel):
    """
    Schema for API key list responses.

    Attributes:
        id: Primary key.
        name: User-provided label for the key.
        key_prefix: First 8 chars of raw key.
        created_at: When the key was created.
        last_used_at: When the key was last used.
        expires_at: Optional expiration timestamp.
    """

    id: int
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime | None

    model_config = {"from_attributes": True}


class ApiKeyCreated(ApiKeyResponse):
    """
    Schema returned once on key creation.

    Attributes:
        full_key: The raw API key, shown only once.
    """

    full_key: str
