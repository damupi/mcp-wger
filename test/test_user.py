"""Tests for the user MCP tools."""
from __future__ import annotations

import httpx
import pytest
import respx
from fastmcp import Client

from tools.user import user_server


@pytest.fixture
async def mcp_client():
    async with Client(user_server) as client:
        yield client


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_get_user_profile_returns_profile(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    profile = {
        "id": 1,
        "username": "athlete",
        "gym": 1,
        "weight_unit": "kg",
        "language": 2,
    }
    respx_mock.get("/userprofile/").mock(
        return_value=httpx.Response(
            200,
            json={"count": 1, "next": None, "previous": None, "results": [profile]},
        )
    )
    result = await mcp_client.call_tool("get_user_profile", {})
    assert result.data["username"] == "athlete"
    assert result.data["weight_unit"] == "kg"


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_get_user_profile_returns_empty_on_no_results(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    respx_mock.get("/userprofile/").mock(
        return_value=httpx.Response(
            200,
            json={"count": 0, "next": None, "previous": None, "results": []},
        )
    )
    result = await mcp_client.call_tool("get_user_profile", {})
    # FastMCP returns None for result.data when the tool returns an empty dict,
    # but structured_content reflects the actual return value.
    assert result.structured_content == {} or result.data is None


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_get_user_statistics_returns_stats(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    stats = {
        "workouts": 42,
        "total_weight_lifted": 15000.0,
        "weight": {"count": 10, "last": "80.50"},
    }
    respx_mock.get("/user-statistics/").mock(
        return_value=httpx.Response(200, json=stats)
    )
    result = await mcp_client.call_tool("get_user_statistics", {})
    assert result.data["workouts"] == 42
    assert result.data["total_weight_lifted"] == 15000.0
