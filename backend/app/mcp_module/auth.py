"""MCP authentication via Endurain API keys."""

from mcp.server.auth.provider import (
    AccessToken,
    TokenVerifier,
)

from core.database import SessionLocal
import api_keys.utils as api_keys_utils


class EndurainTokenVerifier(TokenVerifier):
    """
    Validates Endurain API keys for MCP authentication.

    Attributes:
        None
    """

    async def verify_token(
        self, token: str
    ) -> AccessToken | None:
        """
        Verify an API key token.

        Args:
            token: The raw API key string.

        Returns:
            An AccessToken if valid, or None.
        """
        db = SessionLocal()
        try:
            user = api_keys_utils.validate_api_key(
                token, db
            )
            if user is None:
                return None
            return AccessToken(
                token=token,
                client_id=str(user.id),
                scopes=["read", "write"],
            )
        finally:
            db.close()
