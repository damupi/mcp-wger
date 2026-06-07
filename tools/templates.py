"""Templates and day-copying MCP tools."""
from __future__ import annotations

from typing import Annotated, Any

import httpx
from fastmcp import FastMCP
from fastmcp.dependencies import Depends
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from tools.client import WgerClient, get_wger_client

templates_server = FastMCP("templates")


def _paged(items: list[dict[str, Any]], total: int, offset: int, limit: int) -> dict[str, Any]:
    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + len(items)) < total,
    }


@templates_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_templates(
    limit: Annotated[int, "Results per page (1-100)"] = 20,
    offset: Annotated[int, "Pagination offset"] = 0,
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """List the user's own workout templates.

    Templates are routines marked as reusable starting points. Use
    copy_day_to_routine() to build a new routine from a template's days.
    """
    async with client:
        items, total = await client.paginate("/templates/", limit=limit, offset=offset)
    return _paged(items, total, offset, limit)


@templates_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_public_templates(
    limit: Annotated[int, "Results per page (1-100)"] = 20,
    offset: Annotated[int, "Pagination offset"] = 0,
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """List community-shared public workout templates.

    Anyone can browse these. Use copy_day_to_routine() to reuse a day
    from a public template in your own routine.
    """
    async with client:
        items, total = await client.paginate("/public-templates/", limit=limit, offset=offset)
    return _paged(items, total, offset, limit)


@templates_server.tool
async def convert_routine_to_template(
    routine_id: Annotated[int, "ID of the routine to mark as a template"],
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """Mark an existing routine as a template.

    Templates appear in list_templates() and can optionally be shared
    publicly via set_template_visibility(). The routine's days and
    exercises are preserved.
    """
    async with client:
        return await client.patch(f"/routine/{routine_id}/", {"is_template": True})


@templates_server.tool
async def convert_template_to_routine(
    routine_id: Annotated[int, "ID of the template to convert back to a regular routine"],
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """Convert a template back into a regular editable routine.

    The routine's days and exercises are preserved; it simply stops
    appearing in the templates list.
    """
    async with client:
        return await client.patch(f"/routine/{routine_id}/", {"is_template": False})


@templates_server.tool
async def set_template_visibility(
    routine_id: Annotated[int, "Template routine ID"],
    is_public: Annotated[bool, "True to share publicly, False to make private"],
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """Share or unshare a template with the community.

    Public templates appear in list_public_templates() for all users.
    """
    async with client:
        return await client.patch(f"/routine/{routine_id}/", {"is_public": is_public})


@templates_server.tool
async def copy_day_to_routine(
    day_id: Annotated[int, "ID of the training day to copy"],
    target_routine_id: Annotated[int, "ID of the routine to copy the day into"],
    new_name: Annotated[str | None, "Optional new name for the copied day"] = None,
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """Copy a training day (with all its exercises) into a different routine.

    Since the wger API has no native duplicate endpoint, this tool
    reconstructs the day client-side:
      1. Reads the source day, its slots, and each slot's exercises
      2. Creates a new day in the target routine
      3. Recreates every slot and exercise entry under the new day

    Use this to reuse a day from a template — or any routine — as a
    starting point in a new routine. The copy is fully independent and
    can be edited without affecting the original.

    Returns a summary: new_day_id, slots_copied, entries_copied.
    """
    async with client:
        # 1. Fetch source day
        try:
            source_day = await client.get(f"/day/{day_id}/")
        except httpx.HTTPStatusError as exc:
            raise ToolError(f"Day {day_id} not found: {exc}") from exc

        # 2. Fetch all slots for this day
        slots, _ = await client.paginate("/slot/", limit=100, day=day_id)

        # 3. Fetch entries for each slot
        slot_entries: dict[int, list[dict[str, Any]]] = {}
        for slot in slots:
            entries, _ = await client.paginate("/slot-entry/", limit=100, slot=slot["id"])
            slot_entries[slot["id"]] = entries

        # 4. Create the new day in the target routine
        new_day = await client.post("/day/", {
            "routine": target_routine_id,
            "name": new_name or source_day["name"],
            "description": source_day.get("description", ""),
            "order": source_day.get("order", 1),
            "is_rest": source_day.get("is_rest", False),
            "type": source_day.get("type", "custom"),
        })
        new_day_id: int = new_day["id"]

        # 5. Recreate slots and entries
        slots_copied = 0
        entries_copied = 0
        for slot in slots:
            new_slot = await client.post("/slot/", {
                "day": new_day_id,
                "order": slot.get("order", 1),
                "comment": slot.get("comment", ""),
            })
            slots_copied += 1

            for entry in slot_entries[slot["id"]]:
                await client.post("/slot-entry/", {
                    "slot": new_slot["id"],
                    "exercise": entry["exercise"],
                    "type": entry.get("type", "normal"),
                    "order": entry.get("order", 1),
                    "comment": entry.get("comment", ""),
                    "repetition_unit": entry.get("repetition_unit", 1),
                    "weight_unit": entry.get("weight_unit", 1),
                })
                entries_copied += 1

    return {
        "new_day_id": new_day_id,
        "source_day_name": source_day["name"],
        "target_routine_id": target_routine_id,
        "slots_copied": slots_copied,
        "entries_copied": entries_copied,
    }
