"""MCP prompt templates for AI assistant workflows."""

from mcp_module.server import mcp_server


@mcp_server.prompt(
    name="analyze_training",
    description=(
        "Analyze training load, volume, intensity,"
        " and recovery over a given period."
    ),
)
def analyze_training(
    period: str = "last_30_days",
) -> list[dict]:
    """
    Build a training analysis prompt.

    Args:
        period: Time period to analyze.

    Returns:
        List of message dicts for the LLM.
    """
    return [
        {
            "role": "user",
            "content": (
                f"Analyze my training for the period:"
                f" {period}.\n\n"
                "Please use the available tools to:\n"
                "1. Fetch my recent activities using"
                " list_activities\n"
                "2. Look at activity details and laps"
                " for key workouts\n"
                "3. Check my health data (weight,"
                " steps, sleep) using the health"
                " tools\n"
                "4. Review my goals using get_goals\n"
                "\nThen provide an analysis covering:"
                "\n- Training volume (total distance,"
                " duration, number of sessions)\n"
                "- Intensity distribution (easy vs"
                " hard sessions)\n"
                "- Recovery indicators (sleep quality,"
                " rest days)\n"
                "- Progress toward goals\n"
                "- Recommendations for the next"
                " training period"
            ),
        }
    ]


@mcp_server.prompt(
    name="weekly_summary",
    description=(
        "Generate a weekly recap of activities,"
        " health metrics, and progress."
    ),
)
def weekly_summary() -> list[dict]:
    """
    Build a weekly summary prompt.

    Returns:
        List of message dicts for the LLM.
    """
    return [
        {
            "role": "user",
            "content": (
                "Generate my weekly training and"
                " health summary.\n\n"
                "Please use the available tools to:\n"
                "1. Fetch this week's activities using"
                " list_activities with appropriate"
                " date filters\n"
                "2. Get my health data (weight, steps,"
                " sleep) for this week\n"
                "3. Check my profile and goals\n"
                "\nThen create a summary including:\n"
                "- Activities completed (type,"
                " distance, duration, key metrics)\n"
                "- Health trends (weight change, avg"
                " steps, sleep quality)\n"
                "- Goal progress (% completion for"
                " each active goal)\n"
                "- Highlights and personal records\n"
                "- Suggested focus areas for next week"
            ),
        }
    ]


@mcp_server.prompt(
    name="gear_check",
    description=(
        "Assess gear usage, distance accumulation,"
        " and suggest maintenance or replacement."
    ),
)
def gear_check() -> list[dict]:
    """
    Build a gear assessment prompt.

    Returns:
        List of message dicts for the LLM.
    """
    return [
        {
            "role": "user",
            "content": (
                "Review my gear and provide"
                " maintenance recommendations.\n\n"
                "Please use the available tools to:\n"
                "1. List all my gear using list_gear\n"
                "2. Get details for each gear item\n"
                "3. Check recent activities to see"
                " gear usage patterns\n"
                "\nThen provide an assessment"
                " covering:\n"
                "- Current gear inventory and status\n"
                "- Distance/time accumulated on each"
                " item\n"
                "- Gear approaching replacement"
                " thresholds (e.g. running shoes"
                " > 500-800 km)\n"
                "- Maintenance suggestions\n"
                "- Recommendations for gear rotation"
                " or replacement"
            ),
        }
    ]
