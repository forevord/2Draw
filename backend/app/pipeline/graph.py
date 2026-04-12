"""LangGraph pipeline graph definition.

Topology:
    image → color_match → [search ∥ manual] → pdf → END

PS-05: image_node — k-means segmentation.
PS-06: color_match_node — CIE76 delta-E paint matching.
PS-07: search_node — marketplace URL builder.
PS-08: manual_node — Claude painting guide.
PS-09: pdf_node — ReportLab render + R2 upload.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from anthropic import AsyncAnthropic
from langgraph.graph import END, StateGraph

from app.agents.color_match import match_colors
from app.agents.image import save_segmented_preview, segment_image
from app.agents.manual import generate_manual
from app.agents.pdf import generate_pdf, upload_to_r2
from app.agents.search import build_search_results
from app.core.config import settings
from app.db.supabase import get_supabase
from app.pipeline.state import PipelineState

# Progress milestones per agent
_PROGRESS: dict[str, int] = {
    "image": 10,
    "color_match": 30,
    "search": 60,
    "manual": 60,
    "pdf": 90,
    "done": 100,
}


async def _persist(job_id: str, agent: str, progress: int) -> None:
    """Write current agent + progress to the jobs table."""
    client = await get_supabase()
    await (
        client.table("jobs")
        .update({"settings": {"current_agent": agent, "progress": progress}})
        .eq("id", job_id)
        .execute()
    )


async def image_node(state: PipelineState) -> dict[str, Any]:
    await _persist(state["job_id"], "image", _PROGRESS["image"])
    upload_path = Path("/tmp/paintsnap/uploads") / state["upload_id"]
    img, labels, centroids, zones = await asyncio.to_thread(
        segment_image, str(upload_path), state["n_clusters"]
    )
    preview_dir = Path("/tmp/paintsnap/previews")
    preview_dir.mkdir(parents=True, exist_ok=True)
    preview_path = preview_dir / f"{state['job_id']}_preview.png"
    save_segmented_preview(img, labels, centroids, str(preview_path))
    return {
        "current_agent": "image",
        "progress": _PROGRESS["image"],
        "image_data": {"zones": zones, "preview_path": str(preview_path)},
    }


async def color_match_node(state: PipelineState) -> dict[str, Any]:
    await _persist(state["job_id"], "color_match", _PROGRESS["color_match"])
    client = await get_supabase()
    zones: list[dict[str, Any]] = (state["image_data"] or {}).get("zones", [])
    matches = await match_colors(zones, client, state["region"])
    return {
        "current_agent": "color_match",
        "progress": _PROGRESS["color_match"],
        "matches": matches,
    }


async def search_node(state: PipelineState) -> dict[str, Any]:
    await _persist(state["job_id"], "search", _PROGRESS["search"])
    matches: list[dict[str, Any]] = state["matches"] or []
    results = build_search_results(matches, state["region"])
    return {"search_results": results}


async def manual_node(state: PipelineState) -> dict[str, Any]:
    await _persist(state["job_id"], "manual", _PROGRESS["manual"])
    matches: list[dict[str, Any]] = state["matches"] or []
    anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    results = await generate_manual(matches, anthropic_client)
    return {"manual_results": results}


async def pdf_node(state: PipelineState) -> dict[str, Any]:
    await _persist(state["job_id"], "pdf", _PROGRESS["pdf"])
    pdf_bytes = await generate_pdf(
        job_id=state["job_id"],
        image_data=state["image_data"] or {},
        matches=state["matches"] or [],
        search_results=state["search_results"],
        manual_results=state["manual_results"],
    )
    pdf_url = await upload_to_r2(state["job_id"], pdf_bytes)
    client = await get_supabase()
    await (
        client.table("jobs")
        .update(
            {
                "status": "complete",
                "settings": {
                    "current_agent": "done",
                    "progress": _PROGRESS["done"],
                    "pdf_url": pdf_url,
                },
            }
        )
        .eq("id", state["job_id"])
        .execute()
    )
    return {
        "current_agent": "done",
        "progress": _PROGRESS["done"],
        "pdf_url": pdf_url,
    }


def _build_graph() -> Any:
    g: Any = StateGraph(PipelineState)

    g.add_node("image", image_node)
    g.add_node("color_match", color_match_node)
    g.add_node("search", search_node)
    g.add_node("manual", manual_node)
    g.add_node("pdf", pdf_node)

    g.set_entry_point("image")
    g.add_edge("image", "color_match")
    # Fan-out: color_match triggers search and manual in parallel
    g.add_edge("color_match", "search")
    g.add_edge("color_match", "manual")
    # Fan-in: both parallel branches converge on pdf
    g.add_edge("search", "pdf")
    g.add_edge("manual", "pdf")
    g.add_edge("pdf", END)

    return g.compile()


pipeline_graph: Any = _build_graph()
