"""Scrape paint data from brand websites using Firecrawl and write to seeds/*.json.

This is a one-time / periodic refresh script.  Run it whenever you want to
update the seed files with fresh data from the brand websites.

Usage (from backend/ directory):
    uv run python scripts/scrape_paints.py

Requires FIRECRAWL_API_KEY in backend/.env
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).parent.parent
SEEDS_DIR = BACKEND_DIR / "seeds"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings  # noqa: E402

# Brand scrape targets ─────────────────────────────────────────────────────────

SCRAPE_TARGETS: list[dict[str, Any]] = [
    {
        "brand": "Winsor & Newton",
        "output": "winsor_newton.json",
        "urls": [
            "https://www.winsornewton.com/collections/professional-oil-colour",
            "https://www.winsornewton.com/collections/professional-watercolour",
        ],
    },
    {
        "brand": "Liquitex",
        "output": "liquitex.json",
        "urls": [
            "https://www.liquitex.com/us/products/paint/heavy-body-acrylic/",
            "https://www.liquitex.com/us/products/paint/basics-acrylic/",
        ],
    },
    {
        "brand": "Nevskaya Palitra",
        "output": "nevskaya.json",
        "urls": [
            "https://www.nevskaya-palitra.ru/catalog/master-class/",
        ],
    },
]

# Hex colour pattern for extraction from markdown
_HEX_RE = re.compile(r"#([0-9A-Fa-f]{6})\b")
# Color Index Name pattern e.g. PB29, PY35, PR122
_CI_RE = re.compile(r"\b(P[BGYRVOSWN]\d{1,3}(?::\d+)?)\b")


def _parse_markdown(markdown: str) -> list[dict[str, Any]]:
    """Lightweight parser: extract (name, hex, color_index) from Firecrawl markdown.

    Firecrawl returns product pages as structured markdown.  Each product card
    typically has the paint name as a heading and the hex colour either in a
    colour swatch element or as a CSS custom property rendered into the text.

    This parser is intentionally lenient — it extracts what it can and skips
    entries without a valid hex value.  The seed_paints.py seeder also
    validates hex codes before inserting.
    """
    paints: list[dict[str, Any]] = []
    lines = markdown.splitlines()

    current_name: str | None = None
    for line in lines:
        # Heading lines → potential paint name
        if line.startswith("#"):
            stripped = line.lstrip("#").strip()
            # Ignore short section headings (< 4 chars) and nav links
            if len(stripped) > 3 and "[" not in stripped:
                current_name = stripped
            continue

        hexes = _HEX_RE.findall(line)
        if hexes and current_name:
            ci_match = _CI_RE.search(line)
            paints.append(
                {
                    "name": current_name,
                    "hex": f"#{hexes[0].upper()}",
                    "color_index": ci_match.group(1) if ci_match else None,
                }
            )
            current_name = None  # consume — next heading will reset

    # Deduplicate by name (keep first occurrence)
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for p in paints:
        if p["name"] not in seen:
            seen.add(p["name"])
            deduped.append(p)
    return deduped


def _merge_with_existing(
    existing: list[dict[str, Any]],
    scraped: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge scraped data into existing seed, preserving manual entries."""
    by_name = {p["name"]: p for p in existing}
    for p in scraped:
        if p["name"] not in by_name:
            by_name[p["name"]] = p
        else:
            # Update hex/color_index from fresh scrape, keep manual fields
            by_name[p["name"]]["hex"] = p["hex"]
            if p.get("color_index"):
                by_name[p["name"]]["color_index"] = p["color_index"]
    return list(by_name.values())


def _load_existing(path: Path) -> list[dict[str, Any]]:
    if path.exists():
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)  # type: ignore[no-any-return]
    return []


def _write_json(path: Path, data: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def scrape_brand(target: dict[str, Any]) -> list[dict[str, Any]]:
    """Scrape all URLs for a brand and return merged paint list."""
    try:
        from firecrawl import FirecrawlApp  # type: ignore[import-untyped]
    except ImportError:
        print(
            "  ✗  firecrawl-py not installed.  Run: uv pip install -e '.[dev]'",
            file=sys.stderr,
        )
        return []

    if not settings.firecrawl_api_key:
        print(
            "  ✗  FIRECRAWL_API_KEY not set — skipping live scrape.",
            file=sys.stderr,
        )
        return []

    app = FirecrawlApp(api_key=settings.firecrawl_api_key)
    all_paints: list[dict[str, Any]] = []

    for url in target["urls"]:
        print(f"    Scraping {url} …", flush=True)
        try:
            result = app.scrape_url(url, params={"formats": ["markdown"]})
            markdown: str = result.get("markdown", "")
            paints = _parse_markdown(markdown)
            print(f"      → {len(paints)} paint entries extracted")
            all_paints.extend(paints)
        except Exception as exc:  # noqa: BLE001
            print(f"      ⚠  Scrape failed: {exc}", file=sys.stderr)

    return all_paints


def main() -> None:
    SEEDS_DIR.mkdir(parents=True, exist_ok=True)

    for target in SCRAPE_TARGETS:
        brand = target["brand"]
        output_path = SEEDS_DIR / target["output"]
        print(f"\n{brand}")

        scraped = scrape_brand(target)
        existing = _load_existing(output_path)
        merged = _merge_with_existing(existing, scraped)
        _write_json(output_path, merged)

        rel = output_path.relative_to(BACKEND_DIR)
        print(f"  → {len(merged)} paints saved to {rel}")

    print("\nScraping complete.  Run seed_paints.py to push data to Supabase.")


if __name__ == "__main__":
    main()
