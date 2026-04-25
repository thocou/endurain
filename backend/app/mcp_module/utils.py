"""Utility functions for MCP tool implementations."""

from mcp.server.fastmcp import Context

from core.database import SessionLocal


def get_user_id(ctx: Context) -> int:
    """
    Extract user_id from the MCP auth context.

    Args:
        ctx: The MCP request context.

    Returns:
        The authenticated user's ID.
    """
    return int(
        ctx.request_context.access_token.client_id
    )


def get_db():
    """
    Get a new database session.

    Caller must close it when done.

    Returns:
        A new SQLAlchemy database session.
    """
    return SessionLocal()
