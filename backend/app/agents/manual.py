"""Manual Agent — Claude-generated step-by-step painting guide.

PS-08: For each paint match produced by the Color Match Agent, generate a
concise one-sentence practical painting tip. Zones are ordered lightest → darkest
(L* ascending) to define a recommended painting sequence.

Single Anthropic API call for the whole palette — not one per zone.
Fallback on any error: return [], pipeline continues without a manual guide.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)

_MODEL = "claude-haiku-4-5"  # simple structured generation — haiku is sufficient
_MAX_TOKENS = 2048


async def generate_manual(
    matches: list[dict[str, Any]],
    client: AsyncAnthropic,
) -> list[dict[str, Any]]:
    """Return one painting-instruction dict per zone, ordered light-first.

    step=1 is the lightest paint (highest L*).

    Args:
        matches: Match dicts from PipelineState["matches"].
                 Each must have: zone_id, paint_name, brand_name, lab_l, delta_e.
        client:  Async Anthropic client.

    Returns:
        List of dicts with keys: zone_id, paint_name, brand_name, step, instruction.
        Sorted by step (1 = lightest). Returns [] on API error.
    """
    if not matches:
        return []

    # Lightest first (highest L* = white): standard painting sequence
    sorted_matches = sorted(matches, key=lambda m: float(m["lab_l"]), reverse=True)

    palette_lines = "\n".join(
        f"Step {i + 1} — Zone {m['zone_id']}: "
        f'{m["brand_name"]} "{m["paint_name"]}" '
        f"(ΔE={m['delta_e']}, L*={float(m['lab_l']):.1f})"
        for i, m in enumerate(sorted_matches)
    )

    prompt = (
        "You are a painting guide generator for hobby painters.\n"
        "Given the palette below (sorted lightest → darkest), provide a concise "
        "one-sentence practical tip for each step.\n\n"
        "Respond with a JSON array ONLY — no markdown, no prose. Each element:\n"
        '  {"zone_id": <int>, "instruction": "<one-sentence tip>"}\n\n'
        f"Palette:\n{palette_lines}"
    )

    try:
        response = await client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        text_block = next((b for b in response.content if b.type == "text"), None)
        if text_block is None:
            raise ValueError("No text block in response")
        raw = text_block.text
        instructions: list[dict[str, Any]] = json.loads(raw)
    except Exception:
        logger.exception("Manual agent API call failed — returning empty guide")
        return []

    step_map = {m["zone_id"]: i + 1 for i, m in enumerate(sorted_matches)}
    instr_map = {item["zone_id"]: item["instruction"] for item in instructions}

    return [
        {
            "zone_id": m["zone_id"],
            "paint_name": m["paint_name"],
            "brand_name": m["brand_name"],
            "step": step_map[m["zone_id"]],
            "instruction": instr_map.get(
                m["zone_id"], "Apply with a flat brush in thin layers."
            ),
        }
        for m in sorted_matches
    ]
