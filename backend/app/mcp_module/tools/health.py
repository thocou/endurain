"""MCP tools for health data operations."""

from datetime import date

from mcp.server.fastmcp import Context

from mcp_module.server import mcp_server
from mcp_module.utils import get_user_id, get_db

import health.health_weight.crud as weight_crud
import health.health_weight.schema as weight_schema
import health.health_steps.crud as steps_crud
import health.health_steps.schema as steps_schema
import health.health_sleep.crud as sleep_crud
import health.health_sleep.schema as sleep_schema


@mcp_server.tool()
def get_weight_data(
    ctx: Context,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """
    Get user's weight records with optional date range.

    Args:
        ctx: MCP request context.
        start_date: Filter start (YYYY-MM-DD).
        end_date: Filter end (YYYY-MM-DD).

    Returns:
        List of weight record dictionaries.
    """
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        records = (
            weight_crud
            .get_all_health_weight_by_user_id(user_id, db)
        )
        if not records:
            return []
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
        result = []
        for r in records:
            if parsed_start and r.date < parsed_start:
                continue
            if parsed_end and r.date > parsed_end:
                continue
            schema = weight_schema.HealthWeightRead(
                **{
                    c.name: getattr(r, c.name)
                    for c in r.__table__.columns
                }
            )
            result.append(
                schema.model_dump(mode="json")
            )
        return result
    finally:
        db.close()


@mcp_server.tool()
def get_steps_data(
    ctx: Context,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """
    Get user's step count records with optional date range.

    Args:
        ctx: MCP request context.
        start_date: Filter start (YYYY-MM-DD).
        end_date: Filter end (YYYY-MM-DD).

    Returns:
        List of step count record dictionaries.
    """
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        records = (
            steps_crud
            .get_all_health_steps_by_user_id(user_id, db)
        )
        if not records:
            return []
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
        result = []
        for r in records:
            if parsed_start and r.date < parsed_start:
                continue
            if parsed_end and r.date > parsed_end:
                continue
            schema = steps_schema.HealthStepsRead(
                **{
                    c.name: getattr(r, c.name)
                    for c in r.__table__.columns
                }
            )
            result.append(
                schema.model_dump(mode="json")
            )
        return result
    finally:
        db.close()


@mcp_server.tool()
def get_sleep_data(
    ctx: Context,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """
    Get user's sleep records with optional date range.

    Args:
        ctx: MCP request context.
        start_date: Filter start (YYYY-MM-DD).
        end_date: Filter end (YYYY-MM-DD).

    Returns:
        List of sleep record dictionaries.
    """
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        records = (
            sleep_crud
            .get_all_health_sleep_by_user_id(user_id, db)
        )
        if not records:
            return []
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
        result = []
        for r in records:
            if parsed_start and r.date < parsed_start:
                continue
            if parsed_end and r.date > parsed_end:
                continue
            schema = sleep_schema.HealthSleepRead(
                **{
                    c.name: getattr(r, c.name)
                    for c in r.__table__.columns
                }
            )
            result.append(
                schema.model_dump(mode="json")
            )
        return result
    finally:
        db.close()


@mcp_server.tool()
def log_weight(
    ctx: Context,
    weight: float,
    date_str: str | None = None,
) -> dict:
    """
    Log a weight entry for the user.

    Args:
        ctx: MCP request context.
        weight: Weight value in kilograms.
        date_str: Date for entry (YYYY-MM-DD), today if omitted.

    Returns:
        Created weight record dictionary.
    """
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        parsed_date = (
            date.fromisoformat(date_str)
            if date_str
            else None
        )
        create_data = weight_schema.HealthWeightCreate(
            date=parsed_date,
            weight=weight,
        )
        record = weight_crud.create_health_weight(
            user_id, create_data, db
        )
        schema = weight_schema.HealthWeightRead(
            **{
                c.name: getattr(record, c.name)
                for c in record.__table__.columns
            }
        )
        return schema.model_dump(mode="json")
    finally:
        db.close()


@mcp_server.tool()
def log_steps(
    ctx: Context,
    step_count: int,
    date_str: str | None = None,
) -> dict:
    """
    Log a step count entry for the user.

    Args:
        ctx: MCP request context.
        step_count: Number of steps taken.
        date_str: Date for entry (YYYY-MM-DD), today if omitted.

    Returns:
        Created steps record dictionary.
    """
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        parsed_date = (
            date.fromisoformat(date_str)
            if date_str
            else None
        )
        create_data = steps_schema.HealthStepsCreate(
            date=parsed_date,
            steps=step_count,
        )
        record = steps_crud.create_health_steps(
            user_id, create_data, db
        )
        schema = steps_schema.HealthStepsRead(
            **{
                c.name: getattr(record, c.name)
                for c in record.__table__.columns
            }
        )
        return schema.model_dump(mode="json")
    finally:
        db.close()
