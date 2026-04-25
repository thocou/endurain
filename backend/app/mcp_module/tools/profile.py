"""MCP tools for user profile and goals operations."""

from mcp.server.fastmcp import Context

from mcp_module.server import mcp_server
from mcp_module.utils import get_user_id, get_db

import users.users.crud as users_crud
import users.users_goals.crud as goals_crud
import users.users_goals.schema as goals_schema


@mcp_server.tool()
def get_profile(ctx: Context) -> dict | None:
    """
    Get the authenticated user's profile information.

    Returns name, username, email, city, birthdate,
    gender, units, height, max heart rate, preferred
    language, first day of week, and currency.

    Args:
        ctx: MCP request context.

    Returns:
        Profile dictionary or None if not found.
    """
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        user = users_crud.get_user_by_id(user_id, db)
        if user is None:
            return None
        return {
            "id": user.id,
            "name": user.name,
            "username": user.username,
            "email": user.email,
            "city": user.city,
            "birthdate": (
                user.birthdate.isoformat()
                if user.birthdate
                else None
            ),
            "gender": user.gender,
            "units": user.units,
            "height": user.height,
            "max_heart_rate": user.max_heart_rate,
            "preferred_language": (
                user.preferred_language
            ),
            "first_day_of_week": user.first_day_of_week,
            "currency": user.currency,
        }
    finally:
        db.close()


@mcp_server.tool()
def get_goals(ctx: Context) -> list[dict]:
    """
    Get the authenticated user's training goals.

    Args:
        ctx: MCP request context.

    Returns:
        List of goal dictionaries.
    """
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        goals = goals_crud.get_user_goals_by_user_id(
            user_id, db
        )
        if not goals:
            return []
        return [
            goals_schema.UsersGoalRead.model_validate(
                g, from_attributes=True
            ).model_dump(mode="json")
            for g in goals
        ]
    finally:
        db.close()
