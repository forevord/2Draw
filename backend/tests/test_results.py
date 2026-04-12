"""Unit tests for results endpoint (PS-13)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


def _mock_supabase(data: list) -> MagicMock:
    mock_execute = AsyncMock(return_value=MagicMock(data=data))
    mock_sb = MagicMock()
    select_chain = mock_sb.table.return_value.select.return_value.eq.return_value
    select_chain.execute = mock_execute
    return mock_sb


@pytest.mark.asyncio
async def test_results_returns_pdf_url(client: AsyncClient) -> None:
    """GET /results/<id> returns pdf_url from settings JSONB."""
    job_row = {
        "id": "job-uuid-1",
        "status": "complete",
        "settings": {"pdf_url": "https://r2.example.com/guides/job-uuid-1.pdf"},
    }
    mock_sb = _mock_supabase([job_row])
    with patch("app.api.results.get_supabase", AsyncMock(return_value=mock_sb)):
        resp = await client.get("/api/v1/results/job-uuid-1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == "job-uuid-1"
    assert body["status"] == "complete"
    assert body["pdf_url"] == "https://r2.example.com/guides/job-uuid-1.pdf"


@pytest.mark.asyncio
async def test_results_not_found(client: AsyncClient) -> None:
    """GET /results/<unknown-id> returns 404."""
    mock_sb = _mock_supabase([])
    with patch("app.api.results.get_supabase", AsyncMock(return_value=mock_sb)):
        resp = await client.get("/api/v1/results/no-such-job")
    assert resp.status_code == 404
