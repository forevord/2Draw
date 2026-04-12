"""Job results endpoint.

PS-13: Returns the PDF URL and job status for completed jobs.
"""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.supabase import get_supabase

router = APIRouter(tags=["results"])


class ResultsResponse(BaseModel):
    job_id: str
    status: str
    pdf_url: str | None


@router.get("/results/{job_id}", response_model=ResultsResponse)
async def get_results(job_id: str) -> ResultsResponse:
    """Return the PDF URL and status for a completed job."""
    client = await get_supabase()
    result = await (
        client.table("jobs")
        .select("id, status, settings")
        .eq("id", job_id)
        .execute()
    )
    rows = cast(list[dict[str, Any]], result.data)
    if not rows:
        raise HTTPException(status_code=404, detail="Job not found")

    row = rows[0]
    settings: dict[str, Any] = row.get("settings") or {}
    return ResultsResponse(
        job_id=str(row["id"]),
        status=str(row["status"]),
        pdf_url=settings.get("pdf_url"),
    )
