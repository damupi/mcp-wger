"""Tests for the workouts MCP tools."""
from __future__ import annotations

import httpx
import pytest
import respx
from fastmcp import Client

from tools.workouts import workouts_server


def make_paginated(results, count=None):
    return {
        "count": count if count is not None else len(results),
        "next": None,
        "previous": None,
        "results": results,
    }


@pytest.fixture
async def mcp_client():
    async with Client(workouts_server) as client:
        yield client


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_list_routines_returns_paged_shape(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    routines = [{"id": 1, "name": "Push Day"}, {"id": 2, "name": "Pull Day"}]
    respx_mock.get("/routine/").mock(
        return_value=httpx.Response(200, json=make_paginated(routines))
    )
    result = await mcp_client.call_tool("list_routines", {})
    assert result.data["total"] == 2
    assert result.data["offset"] == 0
    assert result.data["limit"] == 20
    assert len(result.data["items"]) == 2
    assert result.data["has_more"] is False


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_list_routines_has_more_true_when_total_exceeds_page(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    routines = [{"id": i, "name": f"Routine {i}"} for i in range(20)]
    respx_mock.get("/routine/").mock(
        return_value=httpx.Response(200, json=make_paginated(routines, count=50))
    )
    result = await mcp_client.call_tool("list_routines", {"limit": 20})
    assert result.data["has_more"] is True
    assert result.data["total"] == 50


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_get_routine_returns_routine(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    routine = {"id": 1, "name": "Push Day", "description": "Chest and shoulders"}
    respx_mock.get("/routine/1/").mock(return_value=httpx.Response(200, json=routine))
    result = await mcp_client.call_tool("get_routine", {"routine_id": 1})
    assert result.data["id"] == 1
    assert result.data["name"] == "Push Day"


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_get_routine_raises_on_404(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    respx_mock.get("/routine/999/").mock(
        return_value=httpx.Response(404, json={"detail": "Not found."})
    )
    with pytest.raises(Exception):
        await mcp_client.call_tool("get_routine", {"routine_id": 999})


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_create_routine_posts_name(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    respx_mock.post("/routine/").mock(
        return_value=httpx.Response(201, json={"id": 10, "name": "Legs", "description": ""})
    )
    result = await mcp_client.call_tool("create_routine", {"name": "Legs"})
    assert result.data["id"] == 10
    import json
    body = json.loads(respx_mock.calls.last.request.content)
    assert body["name"] == "Legs"


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_create_routine_includes_description_when_given(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    respx_mock.post("/routine/").mock(
        return_value=httpx.Response(
            201, json={"id": 11, "name": "Cardio", "description": "Morning run"}
        )
    )
    result = await mcp_client.call_tool(
        "create_routine", {"name": "Cardio", "description": "Morning run"}
    )
    assert result.data["description"] == "Morning run"
    import json
    body = json.loads(respx_mock.calls.last.request.content)
    assert body["description"] == "Morning run"


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_log_workout_set_posts_correct_fields(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    respx_mock.post("/workoutlog/").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": 100,
                "exercise": 42,
                "workout": 1,
                "repetitions": 10,
                "weight": "80.00",
                "date": "2026-06-06",
                "reps_unit": 1,
                "weight_unit": 1,
            },
        )
    )
    result = await mcp_client.call_tool(
        "log_workout_set",
        {
            "exercise_id": 42,
            "workout_id": 1,
            "repetitions": 10,
            "weight": 80.0,
            "date": "2026-06-06",
        },
    )
    assert result.data["id"] == 100
    import json
    body = json.loads(respx_mock.calls.last.request.content)
    assert body["exercise"] == 42
    assert body["workout"] == 1
    assert body["repetitions"] == 10
    assert body["weight"] == 80.0


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_log_workout_set_defaults_kg_and_reps(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    respx_mock.post("/workoutlog/").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": 101,
                "exercise": 5,
                "workout": 2,
                "repetitions": 5,
                "weight": "100.00",
                "date": "2026-06-06",
                "reps_unit": 1,
                "weight_unit": 1,
            },
        )
    )
    await mcp_client.call_tool(
        "log_workout_set",
        {
            "exercise_id": 5,
            "workout_id": 2,
            "repetitions": 5,
            "weight": 100.0,
            "date": "2026-06-06",
        },
    )
    import json
    body = json.loads(respx_mock.calls.last.request.content)
    assert body["reps_unit"] == 1
    assert body["weight_unit"] == 1


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_list_workout_logs_filters_by_date(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    logs = [{"id": 1, "date": "2026-06-06", "exercise": 10}]
    respx_mock.get("/workoutlog/").mock(
        return_value=httpx.Response(200, json=make_paginated(logs))
    )
    result = await mcp_client.call_tool("list_workout_logs", {"date": "2026-06-06"})
    assert len(result.data["items"]) == 1
    # Check that date param was sent
    request_url = str(respx_mock.calls.last.request.url)
    assert "date" in request_url


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_list_workout_logs_filters_by_exercise_id(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    logs = [{"id": 2, "date": "2026-06-06", "exercise": 42}]
    respx_mock.get("/workoutlog/").mock(
        return_value=httpx.Response(200, json=make_paginated(logs))
    )
    result = await mcp_client.call_tool("list_workout_logs", {"exercise_id": 42})
    assert len(result.data["items"]) == 1
    request_url = str(respx_mock.calls.last.request.url)
    assert "exercise" in request_url


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_list_training_sessions_returns_paged_shape(
    respx_mock: respx.MockRouter, mcp_client: Client
) -> None:
    sessions = [{"id": 1, "date": "2026-06-06", "workout": 1}]
    respx_mock.get("/workoutsession/").mock(
        return_value=httpx.Response(200, json=make_paginated(sessions))
    )
    result = await mcp_client.call_tool("list_training_sessions", {})
    assert result.data["total"] == 1
    assert len(result.data["items"]) == 1
    assert result.data["has_more"] is False
