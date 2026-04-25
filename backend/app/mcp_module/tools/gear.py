"""MCP tools for gear operations."""

from mcp.server.fastmcp import Context

from mcp_module.server import mcp_server
from mcp_module.utils import get_user_id, get_db

import gears.gear.crud as gear_crud
import gears.gear.schema as gear_schema


@mcp_server.tool()
def list_gear(
    ctx: Context,
    gear_type: int | None = None,
) -> list[dict]:
    """
    List user's gear with optional type filter.

    Args:
        ctx: MCP request context.
        gear_type: Filter by gear type ID (1=bike, 2=shoes,
            3=wetsuit, 4=racquet, 5=skis, 6=snowboard,
            7=windsurf, 8=water sports board).

    Returns:
        List of gear dictionaries.
    """
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        if gear_type is not None:
            gears = gear_crud.get_gear_by_type_and_user(
                gear_type, user_id, db
            )
        else:
            gears = gear_crud.get_gear_user(
                user_id, db
            )
        if not gears:
            return []
        return [
            gear_schema.Gear.model_validate(
                g, from_attributes=True
            ).model_dump(mode="json")
            for g in gears
        ]
    finally:
        db.close()


@mcp_server.tool()
def get_gear(
    ctx: Context,
    gear_id: int,
) -> dict | None:
    """
    Get a specific gear item by ID.

    Args:
        ctx: MCP request context.
        gear_id: The gear ID to retrieve.

    Returns:
        Gear dictionary or None if not found.
    """
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        gear = gear_crud.get_gear_user_by_id(
            user_id, gear_id, db
        )
        if gear is None:
            return None
        return gear.model_dump(mode="json")
    finally:
        db.close()


@mcp_server.tool()
def create_gear(
    ctx: Context,
    nickname: str,
    gear_type: int,
    brand: str | None = None,
    model: str | None = None,
) -> dict:
    """
    Create a new gear item.

    Args:
        ctx: MCP request context.
        nickname: Name for the gear.
        gear_type: Type ID (1=bike, 2=shoes, 3=wetsuit,
            4=racquet, 5=skis, 6=snowboard, 7=windsurf,
            8=water sports board).
        brand: Gear brand name.
        model: Gear model name.

    Returns:
        Created gear dictionary.
    """
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        gear_data = gear_schema.Gear(
            nickname=nickname,
            gear_type=gear_type,
            brand=brand,
            model=model,
            active=True,
            initial_kms=0,
        )
        created = gear_crud.create_gear(
            gear_data, user_id, db
        )
        return created.model_dump(mode="json")
    finally:
        db.close()


@mcp_server.tool()
def delete_gear(
    ctx: Context,
    gear_id: int,
) -> str:
    """
    Delete a gear item by ID.

    Args:
        ctx: MCP request context.
        gear_id: The gear ID to delete.

    Returns:
        Confirmation message.
    """
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        # Verify ownership before deleting
        gear = gear_crud.get_gear_user_by_id(
            user_id, gear_id, db
        )
        if gear is None:
            return (
                f"Gear {gear_id} not found "
                f"or not owned by user."
            )
        gear_crud.delete_gear(gear_id, db)
        return (
            f"Gear {gear_id} deleted successfully."
        )
    finally:
        db.close()
