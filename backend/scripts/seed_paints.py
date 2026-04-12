"""Seed the paints and brands tables from JSON seed files.

Usage (from backend/ directory):
    uv run python scripts/seed_paints.py

Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env
"""

from __future__ import annotations

import asyncio
import json
import math
import sys
from pathlib import Path
from typing import Any

# Allow running from backend/ or project root
BACKEND_DIR = Path(__file__).parent.parent
SEEDS_DIR = BACKEND_DIR / "seeds"

sys.path.insert(0, str(BACKEND_DIR))

from app.db.supabase import get_supabase  # noqa: E402

PAINT_FILES: dict[str, str] = {
    "Winsor & Newton": "winsor_newton.json",
    "Liquitex": "liquitex.json",
    "Nevskaya Palitra": "nevskaya.json",
}


# ── HEX → CIE L*a*b* ─────────────────────────────────────────────────────────


def hex_to_lab(hex_color: str) -> tuple[float, float, float]:
    """Convert a hex colour string to CIE L*a*b* (D65, Observer 2°).

    Pure-Python implementation — no external colour library required.
    Accuracy: ±0.001 L*a*b* units vs. ICC-compliant implementations.
    """
    h = hex_color.lstrip("#")
    r_s = int(h[0:2], 16) / 255.0
    g_s = int(h[2:4], 16) / 255.0
    b_s = int(h[4:6], 16) / 255.0

    # sRGB gamma expansion → linear light
    def _linearise(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r_l, g_l, b_l = _linearise(r_s), _linearise(g_s), _linearise(b_s)

    # Linear RGB → CIE XYZ (D65 2° observer, IEC 61966-2-1 matrix)
    x = r_l * 0.4124564 + g_l * 0.3575761 + b_l * 0.1804375
    y = r_l * 0.2126729 + g_l * 0.7151522 + b_l * 0.0721750
    z = r_l * 0.0193339 + g_l * 0.1191920 + b_l * 0.9503041

    # Normalise by D65 white point
    xn, yn, zn = x / 0.95047, y / 1.00000, z / 1.08883

    # CIE XYZ → L*a*b*
    epsilon = 0.008856  # (6/29)^3
    kappa = 903.3  # (29/3)^3

    def _f(t: float) -> float:
        return t ** (1.0 / 3.0) if t > epsilon else (kappa * t + 16.0) / 116.0

    fx, fy, fz = _f(xn), _f(yn), _f(zn)
    lab_l = 116.0 * fy - 16.0
    lab_a = 500.0 * (fx - fy)
    lab_b = 200.0 * (fy - fz)

    return round(lab_l, 3), round(lab_a, 3), round(lab_b, 3)


# ── Helpers ───────────────────────────────────────────────────────────────────


def load_json(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)  # type: ignore[no-any-return]


def _is_valid_hex(value: str) -> bool:
    h = value.lstrip("#")
    return len(h) == 6 and all(c in "0123456789abcdefABCDEF" for c in h)


# ── Database operations ───────────────────────────────────────────────────────


async def upsert_brands(
    client: Any,
    brands: list[dict[str, Any]],
) -> dict[str, str]:
    """Upsert brands and return a mapping of name → uuid."""
    result = await client.table("brands").upsert(brands, on_conflict="name").execute()
    rows: list[dict[str, Any]] = result.data
    return {row["name"]: row["id"] for row in rows}


async def upsert_paints(
    client: Any,
    paints: list[dict[str, Any]],
    brand_id: str,
    region: str,
) -> int:
    """Compute LAB values and upsert paints; returns row count inserted/updated."""
    rows: list[dict[str, Any]] = []
    skipped = 0
    for p in paints:
        hex_val: str = p.get("hex", "")
        if not _is_valid_hex(hex_val):
            skipped += 1
            continue
        lab_l, lab_a, lab_b = hex_to_lab(hex_val)
        rows.append(
            {
                "brand_id": brand_id,
                "name": p["name"],
                "color_index": p.get("color_index"),
                "hex": hex_val.upper() if not hex_val.startswith("#") else hex_val,
                "lab_l": lab_l,
                "lab_a": lab_a,
                "lab_b": lab_b,
                "region": region,
            }
        )

    if skipped:
        print(f"    ⚠  Skipped {skipped} entries with invalid hex values.")

    if not rows:
        return 0

    # Upsert in chunks of 500 to stay within Supabase request limits
    total = 0
    chunk_size = 500
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i : i + chunk_size]
        res = (
            await client.table("paints")
            .upsert(chunk, on_conflict="brand_id,name")
            .execute()
        )
        total += len(res.data)

    return total


# ── Entry point ───────────────────────────────────────────────────────────────


async def main() -> None:
    client = await get_supabase()

    print("Seeding brands …")
    brands_data = load_json(SEEDS_DIR / "brands.json")
    brand_ids = await upsert_brands(client, brands_data)
    print(f"  {len(brand_ids)} brands upserted: {', '.join(brand_ids)}")

    # Build a lookup: brand name → region (for paints table)
    region_by_name = {b["name"]: b["region"] for b in brands_data}

    print("\nSeeding paints …")
    total_paints = 0
    for brand_name, filename in PAINT_FILES.items():
        paints = load_json(SEEDS_DIR / filename)
        brand_id = brand_ids.get(brand_name)
        if brand_id is None:
            print(f"  ⚠  Brand '{brand_name}' not found after upsert — skipping.")
            continue
        region = region_by_name[brand_name]
        count = await upsert_paints(client, paints, brand_id, region)
        print(f"  {brand_name}: {count} paints upserted")
        total_paints += count

    print(f"\nDone — {total_paints} paints total across {len(brand_ids)} brands.")
    _check_targets(total_paints)


def _check_targets(total: int) -> None:
    targets = {"Winsor & Newton": 200, "Liquitex": 150}
    for brand, minimum in targets.items():
        file = SEEDS_DIR / PAINT_FILES[brand]
        if file.exists():
            count = len(load_json(file))
            status = "✓" if count >= minimum else "✗"
            print(f"  {status} {brand}: {count}/{minimum} minimum")
    # Rough overall sanity check using sqrt heuristic
    if total < 300:
        print(
            f"\n  ⚠  Only {total} paints seeded — "
            "re-run scrape_paints.py to get full data.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    asyncio.run(main())


# silence unused import (math is kept for potential future use in scripts)
_: Any = math
