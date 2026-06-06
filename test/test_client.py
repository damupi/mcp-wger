"""Tests for WgerClient HTTP methods and pagination helpers."""
from __future__ import annotations

import httpx
import pytest
import respx

from tools.client import WgerClient


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_get_sends_auth_header(respx_mock: respx.MockRouter) -> None:
    respx_mock.get("/test/").mock(return_value=httpx.Response(200, json={"ok": True}))
    async with WgerClient() as client:
        result = await client.get("/test/")
    assert result == {"ok": True}
    assert respx_mock.calls.last.request.headers["Authorization"] == "Token test-token-12345"


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_paginate_returns_results_and_count(respx_mock: respx.MockRouter) -> None:
    payload = {"count": 5, "next": None, "previous": None, "results": [{"id": 1}, {"id": 2}]}
    respx_mock.get("/items/").mock(return_value=httpx.Response(200, json=payload))
    async with WgerClient() as client:
        results, count = await client.paginate("/items/", limit=2, offset=0)
    assert count == 5
    assert results == [{"id": 1}, {"id": 2}]


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_paginate_all_stops_at_max_results(respx_mock: respx.MockRouter) -> None:
    # Return 3 items per page, total 10, but max_results=5
    page1 = {"count": 10, "next": "...", "previous": None, "results": [{"id": i} for i in range(3)]}
    page2 = {"count": 10, "next": "...", "previous": None, "results": [{"id": i} for i in range(3, 6)]}
    page3 = {"count": 10, "next": None, "previous": None, "results": [{"id": i} for i in range(6, 9)]}
    respx_mock.get("/items/").mock(
        side_effect=[
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
            httpx.Response(200, json=page3),
        ]
    )
    async with WgerClient() as client:
        results = await client.paginate_all("/items/", max_results=5)
    assert len(results) == 5
    assert results[0]["id"] == 0
    assert results[4]["id"] == 4


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_paginate_all_stops_when_no_more_pages(respx_mock: respx.MockRouter) -> None:
    # Only 2 items total, total=2 so should stop after first page
    page1 = {"count": 2, "next": None, "previous": None, "results": [{"id": 1}, {"id": 2}]}
    respx_mock.get("/items/").mock(return_value=httpx.Response(200, json=page1))
    async with WgerClient() as client:
        results = await client.paginate_all("/items/", max_results=200)
    assert len(results) == 2
    assert respx_mock.calls.call_count == 1


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_post_sends_json_body(respx_mock: respx.MockRouter) -> None:
    respx_mock.post("/items/").mock(return_value=httpx.Response(201, json={"id": 99}))
    async with WgerClient() as client:
        result = await client.post("/items/", {"name": "test", "value": 42})
    assert result == {"id": 99}
    import json
    sent_body = json.loads(respx_mock.calls.last.request.content)
    assert sent_body == {"name": "test", "value": 42}


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_delete_sends_delete_request(respx_mock: respx.MockRouter) -> None:
    respx_mock.delete("/items/5/").mock(return_value=httpx.Response(204))
    async with WgerClient() as client:
        await client.delete("/items/5/")
    assert respx_mock.calls.last.request.method == "DELETE"


@pytest.mark.respx(base_url="http://testserver/api/v2")
async def test_patch_sends_patch_request(respx_mock: respx.MockRouter) -> None:
    respx_mock.patch("/items/5/").mock(return_value=httpx.Response(200, json={"id": 5, "name": "updated"}))
    async with WgerClient() as client:
        result = await client.patch("/items/5/", {"name": "updated"})
    assert result == {"id": 5, "name": "updated"}
    import json
    sent_body = json.loads(respx_mock.calls.last.request.content)
    assert sent_body == {"name": "updated"}
