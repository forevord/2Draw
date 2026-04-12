"""Unit tests for checkout and webhook endpoints (PS-14)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


def _mock_supabase(
    job_rows: list | None = None,
    export_rows: list | None = None,
) -> MagicMock:
    """Build a Supabase client mock supporting both jobs and exports tables."""
    mock_sb = MagicMock()

    def table_factory(name: str) -> MagicMock:
        mock_table = MagicMock()
        if name == "jobs":
            data = job_rows if job_rows is not None else []
        else:
            data = export_rows if export_rows is not None else []

        mock_execute = AsyncMock(return_value=MagicMock(data=data))

        # SELECT chain: .select().eq().eq().execute()
        eq2 = MagicMock()
        eq2.execute = mock_execute
        eq1 = MagicMock()
        eq1.eq.return_value = eq2
        eq1.execute = mock_execute
        mock_table.select.return_value.eq.return_value = eq1

        # INSERT chain: .insert().execute()
        mock_table.insert.return_value.execute = AsyncMock(
            return_value=MagicMock(
                data=[{"id": "export-uuid-1"}]
            )
        )

        # UPDATE chain: .update().eq().execute()
        mock_table.update.return_value.eq.return_value.execute = (
            mock_execute
        )

        return mock_table

    mock_sb.table.side_effect = table_factory
    return mock_sb


# ── POST /api/v1/checkout ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_checkout_creates_session(client: AsyncClient) -> None:
    """POST /checkout with a complete job returns a session_url."""
    job_rows = [
        {
            "id": "job-uuid-1",
            "status": "complete",
            "settings": {"pdf_url": "https://r2.example.com/test.pdf"},
        }
    ]
    mock_sb = _mock_supabase(job_rows=job_rows)
    mock_session = MagicMock()
    mock_session.id = "cs_test_123"
    mock_session.url = "https://checkout.stripe.com/cs_test_123"

    with (
        patch(
            "app.api.checkout.get_supabase",
            AsyncMock(return_value=mock_sb),
        ),
        patch(
            "app.api.checkout.stripe.checkout.Session.create",
            return_value=mock_session,
        ),
    ):
        resp = await client.post(
            "/api/v1/checkout", json={"job_id": "job-uuid-1"}
        )
    assert resp.status_code == 200
    assert "checkout.stripe.com" in resp.json()["session_url"]


@pytest.mark.asyncio
async def test_checkout_job_not_found(client: AsyncClient) -> None:
    """POST /checkout with unknown job_id returns 404."""
    mock_sb = _mock_supabase(job_rows=[])
    with patch(
        "app.api.checkout.get_supabase",
        AsyncMock(return_value=mock_sb),
    ):
        resp = await client.post(
            "/api/v1/checkout", json={"job_id": "no-such-job"}
        )
    assert resp.status_code == 404


# ── POST /api/v1/webhook/stripe ─────────────────────────────────


@pytest.mark.asyncio
async def test_webhook_marks_paid(client: AsyncClient) -> None:
    """Valid checkout.session.completed event marks export as paid."""
    event_payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "customer_details": {"email": "user@example.com"},
                "metadata": {
                    "export_id": "export-uuid-1",
                    "job_id": "job-uuid-1",
                },
            }
        },
    }
    mock_sb = _mock_supabase(export_rows=[{"id": "export-uuid-1"}])
    with (
        patch(
            "app.api.webhook.get_supabase",
            AsyncMock(return_value=mock_sb),
        ),
        patch(
            "app.api.webhook.stripe.Webhook.construct_event",
            return_value=event_payload,
        ),
    ):
        resp = await client.post(
            "/api/v1/webhook/stripe",
            content=b"raw-body",
            headers={"stripe-signature": "test-sig"},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
