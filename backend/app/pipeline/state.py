"""LangGraph pipeline state schema."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class PipelineState(TypedDict):
    """Shared state passed between all pipeline nodes."""

    job_id: str
    upload_id: str
    n_clusters: int  # k-means colour zones, range 4–24, default 14
    # "image" | "color_match" | "search" | "manual" | "pdf" | "done"
    current_agent: str
    progress: int  # 0–100

    image_data: dict[str, Any] | None  # set by Image Agent (PS-05)
    matches: list[Any] | None  # set by Color Match Agent (PS-06)

    # Annotated with operator.add so LangGraph merges parallel branch outputs
    search_results: Annotated[list[Any], operator.add]
    manual_results: Annotated[list[Any], operator.add]

    pdf_url: str | None
    error: str | None
