"""Unit tests for the Image Agent (PS-05).

All tests are fully offline — no real filesystem I/O.
PIL.Image.open and KMeans are mocked; a real in-memory PIL image is used so
numpy conversion works without additional mocking.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

from app.utils.color import hex_to_lab

# ── hex_to_lab ────────────────────────────────────────────────────────────────


def test_hex_to_lab_matches_known_values() -> None:
    """Verify LAB anchor values for white, black, and primary blue."""
    lab_l, a, b = hex_to_lab("#FFFFFF")
    assert abs(lab_l - 100.0) < 0.1
    assert abs(a) < 0.1
    assert abs(b) < 0.1

    lab_l, a, b = hex_to_lab("#000000")
    assert lab_l == 0.0
    assert a == 0.0
    assert b == 0.0

    lab_l, a, b = hex_to_lab("#0000FF")
    assert abs(lab_l - 32.3) < 1.0  # blue is dark
    assert a > 50.0  # positive a* (magenta shift)
    assert b < -80.0  # strongly negative b* (blue)


# ── helpers ───────────────────────────────────────────────────────────────────


def _make_pil(h: int = 10, w: int = 10) -> Image.Image:
    """Create a tiny black RGB PIL image entirely in memory."""
    return Image.fromarray(np.zeros((h, w, 3), dtype=np.uint8))


def _make_km(n: int, pixel_count: int) -> MagicMock:
    mock_km = MagicMock()
    mock_km.cluster_centers_ = np.zeros((n, 3), dtype=np.float32)
    mock_km.predict.return_value = np.array([i % n for i in range(pixel_count)])
    return mock_km


def _stat(size: int = 1000) -> MagicMock:
    s = MagicMock()
    s.st_size = size
    return s


# ── segment_image tests ───────────────────────────────────────────────────────


def test_segment_image_returns_n_zones() -> None:
    """segment_image must return exactly n_clusters zone dicts."""
    n = 3
    pil_img = _make_pil(10, 10)  # 100 pixels
    mock_km = _make_km(n, 100)
    mock_km.cluster_centers_ = np.array(
        [[255.0, 0.0, 0.0], [0.0, 255.0, 0.0], [0.0, 0.0, 255.0]],
        dtype=np.float32,
    )

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.stat", return_value=_stat()),
        patch("app.agents.image.Image.open", return_value=pil_img),
        patch("app.agents.image.KMeans", return_value=mock_km),
    ):
        from app.agents.image import segment_image

        _, _, _, zones = segment_image("/fake/test.jpg", n_clusters=n)

    assert len(zones) == n


def test_zones_are_sorted_by_pixel_count() -> None:
    """Zones must be ordered largest-first by pixel_count."""
    n = 4
    pil_img = _make_pil(10, 10)  # 100 pixels
    labels = np.array([3] * 50 + [0] * 20 + [1] * 20 + [2] * 10)
    mock_km = MagicMock()
    mock_km.cluster_centers_ = np.zeros((n, 3), dtype=np.float32)
    mock_km.predict.return_value = labels

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.stat", return_value=_stat()),
        patch("app.agents.image.Image.open", return_value=pil_img),
        patch("app.agents.image.KMeans", return_value=mock_km),
    ):
        from app.agents.image import segment_image

        _, _, _, zones = segment_image("/fake/test.jpg", n_clusters=n)

    for i in range(len(zones) - 1):
        assert zones[i]["pixel_count"] >= zones[i + 1]["pixel_count"]


def test_zone_has_required_fields() -> None:
    """Every zone dict must contain all 7 required keys."""
    required: set[str] = {
        "zone_id", "hex", "lab_l", "lab_a", "lab_b", "pixel_count", "percentage"
    }
    n = 2
    pil_img = _make_pil(4, 4)  # 16 pixels
    mock_km = MagicMock()
    mock_km.cluster_centers_ = np.array(
        [[128.0, 64.0, 32.0], [10.0, 20.0, 30.0]], dtype=np.float32
    )
    mock_km.predict.return_value = np.array([i % n for i in range(16)])

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.stat", return_value=_stat()),
        patch("app.agents.image.Image.open", return_value=pil_img),
        patch("app.agents.image.KMeans", return_value=mock_km),
    ):
        from app.agents.image import segment_image

        _, _, _, zones = segment_image("/fake/test.jpg", n_clusters=n)

    for zone in zones:
        assert required == set(zone.keys())


@pytest.mark.asyncio
async def test_segment_image_raises_on_missing_file() -> None:
    """segment_image must raise ValueError when the image path does not exist."""
    import asyncio

    from app.agents.image import segment_image

    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(ValueError, match="Image not found"):
            await asyncio.to_thread(segment_image, "/no/such/file.jpg", 14)


# satisfy F401 for Any (used in annotation only)
_: Any = None
