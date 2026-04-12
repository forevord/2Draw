"""Unit tests for results endpoint (PS-13, PS-14)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


def _mock_supabase(
    job_rows: list,
    export_rows: list | None = None,
) -> MagicMock:
    """Mock supporting both jobs and exports table queries."""
    mock_sb = MagicMock()

    def table_factory(name: str) -> MagicMock:
        mock_table = MagicMock()
        data = job_rows if name == "jobs" else (export_rows or [])
        mock_execute = AsyncMock(return_value=MagicMock(data=data))
        # .select().eq().eq().execute()
        eq2 = MagicMock()
        eq2.execute = mock_execute
        eq1 = MagicMock()
        eq1.eq.return_value = eq2
        eq1.execute = mock_execute
        mock_table.select.return_value.eq.return_value = eq1
        return mock_table

    mock_sb.table.side_effect = table_factory
    return mock_sb


@pytest.mark.asyncio
async def test_results_returns_pdf_url_when_paid(
    client: AsyncClient,
) -> None:
    """GET /results/<id> returns pdf_url when export is paid."""
    job_row = {
        "id": "job-uuid-1",
        "status": "complete",
        "settings": {"pdf_url": "https://r2.example.com/guides/job-uuid-1.pdf"},
    }
    export_row = {"status": "paid"}
    mock_sb = _mock_supabase([job_row], [export_row])
    with patch(
        "app.api.results.get_supabase",
        AsyncMock(return_value=mock_sb),
    ):
        resp = await client.get("/api/v1/results/job-uuid-1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == "job-uuid-1"
    assert body["paid"] is True
    assert body["pdf_url"] is not None


@pytest.mark.asyncio
async def test_results_hides_pdf_when_unpaid(
    client: AsyncClient,
) -> None:
    """GET /results/<id> returns paid=false and pdf_url=null when unpaid."""
    job_row = {
        "id": "job-uuid-2",
        "status": "complete",
        "settings": {"pdf_url": "https://r2.example.com/guides/job-uuid-2.pdf"},
    }
    mock_sb = _mock_supabase([job_row], [])
    with patch(
        "app.api.results.get_supabase",
        AsyncMock(return_value=mock_sb),
    ):
        resp = await client.get("/api/v1/results/job-uuid-2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["paid"] is False
    assert body["pdf_url"] is None


@pytest.mark.asyncio
async def test_results_not_found(client: AsyncClient) -> None:
    """GET /results/<unknown-id> returns 404."""
    mock_sb = _mock_supabase([])
    with patch(
        "app.api.results.get_supabase",
        AsyncMock(return_value=mock_sb),
    ):
        resp = await client.get("/api/v1/results/no-such-job")
    assert resp.status_code == 404
