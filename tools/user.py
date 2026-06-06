"""User profile and statistics MCP tools."""
from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from fastmcp.dependencies import Depends
from mcp.types import ToolAnnotations

from tools.client import WgerClient, get_wger_client

user_server = FastMCP("user")


@user_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def get_user_profile(
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """
    Get the authenticated user's profile.

    Returns preferred units (kg/lb), language, gym, and other settings.
    """
    async with client:
        results, _ = await client.paginate("/userprofile/", limit=1, offset=0)
    return results[0] if results else {}


@user_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def get_user_statistics(
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """
    Get user training statistics.

    Includes workout counts, total weight lifted, weight history summary.
    """
    async with client:
        return await client.get("/user-statistics/")
