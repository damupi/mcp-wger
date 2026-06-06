"""Tests for the tracking MCP tools."""
from __future__ import annotations

import httpx
import pytest
import respx
from fastmcp import Client

from tools.tracking import tracking_server


def make_paginated(results, count=None):
    return {
        "count": count if count is not None else len(results),
        "next": None,
        "previous": None,
        "results": results,
    }


@pytest.fixture
async def mcp_client():
    async with Client(tracking_server) as client:
        yield client


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_list_weight_entries_returns_paged(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    entries = [
        {"id": 1, "date": "2026-06-01", "weight": "80.50"},
        {"id": 2, "date": "2026-06-06", "weight": "80.10"},
    ]
    respx_mock.get("/weightentry/").mock(
        return_value=httpx.Response(200, json=make_paginated(entries))
    )
    result = await mcp_client.call_tool("list_weight_entries", {})
    assert result.data["total"] == 2
    assert len(result.data["items"]) == 2
    assert result.data["items"][0]["weight"] == "80.50"
    assert result.data["has_more"] is False


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_add_weight_entry_posts_date_and_weight(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    respx_mock.post("/weightentry/").mock(
        return_value=httpx.Response(
            201, json={"id": 10, "date": "2026-06-06", "weight": "79.80"}
        )
    )
    result = await mcp_client.call_tool(
        "add_weight_entry", {"weight": 79.80, "date": "2026-06-06"}
    )
    assert result.data["id"] == 10
    import json
    body = json.loads(respx_mock.calls.last.request.content)
    assert body["weight"] == 79.80
    assert body["date"] == "2026-06-06"


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_list_measurement_categories_returns_all(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    categories = [{"id": 1, "name": "Body Fat"}, {"id": 2, "name": "Chest"}]
    respx_mock.get("/measurement-category/").mock(
        return_value=httpx.Response(
            200,
            json={"count": 2, "next": None, "previous": None, "results": categories},
        )
    )
    result = await mcp_client.call_tool("list_measurement_categories", {})
    assert len(result.data) == 2
    assert result.data[0]["name"] == "Body Fat"


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_list_measurements_filters_by_category(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    measurements = [{"id": 1, "category": 1, "value": "18.5", "date": "2026-06-06"}]
    respx_mock.get("/measurement/").mock(
        return_value=httpx.Response(200, json=make_paginated(measurements))
    )
    result = await mcp_client.call_tool("list_measurements", {"category_id": 1})
    assert len(result.data["items"]) == 1
    assert result.data["items"][0]["value"] == "18.5"
    request_url = str(respx_mock.calls.last.request.url)
    assert "category" in request_url


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_add_measurement_posts_all_fields(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    respx_mock.post("/measurement/").mock(
        return_value=httpx.Response(
            201,
            json={"id": 20, "category": 1, "value": "18.5", "date": "2026-06-06", "notes": "Morning"},
        )
    )
    result = await mcp_client.call_tool(
        "add_measurement",
        {
            "category_id": 1,
            "value": 18.5,
            "date": "2026-06-06",
            "notes": "Morning",
        },
    )
    assert result.data["id"] == 20
    import json
    body = json.loads(respx_mock.calls.last.request.content)
    assert body["category"] == 1
    assert body["value"] == 18.5
    assert body["date"] == "2026-06-06"
    assert body["notes"] == "Morning"
