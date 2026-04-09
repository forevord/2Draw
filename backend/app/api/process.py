"""Pipeline process API — POST /process and GET /status/{job_id}."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.db.supabase import get_supabase
from app.pipeline.state import PipelineState

router = APIRouter(tags=["pipeline"])


class ProcessRequest(BaseModel):
    upload_id: str


class ProcessResponse(BaseModel):
    job_id: str


class StatusResponse(BaseModel):
    agent: str
    progress: int
    status: str


async def run_pipeline(job_id: str, upload_id: str) -> None:
    """Execute the LangGraph pipeline (background task)."""
    # Local import keeps graph.py out of the import chain during tests
    from app.pipeline.graph import pipeline_graph  # noqa: PLC0415

    initial_state: PipelineState = {
        "job_id": job_id,
        "upload_id": upload_id,
        "current_agent": "image",
        "progress": 0,
        "image_data": None,
        "matches": None,
        "search_results": [],
        "manual_results": [],
        "pdf_url": None,
        "error": None,
    }
    try:
        await pipeline_graph.ainvoke(initial_state)
    except Exception:  # noqa: BLE001
        client = await get_supabase()
        await (
            client.table("jobs")
            .update(
                {
                    "status": "failed",
                    "settings": {"current_agent": "error", "progress": 0},
                }
            )
            .eq("id", job_id)
            .execute()
        )


@router.post("/process", response_model=ProcessResponse)
async def process(
    req: ProcessRequest,
    background_tasks: BackgroundTasks,
) -> ProcessResponse:
    client = await get_supabase()
    result = await (
        client.table("jobs")
        .insert(
            {
                "status": "processing",
                "settings": {
                    "upload_id": req.upload_id,
                    "current_agent": "image",
                    "progress": 0,
                },
            }
        )
        .execute()
    )
    rows = cast(list[dict[str, Any]], result.data)
    job_id: str = rows[0]["id"]
    background_tasks.add_task(run_pipeline, job_id, req.upload_id)
    return ProcessResponse(job_id=job_id)


@router.get("/status/{job_id}", response_model=StatusResponse)
async def status(job_id: str) -> StatusResponse:
    client = await get_supabase()
    result = await (
        client.table("jobs").select("*").eq("id", job_id).execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Job not found")
    rows = cast(list[dict[str, Any]], result.data)
    job: dict[str, Any] = rows[0]
    settings: dict[str, Any] = job.get("settings") or {}
    return StatusResponse(
        agent=str(settings.get("current_agent", "unknown")),
        progress=int(settings.get("progress", 0)),
        status=str(job["status"]),
    )
