"""Utility functions for API key validation."""

import hashlib
from datetime import datetime, timezone

from sqlalchemy.orm import Session

import api_keys.models as api_keys_models
import core.logger as core_logger
import users.users.models as users_models


def validate_api_key(
    token: str, db: Session
) -> users_models.Users | None:
    """
    Validate a raw API key and return the user.

    Computes the SHA-256 hash of the token, looks up
    the matching key, checks expiration, updates
    last_used_at, and returns the associated user.

    Args:
        token: The raw API key string.
        db: Database session.

    Returns:
        The associated Users object, or None if the
        key is invalid or expired.
    """
    try:
        key_hash = hashlib.sha256(
            token.encode()
        ).hexdigest()

        api_key = (
            db.query(api_keys_models.UserApiKey)
            .filter(
                api_keys_models.UserApiKey.key_hash
                == key_hash
            )
            .first()
        )

        if api_key is None:
            return None

        if (
            api_key.expires_at is not None
            and api_key.expires_at
            < datetime.now(timezone.utc)
        ):
            return None

        api_key.last_used_at = datetime.now(
            timezone.utc
        )
        db.commit()
        db.refresh(api_key)

        return api_key.users
    except Exception as err:
        core_logger.print_to_log(
            f"Error in validate_api_key: {err}",
            "error",
            exc=err,
        )
        return None
