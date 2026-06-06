# fastmcp-wger

[![Tests](https://github.com/damupi/mcp-wger/actions/workflows/test.yml/badge.svg)](https://github.com/damupi/mcp-wger/actions/workflows/test.yml)

FastMCP server that wraps the [wger](https://github.com/wger-project/wger) fitness REST API as an MCP interface. Lets any MCP-compatible LLM (Claude Desktop, etc.) read and write your workout data via natural language. Works with the public [wger.de](https://wger.de) instance out of the box, or with any self-hosted wger server.

## Features

- **Exercises** — search the exercise database, browse categories, muscles, equipment
- **Workouts** — manage routines, log sets (weight + reps), review training sessions
- **Nutrition** — manage nutrition plans, log food diary entries, search ingredients
- **Tracking** — log body weight, record body measurements by category
- **User** — read profile settings and overall training statistics

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- A wger account — either on [wger.de](https://wger.de) (free, no setup) or a self-hosted instance

## Installation

```bash
git clone https://github.com/damupi/mcp-wger.git
cd mcp-wger
uv sync
```

Or install directly as a CLI tool:

```bash
uv tool install git+https://github.com/damupi/mcp-wger.git
```

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```env
# Optional — defaults to https://wger.de/api/v2 if not set
# WGER_BASE_URL=http://localhost:80/api/v2

WGER_API_TOKEN=your-token-here
```

Get your API token from wger at **Settings → API key**.

### Using wger.de (public instance)

1. Create a free account at [wger.de](https://wger.de/en/user/register)
2. Go to **Settings → API key** and copy your token
3. Set `WGER_API_TOKEN` in your `.env` — no need to set `WGER_BASE_URL`

### Self-hosting wger

Run wger locally with Docker:

```bash
docker run -ti --name wger \
  -p 80:80 \
  wger/server:latest
```

Then set both variables in your `.env`:

```env
WGER_BASE_URL=http://localhost:80/api/v2
WGER_API_TOKEN=your-token-here
```

Full self-hosting docs: [github.com/wger-project/wger](https://github.com/wger-project/wger#installation)

## Usage

### stdio (default — for Claude Desktop)

```bash
mcp-wger
# or without installing:
uv run mcp-wger
```

### HTTP transport

```bash
mcp-wger --transport http --port 8000
```

Options:
- `--transport` — `stdio` (default) or `http`
- `--host` — bind address for HTTP (default: `0.0.0.0`)
- `--port` — port for HTTP (default: `8000`)

### Claude Desktop integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "wger": {
      "command": "uv",
      "args": ["run", "mcp-wger"],
      "cwd": "/path/to/fastmcp-wger",
      "env": {
        "WGER_API_TOKEN": "your-token-here",
        "WGER_BASE_URL": "http://localhost:80/api/v2"
      }
    }
  }
}
```

### Interactive dev inspector

```bash
uv run fastmcp dev server.py
```

## Available Tools

| Tool | Description |
|---|---|
| `search_exercises` | Search by name (e.g. "squat", "bench press") |
| `get_exercise_info` | Full detail: muscles, equipment, images |
| `list_exercise_categories` | All categories (Abs, Arms, Back, …) |
| `list_muscles` / `list_equipment` | Reference lists |
| `list_routines` | Your workout routines |
| `get_routine` / `create_routine` | Fetch or create a routine |
| `log_workout_set` | Record a set (exercise + reps + weight + date) |
| `list_workout_logs` | History of logged sets, filterable by date/exercise |
| `list_training_sessions` | High-level session summaries |
| `list_nutrition_plans` | Your nutrition plans |
| `get_nutrition_plan_info` | Plan with nested meals and macro totals |
| `search_ingredients` | Find food ingredients |
| `log_food_diary_entry` | Log a food entry to a plan |
| `list_food_diary` | Review food diary |
| `list_weight_entries` / `add_weight_entry` | Body weight log |
| `list_measurement_categories` | Body measurement categories |
| `list_measurements` / `add_measurement` | Body measurement log |
| `get_user_profile` | Profile settings (units, language) |
| `get_user_statistics` | Training statistics summary |

## Development

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=tools --cov-report=html
```

All tools are tested with `respx`-mocked httpx calls. Coverage target: 100%.

## Project Structure

```
fastmcp-wger/
├── server.py          # Entry point — mounts all tool sub-servers
├── tools/
│   ├── client.py      # WgerClient (async httpx wrapper + pagination)
│   ├── exercises.py
│   ├── workouts.py
│   ├── nutrition.py
│   ├── tracking.py
│   └── user.py
└── test/
    ├── conftest.py
    ├── test_client.py
    ├── test_exercises.py
    ├── test_workouts.py
    ├── test_nutrition.py
    ├── test_tracking.py
    └── test_user.py
```
