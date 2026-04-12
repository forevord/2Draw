"""Unit tests for PDF Agent (PS-09).

generate_pdf tests exercise the real ReportLab renderer (no mocks needed).
upload_to_r2 tests fully mock boto3 to avoid real network calls.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.agents.pdf import generate_pdf, upload_to_r2

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sample_matches() -> list[dict[str, Any]]:
    return [
        {
            "zone_id": 0,
            "paint_name": "Titanium White",
            "brand_name": "Winsor & Newton",
            "paint_hex": "#F5F5F5",
            "delta_e": 1.2,
            "lab_l": 95.0,
            "lab_a": 0.1,
            "lab_b": 0.2,
        },
        {
            "zone_id": 1,
            "paint_name": "Ivory Black",
            "brand_name": "Winsor & Newton",
            "paint_hex": "#1A1A1A",
            "delta_e": 0.8,
            "lab_l": 5.0,
            "lab_a": -0.1,
            "lab_b": -0.2,
        },
    ]


def _sample_manual_results() -> list[dict[str, Any]]:
    return [
        {
            "zone_id": 1,
            "paint_name": "Ivory Black",
            "brand_name": "Winsor & Newton",
            "step": 2,
            "instruction": "Apply in thin layers with a round brush.",
        },
        {
            "zone_id": 0,
            "paint_name": "Titanium White",
            "brand_name": "Winsor & Newton",
            "step": 1,
            "instruction": "Start with a thin wash to establish highlights.",
        },
    ]


def _sample_search_results() -> list[dict[str, Any]]:
    return [
        {
            "zone_id": 0,
            "marketplace": "Amazon.de",
            "paint_name": "Titanium White",
            "url": "https://amazon.de/s?k=Winsor+Titanium+White",
        },
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_pdf_returns_bytes() -> None:
    """generate_pdf() returns non-empty bytes starting with %PDF signature."""
    result = await generate_pdf(
        job_id="test-job-001",
        image_data={},
        matches=_sample_matches(),
        search_results=_sample_search_results(),
        manual_results=_sample_manual_results(),
    )
    assert isinstance(result, bytes)
    assert len(result) > 0
    assert result.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_generate_pdf_with_empty_state() -> None:
    """generate_pdf() with all empty lists still returns a valid PDF."""
    result = await generate_pdf(
        job_id="test-job-empty",
        image_data={},
        matches=[],
        search_results=[],
        manual_results=[],
    )
    assert isinstance(result, bytes)
    assert result.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_upload_to_r2_returns_url() -> None:
    """upload_to_r2() calls boto3 and returns a URL with job_id and .pdf suffix."""
    mock_s3 = MagicMock()
    with patch("app.agents.pdf.boto3.client", return_value=mock_s3):
        url = await upload_to_r2("test-job-001", b"%PDF-fake")
    assert "test-job-001" in url
    assert url.endswith(".pdf")
    mock_s3.put_object.assert_called_once()


@pytest.mark.asyncio
async def test_upload_to_r2_propagates_error() -> None:
    """upload_to_r2() lets exceptions from put_object bubble up."""
    mock_s3 = MagicMock()
    mock_s3.put_object.side_effect = RuntimeError("R2 unavailable")
    with patch("app.agents.pdf.boto3.client", return_value=mock_s3):
        with pytest.raises(RuntimeError, match="R2 unavailable"):
            await upload_to_r2("test-job-002", b"%PDF-fake")
