# MCP (Model Context Protocol)

Endurain includes a built-in [MCP](https://modelcontextprotocol.io/) server that allows AI assistants like Claude Desktop, VS Code Copilot, and other MCP-compatible clients to interact with your fitness data.

The MCP server is available at `/mcp` on your Endurain instance and uses the streamable HTTP transport. Authentication is handled via API keys.

## Prerequisites

- A running Endurain instance (v0.18.0 or later)
- A user account on the instance
- An MCP-compatible client (e.g., Claude Desktop, VS Code with GitHub Copilot)

## Generate an API Key

1. Log in to your Endurain instance
2. Navigate to **Settings** → **API Keys**
3. Enter a name for the key (e.g., "Claude Desktop") and click **Create**
4. Copy the full API key immediately — it will only be shown once
5. The key will appear in the list with its prefix for identification

## Configure Claude Desktop

Add the following to your Claude Desktop MCP configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "endurain": {
      "url": "https://your-endurain.example.com/mcp",
      "headers": {
        "Authorization": "Bearer <your-api-key>"
      }
    }
  }
}
```

Replace `https://your-endurain.example.com` with your actual Endurain URL and `<your-api-key>` with the full key you copied.

## Configure Other MCP Clients

Any MCP client that supports the streamable HTTP transport can connect to Endurain. The generic configuration requires:

- **URL:** `https://your-endurain.example.com/mcp`
- **Authorization header:** `Bearer <your-api-key>`
- **Transport:** Streamable HTTP

## Available Tools

MCP tools allow AI assistants to read and write your fitness data.

### Activities

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_activities` | List activities with optional filters | `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD), `activity_type` (int), `page_number` (default 1), `num_records` (default 10) |
| `get_activity` | Get a single activity by ID | `activity_id` (int) |
| `get_activity_laps` | Get lap data for an activity | `activity_id` (int) |
| `get_activity_streams` | Get GPS, heart rate, and power stream data | `activity_id` (int) |
| `delete_activity` | Delete an activity by ID | `activity_id` (int) |

### Health

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_weight_data` | Get weight records | `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD) |
| `get_steps_data` | Get step count records | `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD) |
| `get_sleep_data` | Get sleep records | `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD) |
| `log_weight` | Log a weight entry | `weight` (float, kg), `date_str` (YYYY-MM-DD, defaults to today) |
| `log_steps` | Log a step count entry | `step_count` (int), `date_str` (YYYY-MM-DD, defaults to today) |

### Gear

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_gear` | List gear with optional type filter | `gear_type` (int: 1=bike, 2=shoes, 3=wetsuit, 4=racquet, 5=skis, 6=snowboard, 7=windsurf, 8=water sports board) |
| `get_gear` | Get a specific gear item | `gear_id` (int) |
| `create_gear` | Create a new gear item | `nickname` (str), `gear_type` (int), `brand` (str), `model` (str) |
| `delete_gear` | Delete a gear item | `gear_id` (int) |

### Profile

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_profile` | Get your profile information | — |
| `get_goals` | Get your training goals | — |

## Available Resources

Resources provide pre-built data snapshots that AI assistants can load into context.

| URI | Description |
|-----|-------------|
| `activities://recent` | Last 20 activities (name, type, date, distance, duration) |
| `health://summary` | Last 30 days of weight, steps, and sleep data |
| `profile://me` | Your profile information |

## Available Prompts

Prompts are reusable templates that guide AI assistants through common analyses.

| Prompt | Arguments | Description |
|--------|-----------|-------------|
| `analyze_training` | `period` (default: `last_30_days`) | Analyze training load, volume, intensity, and recovery |
| `weekly_summary` | — | Generate a weekly recap of activities, health metrics, and progress |
| `gear_check` | — | Assess gear usage, distance accumulation, and suggest maintenance |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_ENABLED` | `true` | Set to `false` to disable the MCP server endpoint |

When `MCP_ENABLED` is set to `false`, the `/mcp` endpoint will not be mounted and requests to it will return a 404 response.

## Troubleshooting

**401 Unauthorized** — The API key is missing, invalid, or expired. Generate a new key from Settings → API Keys.

**404 Not Found on `/mcp`** — The MCP server may be disabled. Check that `MCP_ENABLED` is not set to `false` in your environment.

**Connection refused** — Ensure your Endurain instance is running and accessible at the URL configured in your MCP client.

**Tools not appearing** — Verify the MCP client is configured with the correct URL and authorization header. Check the Endurain logs for authentication errors.

**Data not returned** — Each API key is scoped to a single user. The MCP tools will only return data belonging to the user who owns the API key.
