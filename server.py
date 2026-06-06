"""FastMCP MCP server for the wger fitness tracker."""
from __future__ import annotations

import argparse

from dotenv import load_dotenv
from fastmcp import FastMCP

from tools.exercises import exercises_server
from tools.nutrition import nutrition_server
from tools.tracking import tracking_server
from tools.user import user_server
from tools.workouts import workouts_server

load_dotenv()

mcp = FastMCP(
    name="wger",
    instructions=(
        "This server provides access to a wger self-hosted fitness tracker. "
        "You can read and write workout routines, log exercise sets, browse "
        "the exercise database, track nutrition, log body weight and measurements, "
        "and view user profile statistics. "
        "Start with list_exercise_categories() or search_exercises() to find exercise IDs, "
        "then use log_workout_set() to record training. "
        "Use get_user_profile() to see the user's preferred units."
    ),
)

mcp.mount(exercises_server)
mcp.mount(workouts_server)
mcp.mount(nutrition_server)
mcp.mount(tracking_server)
mcp.mount(user_server)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="wger FastMCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport to use (default: stdio)",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host for HTTP transport")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP transport")
    args = parser.parse_args()

    if args.transport == "http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")
