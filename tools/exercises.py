"""Exercise database MCP tools."""
from __future__ import annotations

from typing import Annotated, Any

import httpx
from fastmcp import FastMCP
from fastmcp.dependencies import Depends
from mcp.types import ToolAnnotations

from tools.client import WgerClient, get_wger_client

exercises_server = FastMCP("exercises")


@exercises_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_exercise_categories(
    client: WgerClient = Depends(get_wger_client),
) -> list[dict[str, Any]]:
    """List all exercise categories (Abs, Arms, Back, Calves, Cardio, Chest, Legs, Shoulders)."""
    async with client:
        return await client.paginate_all("/exercisecategory/")


@exercises_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_muscles(
    client: WgerClient = Depends(get_wger_client),
) -> list[dict[str, Any]]:
    """List all muscle groups available in the exercise database."""
    async with client:
        return await client.paginate_all("/muscle/")


@exercises_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_equipment(
    client: WgerClient = Depends(get_wger_client),
) -> list[dict[str, Any]]:
    """List all equipment types (Barbell, Dumbbell, Bodyweight, etc.)."""
    async with client:
        return await client.paginate_all("/equipment/")


@exercises_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def search_exercises(
    term: Annotated[str, "Search term, e.g. 'squat', 'bench press'"],
    language_id: Annotated[int, "Language ID (2=English)"] = 2,
    category_id: Annotated[int | None, "Filter by category ID"] = None,
    equipment_id: Annotated[int | None, "Filter by equipment ID"] = None,
    muscle_id: Annotated[int | None, "Filter by primary muscle ID"] = None,
    limit: Annotated[int, "Results per page (1-100)"] = 20,
    offset: Annotated[int, "Pagination offset"] = 0,
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """
    Search exercises by name.

    Returns translation objects with exercise IDs.
    Use the exercise ID with get_exercise_info() for full details.
    """
    async with client:
        items, total = await client.paginate(
            "/exercise-translation/",
            limit=limit,
            offset=offset,
            format="json",
            language=language_id,
            term=term,
            category=category_id,
            equipment=equipment_id,
            muscles=muscle_id,
        )
    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + len(items)) < total,
    }


@exercises_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def get_exercise_info(
    exercise_id: Annotated[int, "Exercise ID to retrieve full details for"],
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """
    Get full exercise details: muscles targeted, equipment needed, images, translations.

    Use this after search_exercises() to get the complete exercise profile.
    """
    from fastmcp.exceptions import ToolError

    try:
        async with client:
            return await client.get(f"/exerciseinfo/{exercise_id}/")
    except httpx.HTTPStatusError as exc:
        raise ToolError(f"Exercise {exercise_id} not found: {exc}") from exc
