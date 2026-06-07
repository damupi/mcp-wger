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


@workouts_server.tool
async def create_training_session(
    date: Annotated[str, "Date of the session (YYYY-MM-DD)"],
    workout_id: Annotated[int, "Workout/routine ID this session belongs to"],
    notes: Annotated[str, "Free-text notes about the session"] = "",
    impression: Annotated[int, "Overall impression: 1=General, 2=Burned out, 3=Good, 4=Excellent"] = 3,
    time_start: Annotated[str | None, "Session start time (HH:MM:SS)"] = None,
    time_end: Annotated[str | None, "Session end time (HH:MM:SS)"] = None,
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """Create a new training session (the header that groups a set of workout logs).

    Call this before log_workout_set() when logging a full training session.
    Returns the created session including its ID, which can be linked to logs.
    """
    payload: dict[str, Any] = {
        "date": date,
        "workout": workout_id,
        "notes": notes,
        "impression": impression,
    }
    if time_start is not None:
        payload["time_start"] = time_start
    if time_end is not None:
        payload["time_end"] = time_end
    async with client:
        return await client.post("/workoutsession/", payload)


@workouts_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def get_routine_structure(
    routine_id: Annotated[int, "Routine ID"],
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """Get the full nested structure of a routine: days → slots → entries + configs.

    Useful for understanding exactly what exercises, sets, reps and weights are
    prescribed in each day of the routine, including progression rules.
    """
    from fastmcp.exceptions import ToolError

    try:
        async with client:
            return await client.get(f"/routine/{routine_id}/structure/")
    except httpx.HTTPStatusError as exc:
        raise ToolError(f"Routine {routine_id} not found: {exc}") from exc


@workouts_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def get_routine_schedule(
    routine_id: Annotated[int, "Routine ID"],
    client: WgerClient = Depends(get_wger_client),
) -> list[dict[str, Any]]:
    """Get the date-by-date training schedule for a routine (display view).

    Returns one entry per date showing which day and exercises are planned.
    Repeated sets of the same exercise are folded together for readability.
    Useful for answering 'what should I train today?' or 'what's this week's plan?'
    """
    from fastmcp.exceptions import ToolError

    try:
        async with client:
            return await client.get(f"/routine/{routine_id}/date-sequence-display/")
    except httpx.HTTPStatusError as exc:
        raise ToolError(f"Routine {routine_id} not found: {exc}") from exc


@workouts_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def get_routine_gym_view(
    routine_id: Annotated[int, "Routine ID"],
    client: WgerClient = Depends(get_wger_client),
) -> list[dict[str, Any]]:
    """Get the date-by-date schedule split into individual sets (gym mode).

    Supersets are interleaved set-by-set (e.g. A1, B1, A2, B2…).
    Use this when guiding a user through a live workout session.
    """
    from fastmcp.exceptions import ToolError

    try:
        async with client:
            return await client.get(f"/routine/{routine_id}/date-sequence-gym/")
    except httpx.HTTPStatusError as exc:
        raise ToolError(f"Routine {routine_id} not found: {exc}") from exc


@workouts_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def get_routine_logs(
    routine_id: Annotated[int, "Routine ID"],
    client: WgerClient = Depends(get_wger_client),
) -> list[dict[str, Any]]:
    """Get all workout sessions and logs for a routine, grouped by session.

    Each entry contains the session (date, notes, impression) and the list
    of individual log entries (exercise, reps, weight, targets).
    """
    from fastmcp.exceptions import ToolError

    try:
        async with client:
            return await client.get(f"/routine/{routine_id}/logs/")
    except httpx.HTTPStatusError as exc:
        raise ToolError(f"Routine {routine_id} not found: {exc}") from exc


@workouts_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def get_routine_stats(
    routine_id: Annotated[int, "Routine ID"],
    client: WgerClient = Depends(get_wger_client),
) -> dict[str, Any]:
    """Get aggregated training statistics for a routine.

    Returns volume (kg moved), set counts, and estimated 1RM (Brzycki formula)
    broken down by day, ISO week, iteration, and exercise.
    Great for tracking progress over time.
    """
    from fastmcp.exceptions import ToolError

    try:
        async with client:
            return await client.get(f"/routine/{routine_id}/stats/")
    except httpx.HTTPStatusError as exc:
        raise ToolError(f"Routine {routine_id} not found: {exc}") from exc
