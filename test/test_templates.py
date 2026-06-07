"""Tests for the templates and copy-day MCP tools."""
from __future__ import annotations

import json

import httpx
import pytest
import respx
from fastmcp import Client

from tools.templates import templates_server


def make_paginated(results, count=None):
    return {
        "count": count if count is not None else len(results),
        "next": None,
        "previous": None,
        "results": results,
    }


@pytest.fixture
async def mcp_client():
    async with Client(templates_server) as client:
        yield client


# ---------------------------------------------------------------------------
# list_templates
# ---------------------------------------------------------------------------

@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_list_templates_returns_paged_shape(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    templates = [
        {"id": 2, "name": "Push Template", "is_template": True, "is_public": False},
        {"id": 3, "name": "Pull Template", "is_template": True, "is_public": True},
    ]
    respx_mock.get("/templates/").mock(
        return_value=httpx.Response(200, json=make_paginated(templates))
    )
    result = await mcp_client.call_tool("list_templates", {})
    assert result.data["total"] == 2
    assert len(result.data["items"]) == 2
    assert result.data["has_more"] is False


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_list_templates_has_more_when_partial_page(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    templates = [{"id": i, "name": f"T{i}", "is_template": True} for i in range(20)]
    respx_mock.get("/templates/").mock(
        return_value=httpx.Response(200, json=make_paginated(templates, count=35))
    )
    result = await mcp_client.call_tool("list_templates", {"limit": 20})
    assert result.data["has_more"] is True
    assert result.data["total"] == 35


# ---------------------------------------------------------------------------
# list_public_templates
# ---------------------------------------------------------------------------

@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_list_public_templates_returns_paged_shape(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    templates = [{"id": 5, "name": "Community PPL", "is_template": True, "is_public": True}]
    respx_mock.get("/public-templates/").mock(
        return_value=httpx.Response(200, json=make_paginated(templates))
    )
    result = await mcp_client.call_tool("list_public_templates", {})
    assert result.data["total"] == 1
    assert result.data["items"][0]["name"] == "Community PPL"


# ---------------------------------------------------------------------------
# convert_routine_to_template / convert_template_to_routine
# ---------------------------------------------------------------------------

@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_convert_routine_to_template_patches_is_template_true(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    updated = {"id": 1, "name": "My Workout", "is_template": True, "is_public": False}
    route = respx_mock.patch("/routine/1/").mock(
        return_value=httpx.Response(200, json=updated)
    )
    result = await mcp_client.call_tool("convert_routine_to_template", {"routine_id": 1})
    assert route.called
    body = json.loads(route.calls.last.request.content)
    assert body == {"is_template": True}
    assert result.data["is_template"] is True


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_convert_template_to_routine_patches_is_template_false(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    updated = {"id": 2, "name": "temp 1", "is_template": False, "is_public": False}
    route = respx_mock.patch("/routine/2/").mock(
        return_value=httpx.Response(200, json=updated)
    )
    result = await mcp_client.call_tool("convert_template_to_routine", {"routine_id": 2})
    body = json.loads(route.calls.last.request.content)
    assert body == {"is_template": False}
    assert result.data["is_template"] is False


# ---------------------------------------------------------------------------
# set_template_visibility
# ---------------------------------------------------------------------------

@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_set_template_visibility_makes_public(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    updated = {"id": 2, "name": "temp 1", "is_template": True, "is_public": True}
    route = respx_mock.patch("/routine/2/").mock(
        return_value=httpx.Response(200, json=updated)
    )
    result = await mcp_client.call_tool(
        "set_template_visibility", {"routine_id": 2, "is_public": True}
    )
    body = json.loads(route.calls.last.request.content)
    assert body == {"is_public": True}
    assert result.data["is_public"] is True


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_set_template_visibility_makes_private(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    updated = {"id": 2, "name": "temp 1", "is_template": True, "is_public": False}
    route = respx_mock.patch("/routine/2/").mock(
        return_value=httpx.Response(200, json=updated)
    )
    result = await mcp_client.call_tool(
        "set_template_visibility", {"routine_id": 2, "is_public": False}
    )
    body = json.loads(route.calls.last.request.content)
    assert body == {"is_public": False}
    assert result.data["is_public"] is False


# ---------------------------------------------------------------------------
# copy_day_to_routine
# ---------------------------------------------------------------------------

@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_copy_day_to_routine_creates_day_slots_and_entries(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    """
    Source day 3 has 2 slots, each with 1 entry.
    copy_day_to_routine should POST 1 day + 2 slots + 2 entries in the target routine.
    """
    source_day = {"id": 3, "routine": 1, "name": "Legs", "order": 3, "is_rest": False, "type": "custom", "config": None, "description": ""}
    slots = make_paginated([
        {"id": 11, "day": 3, "order": 1, "comment": "", "config": None},
        {"id": 12, "day": 3, "order": 2, "comment": "", "config": None},
    ])
    entries_slot11 = make_paginated([
        {"id": 21, "slot": 11, "exercise": 1627, "type": "normal", "order": 1,
         "comment": "Barbell Squat", "repetition_unit": 1, "weight_unit": 1,
         "repetition_rounding": None, "weight_rounding": None, "config": None},
    ])
    entries_slot12 = make_paginated([
        {"id": 22, "slot": 12, "exercise": 205, "type": "normal", "order": 1,
         "comment": "Reverse Lunge", "repetition_unit": 1, "weight_unit": 1,
         "repetition_rounding": None, "weight_rounding": None, "config": None},
    ])
    new_day = {"id": 10, "routine": 5, "name": "Legs", "order": 1}
    new_slot_1 = {"id": 101, "day": 10, "order": 1}
    new_slot_2 = {"id": 102, "day": 10, "order": 2}
    new_entry_1 = {"id": 201, "slot": 101, "exercise": 1627}
    new_entry_2 = {"id": 202, "slot": 102, "exercise": 205}

    respx_mock.get("/day/3/").mock(return_value=httpx.Response(200, json=source_day))
    respx_mock.get("/slot/").mock(return_value=httpx.Response(200, json=slots))
    respx_mock.get("/slot-entry/").mock(side_effect=[
        httpx.Response(200, json=entries_slot11),
        httpx.Response(200, json=entries_slot12),
    ])
    day_post = respx_mock.post("/day/").mock(return_value=httpx.Response(201, json=new_day))
    slot_post = respx_mock.post("/slot/").mock(side_effect=[
        httpx.Response(201, json=new_slot_1),
        httpx.Response(201, json=new_slot_2),
    ])
    entry_post = respx_mock.post("/slot-entry/").mock(side_effect=[
        httpx.Response(201, json=new_entry_1),
        httpx.Response(201, json=new_entry_2),
    ])

    result = await mcp_client.call_tool(
        "copy_day_to_routine", {"day_id": 3, "target_routine_id": 5}
    )

    assert day_post.called
    assert slot_post.call_count == 2
    assert entry_post.call_count == 2

    # New day should be in target routine
    day_body = json.loads(day_post.calls.last.request.content)
    assert day_body["routine"] == 5
    assert day_body["name"] == "Legs"

    # Result summarises what was created
    assert result.data["new_day_id"] == 10
    assert result.data["slots_copied"] == 2
    assert result.data["entries_copied"] == 2


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_copy_day_to_routine_raises_on_missing_day(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    respx_mock.get("/day/999/").mock(return_value=httpx.Response(404, json={"detail": "Not found."}))
    with pytest.raises(Exception):
        await mcp_client.call_tool("copy_day_to_routine", {"day_id": 999, "target_routine_id": 1})


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_copy_day_to_routine_uses_custom_name(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    source_day = {"id": 3, "routine": 1, "name": "Legs", "order": 3, "is_rest": False, "type": "custom", "config": None, "description": ""}
    respx_mock.get("/day/3/").mock(return_value=httpx.Response(200, json=source_day))
    respx_mock.get("/slot/").mock(return_value=httpx.Response(200, json=make_paginated([])))
    day_post = respx_mock.post("/day/").mock(
        return_value=httpx.Response(201, json={"id": 11, "routine": 5, "name": "Legs v2"})
    )

    await mcp_client.call_tool(
        "copy_day_to_routine",
        {"day_id": 3, "target_routine_id": 5, "new_name": "Legs v2"},
    )

    day_body = json.loads(day_post.calls.last.request.content)
    assert day_body["name"] == "Legs v2"
