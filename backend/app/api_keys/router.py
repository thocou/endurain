"""API key management router."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

import auth.security as auth_security
import api_keys.crud as api_keys_crud
import api_keys.schema as api_keys_schema
import core.database as core_database


router = APIRouter()


@router.post(
    "",
    response_model=api_keys_schema.ApiKeyCreated,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    body: api_keys_schema.ApiKeyCreate,
    token_user_id: Annotated[
        int,
        Depends(
            auth_security.get_sub_from_access_token
        ),
    ],
    db: Annotated[
        Session, Depends(core_database.get_db)
    ],
):
    """Create a new API key for the user."""
    return api_keys_crud.create_api_key(
        token_user_id, body.name, db
    )


@router.get(
    "",
    response_model=list[api_keys_schema.ApiKeyResponse],
)
async def list_api_keys(
    token_user_id: Annotated[
        int,
        Depends(
            auth_security.get_sub_from_access_token
        ),
    ],
    db: Annotated[
        Session, Depends(core_database.get_db)
    ],
):
    """List all API keys for the user."""
    return api_keys_crud.list_user_api_keys(
        token_user_id, db
    )


@router.delete(
    "/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_api_key(
    key_id: int,
    token_user_id: Annotated[
        int,
        Depends(
            auth_security.get_sub_from_access_token
        ),
    ],
    db: Annotated[
        Session, Depends(core_database.get_db)
    ],
):
    """Delete an API key by ID."""
    api_keys_crud.delete_api_key(
        token_user_id, key_id, db
    )
    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
