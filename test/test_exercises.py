"""Tests for the exercises MCP tools."""
from __future__ import annotations

import httpx
import pytest
import respx
from fastmcp import Client

from tools.exercises import exercises_server


@pytest.fixture
async def mcp_client():
    async with Client(exercises_server) as client:
        yield client


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_list_exercise_categories_returns_all(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    categories = [{"id": 1, "name": "Abs"}, {"id": 2, "name": "Arms"}]
    respx_mock.get("/exercisecategory/").mock(
        return_value=httpx.Response(
            200,
            json={"count": 2, "next": None, "previous": None, "results": categories},
        )
    )
    result = await mcp_client.call_tool("list_exercise_categories", {})
    assert len(result.data) == 2
    assert result.data[0]["name"] == "Abs"


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_list_muscles_returns_all(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    muscles = [{"id": 1, "name_en": "Biceps"}, {"id": 2, "name_en": "Triceps"}]
    respx_mock.get("/muscle/").mock(
        return_value=httpx.Response(
            200,
            json={"count": 2, "next": None, "previous": None, "results": muscles},
        )
    )
    result = await mcp_client.call_tool("list_muscles", {})
    assert len(result.data) == 2
    assert result.data[0]["name_en"] == "Biceps"


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_list_equipment_returns_all(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    equipment = [{"id": 1, "name": "Barbell"}, {"id": 2, "name": "Dumbbell"}]
    respx_mock.get("/equipment/").mock(
        return_value=httpx.Response(
            200,
            json={"count": 2, "next": None, "previous": None, "results": equipment},
        )
    )
    result = await mcp_client.call_tool("list_equipment", {})
    assert len(result.data) == 2
    assert result.data[0]["name"] == "Barbell"


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_search_exercises_by_term(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    translations = [{"id": 1, "exercise": 42, "name": "Squat", "language": 2}]
    respx_mock.get("/exercise-translation/").mock(
        return_value=httpx.Response(
            200,
            json={"count": 1, "next": None, "previous": None, "results": translations},
        )
    )
    result = await mcp_client.call_tool("search_exercises", {"term": "squat"})
    assert result.data["total"] == 1
    assert result.data["items"][0]["name"] == "Squat"


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_search_exercises_has_more_false_when_all_returned(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    translations = [{"id": 1, "exercise": 42, "name": "Squat", "language": 2}]
    respx_mock.get("/exercise-translation/").mock(
        return_value=httpx.Response(
            200,
            json={"count": 1, "next": None, "previous": None, "results": translations},
        )
    )
    result = await mcp_client.call_tool("search_exercises", {"term": "squat"})
    assert result.data["has_more"] is False


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_search_exercises_has_more_true_when_more_pages(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    translations = [{"id": i, "exercise": i, "name": f"Ex{i}", "language": 2} for i in range(20)]
    respx_mock.get("/exercise-translation/").mock(
        return_value=httpx.Response(
            200,
            json={"count": 50, "next": "...", "previous": None, "results": translations},
        )
    )
    result = await mcp_client.call_tool("search_exercises", {"term": "ex", "limit": 20})
    assert result.data["has_more"] is True
    assert result.data["total"] == 50


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_get_exercise_info_returns_detail(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    info = {"id": 42, "translations": [{"name": "Squat"}], "muscles": [{"id": 1}]}
    respx_mock.get("/exerciseinfo/42/").mock(return_value=httpx.Response(200, json=info))
    result = await mcp_client.call_tool("get_exercise_info", {"exercise_id": 42})
    assert result.data["id"] == 42


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_get_exercise_info_raises_on_404(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    respx_mock.get("/exerciseinfo/999/").mock(
        return_value=httpx.Response(404, json={"detail": "Not found."})
    )
    with pytest.raises(Exception):
        await mcp_client.call_tool("get_exercise_info", {"exercise_id": 999})
