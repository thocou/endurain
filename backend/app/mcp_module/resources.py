"""MCP resources for Endurain data context."""

import json
from datetime import date, timedelta

from mcp.server.fastmcp import Context

from mcp_module.server import mcp_server
from mcp_module.utils import get_user_id, get_db

import activities.activity.crud as activities_crud
import health.health_weight.crud as weight_crud
import health.health_weight.schema as weight_schema
import health.health_steps.crud as steps_crud
import health.health_steps.schema as steps_schema
import health.health_sleep.crud as sleep_crud
import health.health_sleep.schema as sleep_schema
import users.users.crud as users_crud


@mcp_server.resource(
    "activities://recent",
    name="recent_activities",
    description=(
        "Last 20 activities with name, type, date,"
        " distance, and duration."
    ),
    mime_type="application/json",
)
def recent_activities(ctx: Context) -> str:
    """
    Get the last 20 activities as a JSON summary.

    Args:
        ctx: MCP request context.

    Returns:
        JSON string of recent activities.
    """
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        activities = (
            activities_crud
            .get_user_activities_with_pagination(
                user_id,
                db,
                page_number=1,
                num_records=20,
                user_is_owner=True,
            )
        )
        if not activities:
            return json.dumps([])
        result = []
        for a in activities:
            data = a.model_dump()
            result.append({
                "id": data.get("id"),
                "name": data.get("name"),
                "activity_type": data.get(
                    "activity_type"
                ),
                "start_time": str(
                    data.get("start_time", "")
                ),
                "distance": data.get("distance"),
                "elapsed_time": data.get(
                    "elapsed_time"
                ),
            })
        return json.dumps(result, default=str)
    finally:
        db.close()


@mcp_server.resource(
    "health://summary",
    name="health_summary",
    description=(
        "Last 30 days of weight, steps,"
        " and sleep data."
    ),
    mime_type="application/json",
)
def health_summary(ctx: Context) -> str:
    """
    Get a health summary for the last 30 days.

    Args:
        ctx: MCP request context.

    Returns:
        JSON string with weight, steps, and sleep.
    """
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        cutoff = date.today() - timedelta(days=30)

        weight_records = (
            weight_crud
            .get_all_health_weight_by_user_id(
                user_id, db
            )
        )
        weight_data = []
        if weight_records:
            for r in weight_records:
                if r.date >= cutoff:
                    schema = (
                        weight_schema.HealthWeightRead(
                            **{
                                c.name: getattr(
                                    r, c.name
                                )
                                for c in (
                                    r.__table__.columns
                                )
                            }
                        )
                    )
                    weight_data.append(
                        schema.model_dump(mode="json")
                    )

        steps_records = (
            steps_crud
            .get_all_health_steps_by_user_id(
                user_id, db
            )
        )
        steps_data = []
        if steps_records:
            for r in steps_records:
                if r.date >= cutoff:
                    schema = (
                        steps_schema.HealthStepsRead(
                            **{
                                c.name: getattr(
                                    r, c.name
                                )
                                for c in (
                                    r.__table__.columns
                                )
                            }
                        )
                    )
                    steps_data.append(
                        schema.model_dump(mode="json")
                    )

        sleep_records = (
            sleep_crud
            .get_all_health_sleep_by_user_id(
                user_id, db
            )
        )
        sleep_data = []
        if sleep_records:
            for r in sleep_records:
                if r.date >= cutoff:
                    schema = (
                        sleep_schema.HealthSleepRead(
                            **{
                                c.name: getattr(
                                    r, c.name
                                )
                                for c in (
                                    r.__table__.columns
                                )
                            }
                        )
                    )
                    sleep_data.append(
                        schema.model_dump(mode="json")
                    )

        summary = {
            "period": f"{cutoff.isoformat()} to "
            f"{date.today().isoformat()}",
            "weight": weight_data,
            "steps": steps_data,
            "sleep": sleep_data,
        }
        return json.dumps(summary, default=str)
    finally:
        db.close()


@mcp_server.resource(
    "profile://me",
    name="user_profile",
    description="Authenticated user's profile.",
    mime_type="application/json",
)
def user_profile(ctx: Context) -> str:
    """
    Get the authenticated user's profile.

    Args:
        ctx: MCP request context.

    Returns:
        JSON string of user profile data.
    """
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        user = users_crud.get_user_by_id(
            user_id, db
        )
        if user is None:
            return json.dumps(None)
        profile = {
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
            "first_day_of_week": (
                user.first_day_of_week
            ),
            "currency": user.currency,
        }
        return json.dumps(profile, default=str)
    finally:
        db.close()
