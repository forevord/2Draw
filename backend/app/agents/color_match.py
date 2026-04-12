"""Color Match Agent — CIE76 delta-E matching of image zones to paint catalog.

PS-06: For each zone produced by the Image Agent, find the closest paint in the
Supabase catalog using the CIE76 formula:
    ΔE = sqrt((L1-L2)² + (a1-a2)² + (b1-b2)²)

Paints are loaded once per call (≈459 rows) and filtered by region before matching.
The paint catalog is small enough for in-memory nearest-neighbour search.
"""

from __future__ import annotations

import math
from typing import Any, cast

from supabase import AsyncClient


async def match_colors(
    zones: list[dict[str, Any]],
    client: AsyncClient,
    region: str = "eu",
) -> list[dict[str, Any]]:
    """Return one best-matching paint per zone, sorted by zone_id ascending.

    Args:
        zones: Zone dicts from PipelineState["image_data"]["zones"].
               Each must have keys: zone_id, hex, lab_l, lab_a, lab_b.
        client: Async Supabase client (service role).
        region: "eu" | "cis" | "global".  Paints whose region field matches
                *region* or "global" are included.  If region is "global",
                all paints are included.

    Returns:
        List of match dicts (one per zone) with keys:
            zone_id, zone_hex, paint_id, paint_name, brand_id, brand_name,
            paint_hex, delta_e, lab_l, lab_a, lab_b.

    Raises:
        ValueError: If no paints are available after region filtering.
    """
    result = await client.table("paints").select("*, brands(name)").execute()
    paints: list[dict[str, Any]] = cast(list[dict[str, Any]], result.data)

    if region != "global":
        paints = [p for p in paints if p["region"] in (region, "global")]

    if not paints:
        raise ValueError(f"No paints found for region '{region}'")

    matches: list[dict[str, Any]] = []
    for zone in zones:
        zl = float(zone["lab_l"])
        za = float(zone["lab_a"])
        zb = float(zone["lab_b"])

        # Use squared distance in the hot path to avoid sqrt on every candidate.
        best = min(
            paints,
            key=lambda p: (
                (float(p["lab_l"]) - zl) ** 2
                + (float(p["lab_a"]) - za) ** 2
                + (float(p["lab_b"]) - zb) ** 2
            ),
        )
        delta_e = round(
            math.sqrt(
                (float(best["lab_l"]) - zl) ** 2
                + (float(best["lab_a"]) - za) ** 2
                + (float(best["lab_b"]) - zb) ** 2
            ),
            2,
        )
        matches.append(
            {
                "zone_id": zone["zone_id"],
                "zone_hex": zone["hex"],
                "paint_id": best["id"],
                "paint_name": best["name"],
                "brand_id": best["brand_id"],
                "brand_name": best["brands"]["name"],
                "paint_hex": best["hex"],
                "delta_e": delta_e,
                "lab_l": float(best["lab_l"]),
                "lab_a": float(best["lab_a"]),
                "lab_b": float(best["lab_b"]),
            }
        )

    return sorted(matches, key=lambda m: int(m["zone_id"]))
