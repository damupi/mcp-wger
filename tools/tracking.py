"""Body weight and measurement tracking MCP tools."""
from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.dependencies import Depends
from mcp.types import ToolAnnotations

from tools.client import WgerClient, get_wger_client

tracking_server = FastMCP("tracking")


def _paged(items: list[dict[str, Any]], total: int, offset: int, limit: int) -> dict[str, Any]:
    """Build a standard paged response dict."""
    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + len(items)) < total,
    }


@tracking_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_weight_entries(
    limit: Annotated[int, "Results per page (1-100)"] = 30,
    offset: Annotated[int, "Pagination offset"] = 0,
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """List body weight entries for the authenticated user, most recent first."""
    async with client:
        items, total = await client.paginate("/weightentry/", limit=limit, offset=offset)
    return _paged(items, total, offset, limit)


@tracking_server.tool
async def add_weight_entry(
    weight: Annotated[float, "Body weight value"],
    date: Annotated[str, "Date of measurement (YYYY-MM-DD)"],
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """Add a new body weight entry."""
    async with client:
        return await client.post("/weightentry/", {"weight": weight, "date": date})


@tracking_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_measurement_categories(
    client: WgerClient = Depends(get_wger_client),
) -> list[dict[str, Any]]:
    """List all measurement categories (e.g. Body Fat, Chest, Waist)."""
    async with client:
        return await client.paginate_all("/measurement-category/")


@tracking_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_measurements(
    category_id: Annotated[int, "Measurement category ID to filter by"],
    limit: Annotated[int, "Results per page (1-100)"] = 30,
    offset: Annotated[int, "Pagination offset"] = 0,
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """List measurements for a given category."""
    async with client:
        items, total = await client.paginate(
            "/measurement/",
            limit=limit,
            offset=offset,
            category=category_id,
        )
    return _paged(items, total, offset, limit)


@tracking_server.tool
async def add_measurement(
    category_id: Annotated[int, "Measurement category ID"],
    value: Annotated[float, "Measurement value"],
    date: Annotated[str, "Date of measurement (YYYY-MM-DD)"],
    notes: Annotated[str, "Optional notes"] = "",
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """Add a new measurement entry to a category."""
    body: dict[str, Any] = {
        "category": category_id,
        "value": value,
        "date": date,
        "notes": notes,
    }
    async with client:
        return await client.post("/measurement/", body)
