"""Shared async HTTP client for the wger REST API."""
from __future__ import annotations

import os
from typing import Any

import httpx


class WgerClient:
    """
    Async HTTP client for the wger API.

    Reads WGER_BASE_URL and WGER_API_TOKEN from environment.
    """

    def __init__(self) -> None:
        base_url = os.environ["WGER_BASE_URL"].rstrip("/")
        token = os.environ["WGER_API_TOKEN"]
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Token {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(30.0),
        )

    async def __aenter__(self) -> "WgerClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._client.aclose()

    async def get(self, path: str, **params: Any) -> dict[str, Any]:
        """Send a GET request and return parsed JSON."""
        response = await self._client.get(
            path, params={k: v for k, v in params.items() if v is not None}
        )
        response.raise_for_status()
        return response.json()

    async def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        """Send a POST request with JSON body and return parsed JSON."""
        response = await self._client.post(path, json=body)
        response.raise_for_status()
        return response.json()

    async def patch(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        """Send a PATCH request with JSON body and return parsed JSON."""
        response = await self._client.patch(path, json=body)
        response.raise_for_status()
        return response.json()

    async def delete(self, path: str) -> None:
        """Send a DELETE request."""
        response = await self._client.delete(path)
        response.raise_for_status()

    async def paginate(
        self,
        path: str,
        limit: int = 20,
        offset: int = 0,
        **params: Any,
    ) -> tuple[list[dict[str, Any]], int]:
        """Fetch one page. Returns (results, total_count)."""
        data = await self.get(path, limit=limit, offset=offset, **params)
        return data.get("results", []), data.get("count", 0)

    async def paginate_all(
        self,
        path: str,
        max_results: int = 200,
        **params: Any,
    ) -> list[dict[str, Any]]:
        """Auto-paginate all pages up to max_results. Use only for bounded reference data."""
        results: list[dict[str, Any]] = []
        offset = 0
        page_size = 100
        while len(results) < max_results:
            page, total = await self.paginate(
                path,
                limit=min(page_size, max_results - len(results)),
                offset=offset,
                **params,
            )
            results.extend(page)
            if len(results) >= total or not page:
                break
            offset += len(page)
        return results[:max_results]


def get_wger_client() -> WgerClient:
    """Dependency-injection factory for FastMCP's Depends()."""
    return WgerClient()
