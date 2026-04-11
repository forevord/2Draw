"""Unit tests for Search Agent (PS-07).

Pure function — no mocks needed.
"""

from __future__ import annotations

import urllib.parse

from app.agents.search import build_search_results


def _make_match(zone_id: int, paint_name: str, brand_name: str) -> dict:
    return {
        "zone_id": zone_id,
        "paint_name": paint_name,
        "brand_name": brand_name,
        "paint_id": "uuid-1",
        "brand_id": "uuid-b",
        "zone_hex": "#123456",
        "paint_hex": "#123456",
        "delta_e": 1.5,
        "lab_l": 50.0,
        "lab_a": 0.0,
        "lab_b": 0.0,
    }


def test_eu_region_returns_allegro_and_amazon_de() -> None:
    """EU region produces 2 marketplace results per match."""
    matches = [_make_match(0, "Ultramarine Blue", "Winsor & Newton")]
    results = build_search_results(matches, region="eu")
    marketplaces = [r["marketplace"] for r in results]
    assert "Allegro" in marketplaces
    assert "Amazon.de" in marketplaces
    assert len(results) == 2


def test_cis_region_returns_wildberries() -> None:
    """CIS region produces exactly 1 Wildberries result per match."""
    matches = [_make_match(0, "Ultramarine", "Nevskaya Palitra")]
    results = build_search_results(matches, region="cis")
    assert len(results) == 1
    assert results[0]["marketplace"] == "Wildberries"
    assert "wildberries.ru" in results[0]["url"]


def test_query_is_url_encoded() -> None:
    """Paint names with special chars are percent-encoded in the URL."""
    matches = [_make_match(0, "Cadmium Red & Orange", "W&N")]
    results = build_search_results(matches, region="global")
    encoded_query = urllib.parse.quote_plus("W&N Cadmium Red & Orange")
    assert encoded_query in results[0]["url"]


def test_result_has_required_fields() -> None:
    """Every result dict contains all 5 required keys."""
    matches = [_make_match(0, "White", "Liquitex")]
    results = build_search_results(matches, region="eu")
    required = {"zone_id", "paint_name", "brand_name", "marketplace", "url"}
    for r in results:
        assert required.issubset(r.keys())
