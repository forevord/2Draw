"""Unit tests for the pipeline process API endpoints.

All tests are fully offline — no Supabase credentials or LangGraph execution needed.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


def _mock_supabase(data: list) -> MagicMock:
    """Build a minimal Supabase client mock for a single chained call."""
    mock_execute = AsyncMock(return_value=MagicMock(data=data))
    mock_sb = MagicMock()
    mock_sb.table.return_value.insert.return_value.execute = mock_execute
    select_chain = mock_sb.table.return_value.select.return_value.eq.return_value
    select_chain.execute = mock_execute
    return mock_sb


# ── POST /api/v1/process ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_process_returns_job_id(client: AsyncClient) -> None:
    """POST /process with a valid upload_id must return a job_id."""
    mock_sb = _mock_supabase([{"id": "job-uuid-1"}])
    with (
        patch("app.api.process.get_supabase", AsyncMock(return_value=mock_sb)),
        patch("app.api.process.run_pipeline", AsyncMock()),
    ):
        resp = await client.post("/api/v1/process", json={"upload_id": "upload-abc"})
    assert resp.status_code == 200
    assert resp.json()["job_id"] == "job-uuid-1"


@pytest.mark.asyncio
async def test_process_missing_upload_id(client: AsyncClient) -> None:
    """POST /process without upload_id must return 422 Unprocessable Entity."""
    resp = await client.post("/api/v1/process", json={})
    assert resp.status_code == 422


# ── GET /api/v1/status/{job_id} ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_status_returns_agent_progress(client: AsyncClient) -> None:
    """GET /status/<id> must return agent name and progress from the job row."""
    job_row = {
        "id": "job-uuid-1",
        "status": "processing",
        "settings": {"current_agent": "image", "progress": 10},
    }
    mock_sb = _mock_supabase([job_row])
    with patch("app.api.process.get_supabase", AsyncMock(return_value=mock_sb)):
        resp = await client.get("/api/v1/status/job-uuid-1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["agent"] == "image"
    assert body["progress"] == 10
    assert body["status"] == "processing"


@pytest.mark.asyncio
async def test_status_not_found(client: AsyncClient) -> None:
    """GET /status/<unknown-id> must return 404."""
    mock_sb = _mock_supabase([])
    with patch("app.api.process.get_supabase", AsyncMock(return_value=mock_sb)):
        resp = await client.get("/api/v1/status/no-such-job")
    assert resp.status_code == 404
