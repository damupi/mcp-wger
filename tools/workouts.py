"""Workout routines and logging MCP tools."""
from __future__ import annotations

from typing import Annotated, Any

import httpx
from fastmcp import FastMCP
from fastmcp.dependencies import Depends
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from tools.client import WgerClient, get_wger_client

workouts_server = FastMCP("workouts")


class WorkoutLogCreate(BaseModel):
    """Validated payload for creating a workout log entry."""

    exercise: int
    workout: int
    repetitions: int = Field(ge=0)
    weight: float = Field(ge=0.0)
    date: str
    reps_unit: int = 1
    weight_unit: int = 1


def _paged(items: list[dict[str, Any]], total: int, offset: int, limit: int) -> dict[str, Any]:
    """Build a standard paged response dict."""
    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + len(items)) < total,
    }


@workouts_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_routines(
    limit: Annotated[int, "Results per page (1-100)"] = 20,
    offset: Annotated[int, "Pagination offset"] = 0,
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """List workout routines for the authenticated user."""
    async with client:
        items, total = await client.paginate("/routine/", limit=limit, offset=offset)
    return _paged(items, total, offset, limit)


@workouts_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def get_routine(
    routine_id: Annotated[int, "Routine ID to retrieve"],
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """Get a single workout routine by ID."""
    from fastmcp.exceptions import ToolError

    try:
        async with client:
            return await client.get(f"/routine/{routine_id}/")
    except httpx.HTTPStatusError as exc:
        raise ToolError(f"Routine {routine_id} not found: {exc}") from exc


@workouts_server.tool
async def create_routine(
    name: Annotated[str, "Name for the new routine"],
    description: Annotated[str, "Optional description"] = "",
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """Create a new workout routine."""
    async with client:
        return await client.post("/routine/", {"name": name, "description": description})


@workouts_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_workout_logs(
    date: Annotated[str | None, "Filter by date (YYYY-MM-DD)"] = None,
    exercise_id: Annotated[int | None, "Filter by exercise ID"] = None,
    workout_id: Annotated[int | None, "Filter by workout ID"] = None,
    limit: Annotated[int, "Results per page (1-100)"] = 20,
    offset: Annotated[int, "Pagination offset"] = 0,
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """List workout log entries, optionally filtered by date, exercise, or workout."""
    async with client:
        items, total = await client.paginate(
            "/workoutlog/",
            limit=limit,
            offset=offset,
            date=date,
            exercise=exercise_id,
            workout=workout_id,
        )
    return _paged(items, total, offset, limit)


@workouts_server.tool
async def log_workout_set(
    exercise_id: Annotated[int, "Exercise ID"],
    workout_id: Annotated[int, "Workout ID"],
    repetitions: Annotated[int, "Number of repetitions"],
    weight: Annotated[float, "Weight used"],
    date: Annotated[str, "Date of the set (YYYY-MM-DD)"],
    reps_unit: Annotated[int, "Repetition unit (1=Repetitions)"] = 1,
    weight_unit: Annotated[int, "Weight unit (1=kg, 2=lb)"] = 1,
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """Log a completed workout set (exercise + reps + weight)."""
    payload = WorkoutLogCreate(
        exercise=exercise_id,
        workout=workout_id,
        repetitions=repetitions,
        weight=weight,
        date=date,
        reps_unit=reps_unit,
        weight_unit=weight_unit,
    )
    async with client:
        return await client.post("/workoutlog/", payload.model_dump())


@workouts_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_training_sessions(
    limit: Annotated[int, "Results per page (1-100)"] = 20,
    offset: Annotated[int, "Pagination offset"] = 0,
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """List training sessions for the authenticated user."""
    async with client:
        items, total = await client.paginate("/workoutsession/", limit=limit, offset=offset)
    return _paged(items, total, offset, limit)
