"""Search Agent — Marketplace URL builder for matched paints.

PS-07: For each paint match produced by the Color Match Agent, construct
direct search URLs on the target marketplace(s) for the user's region.

Pure function — no I/O, no API calls. One result row per (match × marketplace).

Regions and their marketplaces (from docs/architecture.md):
    eu     → Allegro (PL) + Amazon.de (DE)
    cis    → Wildberries (RU)
    global → Amazon.com (EN)
"""

from __future__ import annotations

import urllib.parse
from typing import Any

# Maps region code → list of (marketplace_display_name, url_template).
# {query} is replaced with urllib.parse.quote_plus("{brand_name} {paint_name}").
_MARKETPLACES: dict[str, list[tuple[str, str]]] = {
    "eu": [
        ("Allegro", "https://allegro.pl/szukaj?string={query}"),
        ("Amazon.de", "https://www.amazon.de/s?k={query}"),
    ],
    "cis": [
        (
            "Wildberries",
            "https://www.wildberries.ru/catalog/0/search.aspx?search={query}",
        ),
    ],
    "global": [
        ("Amazon.com", "https://www.amazon.com/s?k={query}"),
    ],
}


def build_search_results(
    matches: list[dict[str, Any]],
    region: str = "eu",
) -> list[dict[str, Any]]:
    """Return marketplace search URLs for every matched paint.

    Args:
        matches: Match dicts from PipelineState["matches"].
                 Each must have: zone_id, paint_name, brand_name.
        region: "eu" | "cis" | "global".  Unknown values fall back to "eu".

    Returns:
        Flat list of result dicts — one entry per (match × marketplace).
        Each dict has keys: zone_id, paint_name, brand_name, marketplace, url.
    """
    marketplaces = _MARKETPLACES.get(region, _MARKETPLACES["eu"])
    results: list[dict[str, Any]] = []
    for match in matches:
        query = urllib.parse.quote_plus(f"{match['brand_name']} {match['paint_name']}")
        for marketplace_name, url_template in marketplaces:
            results.append(
                {
                    "zone_id": match["zone_id"],
                    "paint_name": match["paint_name"],
                    "brand_name": match["brand_name"],
                    "marketplace": marketplace_name,
                    "url": url_template.format(query=query),
                }
            )
    return results
