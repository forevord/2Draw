"""Unit tests for Manual Agent (PS-08).

All tests are fully mocked — no real Anthropic API calls.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.manual import generate_manual

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_match(
    zone_id: int,
    paint_name: str,
    brand_name: str,
    lab_l: float = 50.0,
) -> dict[str, Any]:
    return {
        "zone_id": zone_id,
        "paint_name": paint_name,
        "brand_name": brand_name,
        "paint_id": f"uuid-{zone_id}",
        "brand_id": "uuid-brand",
        "zone_hex": "#AABBCC",
        "paint_hex": "#AABBCC",
        "delta_e": 1.5,
        "lab_l": lab_l,
        "lab_a": 0.0,
        "lab_b": 0.0,
    }


def _make_client(instructions: list[dict[str, Any]]) -> Any:
    """Build a minimal AsyncAnthropic client mock returning the given instructions."""
    mock_text_block = MagicMock()
    mock_text_block.type = "text"
    mock_text_block.text = json.dumps(instructions)

    mock_response = MagicMock()
    mock_response.content = [mock_text_block]

    mock_messages = MagicMock()
    mock_messages.create = AsyncMock(return_value=mock_response)

    mock_client = MagicMock()
    mock_client.messages = mock_messages
    return mock_client


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_returns_one_result_per_match() -> None:
    """len(results) == len(matches)."""
    matches = [
        _make_match(0, "Titanium White", "Winsor & Newton", lab_l=95.0),
        _make_match(1, "Ultramarine Blue", "Winsor & Newton", lab_l=25.0),
        _make_match(2, "Ivory Black", "Winsor & Newton", lab_l=5.0),
    ]
    instructions = [
        {"zone_id": m["zone_id"], "instruction": "Test tip."} for m in matches
    ]
    client = _make_client(instructions)

    results = await generate_manual(matches, client)

    assert len(results) == 3


@pytest.mark.asyncio
async def test_step_assigned_lightest_to_darkest() -> None:
    """Zone with lowest lab_l gets step=1 (painted first)."""
    matches = [
        _make_match(0, "Black", "W&N", lab_l=5.0),
        _make_match(1, "White", "W&N", lab_l=95.0),
    ]
    instructions = [
        {"zone_id": 0, "instruction": "Dark tip."},
        {"zone_id": 1, "instruction": "Light tip."},
    ]
    client = _make_client(instructions)

    results = await generate_manual(matches, client)

    step_by_zone = {r["zone_id"]: r["step"] for r in results}
    # White (lab_l=95) → step 1 (lightest first)
    # Black (lab_l=5) → step 2
    assert step_by_zone[1] == 1
    assert step_by_zone[0] == 2


@pytest.mark.asyncio
async def test_result_has_required_fields() -> None:
    """Every result dict contains all 5 required keys."""
    matches = [_make_match(0, "Cadmium Red", "Liquitex", lab_l=40.0)]
    instructions = [{"zone_id": 0, "instruction": "A useful tip."}]
    client = _make_client(instructions)

    results = await generate_manual(matches, client)

    required = {"zone_id", "paint_name", "brand_name", "step", "instruction"}
    for r in results:
        assert required.issubset(r.keys())


@pytest.mark.asyncio
async def test_fallback_on_api_error() -> None:
    """Any API exception causes generate_manual() to return []."""
    matches = [_make_match(0, "Burnt Sienna", "W&N", lab_l=30.0)]

    mock_messages = MagicMock()
    mock_messages.create = AsyncMock(side_effect=RuntimeError("API unavailable"))
    mock_client = MagicMock()
    mock_client.messages = mock_messages

    results = await generate_manual(matches, mock_client)

    assert results == []
