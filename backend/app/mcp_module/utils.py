"""Utility functions for MCP tool implementations."""

from mcp.server.fastmcp import Context
from mcp.server.auth.middleware.auth_context import (
    get_access_token,
)

from core.database import SessionLocal


def get_user_id(ctx: Context) -> int:
    """
    Extract user_id from the MCP auth context.

    Args:
        ctx: The MCP request context.

    Returns:
        The authenticated user's ID.
    """
    token = get_access_token()
    if token is None:
        raise ValueError("No access token found")
    return int(token.client_id)


def get_db():
    """
    Get a new database session.

    Caller must close it when done.

    Returns:
        A new SQLAlchemy database session.
    """
    return SessionLocal()
