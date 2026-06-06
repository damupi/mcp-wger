"""Tests for the nutrition MCP tools."""
from __future__ import annotations

import httpx
import pytest
import respx
from fastmcp import Client

from tools.nutrition import nutrition_server


def make_paginated(results, count=None):
    return {
        "count": count if count is not None else len(results),
        "next": None,
        "previous": None,
        "results": results,
    }


@pytest.fixture
async def mcp_client():
    async with Client(nutrition_server) as client:
        yield client


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_list_nutrition_plans_returns_paged(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    plans = [{"id": 1, "description": "Bulk plan"}, {"id": 2, "description": "Cut plan"}]
    respx_mock.get("/nutritionplan/").mock(
        return_value=httpx.Response(200, json=make_paginated(plans))
    )
    result = await mcp_client.call_tool("list_nutrition_plans", {})
    assert result.data["total"] == 2
    assert len(result.data["items"]) == 2
    assert result.data["items"][0]["description"] == "Bulk plan"
    assert result.data["has_more"] is False


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_get_nutrition_plan_info_returns_nested(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    plan_info = {
        "id": 1,
        "description": "Bulk plan",
        "meals": [
            {
                "id": 1,
                "name": "Breakfast",
                "items": [{"ingredient": 10, "amount": 100}],
            }
        ],
        "energy": 2500,
        "protein": 180,
    }
    respx_mock.get("/nutritionplaninfo/1/").mock(
        return_value=httpx.Response(200, json=plan_info)
    )
    result = await mcp_client.call_tool("get_nutrition_plan_info", {"plan_id": 1})
    assert result.data["id"] == 1
    assert len(result.data["meals"]) == 1
    assert result.data["meals"][0]["name"] == "Breakfast"
    assert result.data["energy"] == 2500


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_search_ingredients_by_term(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    ingredients = [
        {"id": 10, "name": "Chicken breast", "energy": 165},
        {"id": 11, "name": "Chicken thigh", "energy": 209},
    ]
    respx_mock.get("/ingredient/").mock(
        return_value=httpx.Response(200, json=make_paginated(ingredients, count=2))
    )
    result = await mcp_client.call_tool("search_ingredients", {"term": "chicken"})
    assert result.data["total"] == 2
    assert len(result.data["items"]) == 2
    assert result.data["items"][0]["name"] == "Chicken breast"
    request_url = str(respx_mock.calls.last.request.url)
    assert "name" in request_url


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_log_food_diary_entry_posts_required_fields(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    respx_mock.post("/nutritiondiary/").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": 50,
                "plan": 1,
                "ingredient": 10,
                "amount": "150.00",
                "datetime": "2026-06-06T08:00:00",
            },
        )
    )
    result = await mcp_client.call_tool(
        "log_food_diary_entry",
        {
            "plan_id": 1,
            "ingredient_id": 10,
            "amount": 150.0,
            "datetime_str": "2026-06-06T08:00:00",
        },
    )
    assert result.data["id"] == 50
    import json
    body = json.loads(respx_mock.calls.last.request.content)
    assert body["plan"] == 1
    assert body["ingredient"] == 10
    assert body["amount"] == 150.0
    assert body["datetime"] == "2026-06-06T08:00:00"


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_log_food_diary_entry_includes_weight_unit_when_given(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    respx_mock.post("/nutritiondiary/").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": 51,
                "plan": 1,
                "ingredient": 10,
                "amount": "150.00",
                "datetime": "2026-06-06T08:00:00",
                "weight_unit": 2,
            },
        )
    )
    result = await mcp_client.call_tool(
        "log_food_diary_entry",
        {
            "plan_id": 1,
            "ingredient_id": 10,
            "amount": 150.0,
            "datetime_str": "2026-06-06T08:00:00",
            "weight_unit_id": 2,
        },
    )
    assert result.data["id"] == 51
    import json
    body = json.loads(respx_mock.calls.last.request.content)
    assert body["weight_unit"] == 2


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_list_food_diary_filters_by_plan(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    entries = [
        {"id": 1, "plan": 1, "ingredient": 10, "amount": "100.00"},
    ]
    respx_mock.get("/nutritiondiary/").mock(
        return_value=httpx.Response(200, json=make_paginated(entries))
    )
    result = await mcp_client.call_tool("list_food_diary", {"plan_id": 1})
    assert len(result.data["items"]) == 1
    request_url = str(respx_mock.calls.last.request.url)
    assert "plan" in request_url
