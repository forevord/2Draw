"""Unit tests for upload endpoint (PS-10)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

# Minimal valid JPEG: SOI marker + padding
_JPEG_HEADER = b"\xff\xd8\xff\xe0" + b"\x00" * 100
# Minimal valid PNG: signature + padding
_PNG_HEADER = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


@pytest.mark.asyncio
async def test_upload_jpeg_returns_upload_id(client: AsyncClient) -> None:
    """Valid JPEG upload returns 200 with upload_id."""
    resp = await client.post(
        "/api/v1/upload",
        files={"file": ("photo.jpg", _JPEG_HEADER, "image/jpeg")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "upload_id" in body
    assert body["filename"] == "photo.jpg"
    assert body["size"] > 0


@pytest.mark.asyncio
async def test_upload_rejects_non_image(client: AsyncClient) -> None:
    """Non-image content type returns 400."""
    resp = await client.post(
        "/api/v1/upload",
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_upload_rejects_too_large(client: AsyncClient) -> None:
    """File exceeding 20 MB returns 400."""
    big_data = b"\xff\xd8\xff\xe0" + b"\x00" * (20 * 1024 * 1024 + 1)
    resp = await client.post(
        "/api/v1/upload",
        files={"file": ("huge.jpg", big_data, "image/jpeg")},
    )
    assert resp.status_code == 400
