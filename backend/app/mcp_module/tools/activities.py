"""MCP tools for activity operations."""

from datetime import date

from mcp.server.fastmcp import Context

from mcp_module.server import mcp_server
from mcp_module.utils import get_user_id, get_db

import activities.activity.crud as activities_crud
import activities.activity_laps.crud as laps_crud
import activities.activity_streams.crud as streams_crud


@mcp_server.tool()
def list_activities(
    ctx: Context,
    start_date: str | None = None,
    end_date: str | None = None,
    activity_type: int | None = None,
    page_number: int = 1,
    num_records: int = 10,
) -> list[dict]:
    """
    List user's activities with optional filters.

    Args:
        ctx: MCP request context.
        start_date: Filter start (YYYY-MM-DD).
        end_date: Filter end (YYYY-MM-DD).
        activity_type: Filter by activity type ID.
        page_number: Page number for pagination.
        num_records: Number of records per page.

    Returns:
        List of activity dictionaries.
    """
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        parsed_start = (
            date.fromisoformat(start_date)
            if start_date
            else None
        )
        parsed_end = (
            date.fromisoformat(end_date)
            if end_date
            else None
        )
        activities = (
            activities_crud
            .get_user_activities_with_pagination(
                user_id,
                db,
                page_number=page_number,
                num_records=num_records,
                activity_type=activity_type,
                start_date=parsed_start,
                end_date=parsed_end,
                user_is_owner=True,
            )
        )
        if not activities:
            return []
        return [a.model_dump() for a in activities]
    finally:
        db.close()


@mcp_server.tool()
def get_activity(
    ctx: Context,
    activity_id: int,
) -> dict | None:
    """
    Get a single activity by ID.

    Args:
        ctx: MCP request context.
        activity_id: The activity ID to retrieve.

    Returns:
        Activity dictionary or None if not found.
    """
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        activity = (
            activities_crud
            .get_activity_by_id_from_user_id(
                activity_id, user_id, db
            )
        )
        if activity is None:
            return None
        return activity.model_dump()
    finally:
        db.close()


@mcp_server.tool()
def get_activity_laps(
    ctx: Context,
    activity_id: int,
) -> list[dict]:
    """
    Get lap data for an activity.

    Args:
        ctx: MCP request context.
        activity_id: The activity ID.

    Returns:
        List of lap dictionaries.
    """
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        laps = laps_crud.get_activity_laps(
            activity_id, user_id, db
        )
        if not laps:
            return []
        return [lap.model_dump() for lap in laps]
    finally:
        db.close()


@mcp_server.tool()
def get_activity_streams(
    ctx: Context,
    activity_id: int,
) -> list[dict]:
    """
    Get GPS, heart rate, and power stream data.

    Args:
        ctx: MCP request context.
        activity_id: The activity ID.

    Returns:
        List of stream dictionaries.
    """
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        streams = streams_crud.get_activity_streams(
            activity_id, user_id, db
        )
        if not streams:
            return []
        return [s.model_dump() for s in streams]
    finally:
        db.close()


@mcp_server.tool()
def delete_activity(
    ctx: Context,
    activity_id: int,
) -> str:
    """
    Delete an activity by ID.

    Args:
        ctx: MCP request context.
        activity_id: The activity ID to delete.

    Returns:
        Confirmation message.
    """
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        # Verify ownership before deleting
        activity = (
            activities_crud
            .get_activity_by_id_from_user_id(
                activity_id, user_id, db
            )
        )
        if activity is None:
            return (
                f"Activity {activity_id} not found "
                f"or not owned by user."
            )
        activities_crud.delete_activity(
            activity_id, db
        )
        return (
            f"Activity {activity_id} deleted "
            f"successfully."
        )
    finally:
        db.close()
