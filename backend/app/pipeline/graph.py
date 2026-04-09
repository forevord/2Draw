"""LangGraph pipeline graph definition.

Topology:
    image → color_match → [search ∥ manual] → pdf → END

Each node is a stub that updates progress and persists to the jobs table.
Downstream tickets (PS-05 … PS-08) will replace stub logic with real agents.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

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
    return {
        "current_agent": "image",
        "progress": _PROGRESS["image"],
        "image_data": {},
    }


async def color_match_node(state: PipelineState) -> dict[str, Any]:
    await _persist(state["job_id"], "color_match", _PROGRESS["color_match"])
    return {
        "current_agent": "color_match",
        "progress": _PROGRESS["color_match"],
        "matches": [],
    }


async def search_node(state: PipelineState) -> dict[str, Any]:
    await _persist(state["job_id"], "search", _PROGRESS["search"])
    return {"search_results": []}


async def manual_node(state: PipelineState) -> dict[str, Any]:
    await _persist(state["job_id"], "manual", _PROGRESS["manual"])
    return {"manual_results": []}


async def pdf_node(state: PipelineState) -> dict[str, Any]:
    client = await get_supabase()
    await (
        client.table("jobs")
        .update(
            {
                "status": "complete",
                "settings": {"current_agent": "done", "progress": _PROGRESS["done"]},
            }
        )
        .eq("id", state["job_id"])
        .execute()
    )
    return {
        "current_agent": "done",
        "progress": _PROGRESS["done"],
        "pdf_url": None,
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
