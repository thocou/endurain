"""CRUD operations for user API keys."""

import hashlib
import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import api_keys.models as api_keys_models
import api_keys.schema as api_keys_schema
import core.logger as core_logger


def create_api_key(
    user_id: int, name: str, db: Session
) -> api_keys_schema.ApiKeyCreated:
    """
    Create a new API key for a user.

    Args:
        user_id: ID of the user creating the key.
        name: User-provided label for the key.
        db: Database session.

    Returns:
        ApiKeyCreated with the full key shown once.

    Raises:
        HTTPException: On database error.
    """
    try:
        raw_key = secrets.token_urlsafe(32)
        key_prefix = raw_key[:8]
        key_hash = hashlib.sha256(
            raw_key.encode()
        ).hexdigest()

        db_key = api_keys_models.UserApiKey(
            user_id=user_id,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
        )
        db.add(db_key)
        db.commit()
        db.refresh(db_key)

        return api_keys_schema.ApiKeyCreated(
            id=db_key.id,
            name=db_key.name,
            key_prefix=db_key.key_prefix,
            created_at=db_key.created_at,
            last_used_at=db_key.last_used_at,
            expires_at=db_key.expires_at,
            full_key=raw_key,
        )
    except Exception as err:
        core_logger.print_to_log(
            f"Error in create_api_key: {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Internal Server Error",
        ) from err


def list_user_api_keys(
    user_id: int, db: Session
) -> list[api_keys_models.UserApiKey]:
    """
    List all API keys for a user.

    Args:
        user_id: ID of the user.
        db: Database session.

    Returns:
        List of UserApiKey models ordered by created_at
        desc.

    Raises:
        HTTPException: On database error.
    """
    try:
        return (
            db.query(api_keys_models.UserApiKey)
            .filter(
                api_keys_models.UserApiKey.user_id
                == user_id
            )
            .order_by(
                api_keys_models.UserApiKey.created_at.desc()
            )
            .all()
        )
    except Exception as err:
        core_logger.print_to_log(
            f"Error in list_user_api_keys: {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Internal Server Error",
        ) from err


def delete_api_key(
    user_id: int, key_id: int, db: Session
) -> None:
    """
    Delete an API key owned by the user.

    Args:
        user_id: ID of the user.
        key_id: ID of the API key to delete.
        db: Database session.

    Returns:
        None.

    Raises:
        HTTPException: If key not found or on error.
    """
    try:
        db_key = (
            db.query(api_keys_models.UserApiKey)
            .filter(
                api_keys_models.UserApiKey.id == key_id,
                api_keys_models.UserApiKey.user_id
                == user_id,
            )
            .first()
        )

        if db_key is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key {key_id} not found",
            )

        db.delete(db_key)
        db.commit()
    except HTTPException:
        raise
    except Exception as err:
        core_logger.print_to_log(
            f"Error in delete_api_key: {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Internal Server Error",
        ) from err
