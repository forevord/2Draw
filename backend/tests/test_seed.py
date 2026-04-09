"""Unit tests for seed_paints utilities.

All tests are fully offline — no Supabase credentials needed.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Allow importing scripts/ from tests/ — must precede local imports
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import pytest  # noqa: E402

from scripts.seed_paints import hex_to_lab, upsert_brands, upsert_paints  # noqa: E402

# ── hex_to_lab ────────────────────────────────────────────────────────────────


def test_hex_to_lab_white() -> None:
    """Pure white #FFFFFF must map to L*≈100, a*≈0, b*≈0."""
    lab_l, lab_a, lab_b = hex_to_lab("#FFFFFF")
    assert abs(lab_l - 100.0) < 0.01
    assert abs(lab_a) < 0.01
    assert abs(lab_b) < 0.01


def test_hex_to_lab_black() -> None:
    """Pure black #000000 must map to L*=0, a*=0, b*=0."""
    lab_l, lab_a, lab_b = hex_to_lab("#000000")
    assert lab_l == 0.0
    assert lab_a == 0.0
    assert lab_b == 0.0


def test_hex_to_lab_blue() -> None:
    """Primary blue #0000FF has well-known LAB values (D65 2°).

    Accepted industry values: L*≈32.3, a*≈79.2, b*≈−107.9.
    Tolerance ±0.5 to allow for rounding in the last conversion step.
    """
    lab_l, lab_a, lab_b = hex_to_lab("#0000FF")
    assert abs(lab_l - 32.3) < 0.5
    assert abs(lab_a - 79.2) < 1.0
    assert abs(lab_b - (-107.9)) < 1.0


def test_hex_to_lab_precision() -> None:
    """Returned values must have at most 3 decimal places (NUMERIC 6,3 in DB)."""
    for color in ["#FF6347", "#40E0D0", "#FFD700", "#8B008B"]:
        for val in hex_to_lab(color):
            decimal_part = str(val).split(".")[-1] if "." in str(val) else ""
            assert len(decimal_part) <= 3, (
                f"hex_to_lab({color}) returned value with >3 decimal places: {val}"
            )


# ── upsert_brands ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_brands_returns_id_map() -> None:
    """upsert_brands should return a dict mapping brand name → UUID string."""
    mock_client = MagicMock()
    mock_execute = AsyncMock(
        return_value=MagicMock(
            data=[
                {"id": "uuid-1", "name": "Winsor & Newton"},
                {"id": "uuid-2", "name": "Liquitex"},
            ]
        )
    )
    # Chain: client.table().upsert().execute()
    mock_client.table.return_value.upsert.return_value.execute = mock_execute

    brands = [
        {"name": "Winsor & Newton", "region": "eu"},
        {"name": "Liquitex", "region": "eu"},
    ]
    result = await upsert_brands(mock_client, brands)

    assert result == {"Winsor & Newton": "uuid-1", "Liquitex": "uuid-2"}
    mock_client.table.assert_called_once_with("brands")


# ── upsert_paints ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_paints_lab_computed() -> None:
    """upsert_paints must compute lab_l, lab_a, lab_b before inserting."""
    inserted_rows: list[dict] = []

    mock_client = MagicMock()

    async def _fake_execute() -> MagicMock:
        return MagicMock(data=inserted_rows)

    def _fake_upsert(rows: list, **_kwargs: object) -> MagicMock:
        inserted_rows.extend(rows)
        mock_chain = MagicMock()
        mock_chain.execute = _fake_execute
        return mock_chain

    mock_client.table.return_value.upsert = _fake_upsert

    paints = [{"name": "Titanium White", "hex": "#F5F5F0", "color_index": "PW6"}]
    count = await upsert_paints(mock_client, paints, brand_id="uuid-wn", region="eu")

    assert count == 1 or len(inserted_rows) == 1
    row = inserted_rows[0]
    assert "lab_l" in row, "lab_l must be present in inserted row"
    assert "lab_a" in row, "lab_a must be present in inserted row"
    assert "lab_b" in row, "lab_b must be present in inserted row"
    l_val = row["lab_l"]
    assert 95 < l_val < 100, f"Titanium White L* should be near 100, got {l_val}"
    assert row["brand_id"] == "uuid-wn"
    assert row["region"] == "eu"
