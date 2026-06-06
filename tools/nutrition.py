"""Nutrition planning and food diary MCP tools."""
from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.dependencies import Depends
from mcp.types import ToolAnnotations

from tools.client import WgerClient, get_wger_client

nutrition_server = FastMCP("nutrition")


def _paged(items: list[dict[str, Any]], total: int, offset: int, limit: int) -> dict[str, Any]:
    """Build a standard paged response dict."""
    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + len(items)) < total,
    }


@nutrition_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_nutrition_plans(
    limit: Annotated[int, "Results per page (1-100)"] = 20,
    offset: Annotated[int, "Pagination offset"] = 0,
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """List nutrition plans for the authenticated user."""
    async with client:
        items, total = await client.paginate("/nutritionplan/", limit=limit, offset=offset)
    return _paged(items, total, offset, limit)


@nutrition_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def get_nutrition_plan_info(
    plan_id: Annotated[int, "Nutrition plan ID"],
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """
    Get full nutrition plan details including nested meals, items, and macro totals.

    The response includes energy, protein, carbohydrates, fat breakdowns per meal.
    """
    async with client:
        return await client.get(f"/nutritionplaninfo/{plan_id}/")


@nutrition_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def search_ingredients(
    term: Annotated[str, "Ingredient name to search for"],
    language_id: Annotated[int, "Language ID (2=English)"] = 2,
    limit: Annotated[int, "Results per page (1-100)"] = 20,
    offset: Annotated[int, "Pagination offset"] = 0,
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """Search food ingredients by name."""
    async with client:
        items, total = await client.paginate(
            "/ingredient/",
            limit=limit,
            offset=offset,
            name=term,
            language=language_id,
        )
    return _paged(items, total, offset, limit)


@nutrition_server.tool
async def log_food_diary_entry(
    plan_id: Annotated[int, "Nutrition plan ID"],
    ingredient_id: Annotated[int, "Ingredient ID"],
    amount: Annotated[float, "Amount in grams"],
    datetime_str: Annotated[str, "ISO datetime string (e.g. 2026-06-06T08:00:00)"],
    weight_unit_id: Annotated[int | None, "Weight unit ID (None = grams)"] = None,
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """Log a food diary entry for a nutrition plan."""
    body: dict[str, Any] = {
        "plan": plan_id,
        "ingredient": ingredient_id,
        "amount": amount,
        "datetime": datetime_str,
    }
    if weight_unit_id is not None:
        body["weight_unit"] = weight_unit_id
    async with client:
        return await client.post("/nutritiondiary/", body)


@nutrition_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_food_diary(
    plan_id: Annotated[int | None, "Filter by nutrition plan ID"] = None,
    limit: Annotated[int, "Results per page (1-100)"] = 20,
    offset: Annotated[int, "Pagination offset"] = 0,
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """List food diary entries, optionally filtered by nutrition plan."""
    async with client:
        items, total = await client.paginate(
            "/nutritiondiary/",
            limit=limit,
            offset=offset,
            plan=plan_id,
        )
    return _paged(items, total, offset, limit)
