"""Unit tests for Color Match Agent (PS-06).

All tests are fully mocked — no real Supabase credentials or network calls needed.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.color_match import match_colors

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_paint(
    paint_id: str,
    name: str,
    brand_id: str,
    brand_name: str,
    hex_val: str,
    lab_l: float,
    lab_a: float,
    lab_b: float,
    region: str = "eu",
) -> dict[str, Any]:
    return {
        "id": paint_id,
        "name": name,
        "brand_id": brand_id,
        "brands": {"name": brand_name},
        "hex": hex_val,
        "lab_l": lab_l,
        "lab_a": lab_a,
        "lab_b": lab_b,
        "region": region,
    }


def _make_zone(
    zone_id: int,
    hex_val: str,
    lab_l: float,
    lab_a: float,
    lab_b: float,
) -> dict[str, Any]:
    return {
        "zone_id": zone_id,
        "hex": hex_val,
        "lab_l": lab_l,
        "lab_a": lab_a,
        "lab_b": lab_b,
        "pixel_count": 1000,
        "percentage": 50.0,
    }


def _make_client(paints: list[dict[str, Any]]) -> Any:
    """Build a minimal async Supabase client mock returning the given paints."""
    mock_result = MagicMock()
    mock_result.data = paints

    mock_qb = MagicMock()
    mock_qb.execute = AsyncMock(return_value=mock_result)

    mock_table = MagicMock()
    mock_table.select.return_value = mock_qb

    mock_client = MagicMock()
    mock_client.table.return_value = mock_table
    return mock_client


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_match_colors_returns_one_match_per_zone() -> None:
    """len(matches) == len(zones) — exactly one match per zone."""
    paints = [
        _make_paint("p1", "White", "b1", "W&N", "#FFFFFF", 100.0, 0.0, 0.0),
        _make_paint("p2", "Black", "b1", "W&N", "#000000", 0.0, 0.0, 0.0),
    ]
    zones = [
        _make_zone(0, "#FEFEFE", 99.0, 0.1, 0.1),
        _make_zone(1, "#010101", 1.0, -0.1, -0.1),
    ]
    matches = await match_colors(zones, _make_client(paints))
    assert len(matches) == 2


@pytest.mark.asyncio
async def test_match_colors_selects_closest_by_delta_e() -> None:
    """The paint with the smallest CIE76 delta-E is selected."""
    paints = [
        # Blue: L=32.3, a=79.2, b=-107.9
        _make_paint("p_blue", "Blue", "b1", "W&N", "#0000FF", 32.3, 79.2, -107.9),
        # Red: far from the zone in LAB space
        _make_paint("p_red", "Red", "b1", "W&N", "#FF0000", 53.2, 80.1, 67.2),
    ]
    # Zone close to blue
    zones = [_make_zone(0, "#0000EE", 31.0, 77.0, -105.0)]
    matches = await match_colors(zones, _make_client(paints))
    assert matches[0]["paint_id"] == "p_blue"


@pytest.mark.asyncio
async def test_match_colors_filters_by_region() -> None:
    """With region='eu', a 'cis'-only paint is excluded from candidates."""
    paints = [
        _make_paint(
            "p_eu", "EuPaint", "b1", "W&N", "#FFFFFF", 100.0, 0.0, 0.0, region="eu"
        ),
        _make_paint(
            "p_cis", "CisPaint", "b2", "NP", "#000000", 0.0, 0.0, 0.0, region="cis"
        ),
    ]
    # Zone near CisPaint's LAB — but it should be excluded
    zones = [_make_zone(0, "#000000", 0.0, 0.0, 0.0)]
    matches = await match_colors(zones, _make_client(paints), region="eu")
    assert matches[0]["paint_id"] == "p_eu"


@pytest.mark.asyncio
async def test_match_colors_sorted_by_zone_id() -> None:
    """Output is sorted by zone_id ascending regardless of input order."""
    paints = [_make_paint("p1", "White", "b1", "W&N", "#FFFFFF", 100.0, 0.0, 0.0)]
    zones = [
        _make_zone(2, "#CCCCCC", 80.0, 0.0, 0.0),
        _make_zone(0, "#FFFFFF", 100.0, 0.0, 0.0),
        _make_zone(1, "#888888", 55.0, 0.0, 0.0),
    ]
    matches = await match_colors(zones, _make_client(paints))
    assert [m["zone_id"] for m in matches] == [0, 1, 2]


@pytest.mark.asyncio
async def test_match_result_has_required_fields() -> None:
    """Every match dict contains all 11 required keys."""
    paints = [_make_paint("p1", "White", "b1", "W&N", "#FFFFFF", 100.0, 0.0, 0.0)]
    zones = [_make_zone(0, "#FFFFFF", 100.0, 0.0, 0.0)]
    matches = await match_colors(zones, _make_client(paints))
    required = {
        "zone_id",
        "zone_hex",
        "paint_id",
        "paint_name",
        "brand_id",
        "brand_name",
        "paint_hex",
        "delta_e",
        "lab_l",
        "lab_a",
        "lab_b",
    }
    assert required.issubset(matches[0].keys())
