"""PDF Agent — ReportLab guide generator + Cloudflare R2 uploader.

PS-09: Renders a paint-by-number guide PDF from pipeline state, uploads to R2,
and returns the public URL. Both I/O-bound operations (PDF build, R2 upload) are
run via asyncio.to_thread because ReportLab and boto3 are synchronous.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import date
from io import BytesIO
from typing import Any

import boto3
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

_PAGE_W, _PAGE_H = A4
_MARGIN = 15 * mm


# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------


async def generate_pdf(
    job_id: str,
    image_data: dict[str, Any],
    matches: list[dict[str, Any]],
    search_results: list[dict[str, Any]],
    manual_results: list[dict[str, Any]],
) -> bytes:
    """Render the PDF paint guide in memory and return raw bytes."""
    return await asyncio.to_thread(
        _render_pdf, job_id, image_data, matches, search_results, manual_results
    )


async def upload_to_r2(job_id: str, pdf_bytes: bytes) -> str:
    """Upload PDF to Cloudflare R2 and return the public URL."""
    key = f"guides/{job_id}.pdf"
    await asyncio.to_thread(_sync_upload, pdf_bytes, key)
    return f"{settings.r2_public_url}/{key}"


# ---------------------------------------------------------------------------
# Private sync helpers (for asyncio.to_thread)
# ---------------------------------------------------------------------------


def _color_swatch(hex_color: str) -> Drawing:
    """Return a small Drawing with a filled rectangle for use in a table cell."""
    d = Drawing(14 * mm, 5 * mm)
    try:
        fill = HexColor(hex_color)
    except Exception:
        fill = colors.white
    r = Rect(
        0, 0, 14 * mm, 5 * mm, fillColor=fill, strokeColor=colors.black, strokeWidth=0.5
    )
    d.add(r)
    return d


def _render_pdf(
    job_id: str,
    image_data: dict[str, Any],
    matches: list[dict[str, Any]],
    search_results: list[dict[str, Any]],
    manual_results: list[dict[str, Any]],
) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=_MARGIN,
        rightMargin=_MARGIN,
        topMargin=_MARGIN,
        bottomMargin=_MARGIN,
    )
    styles = getSampleStyleSheet()
    story: list[Any] = []

    # --- Title section ---
    story.append(Paragraph("2Draw Paint Guide", styles["Title"]))
    story.append(Paragraph(f"Job: {job_id}", styles["Normal"]))
    story.append(Paragraph(f"Date: {date.today().isoformat()}", styles["Normal"]))
    story.append(Spacer(1, 6 * mm))

    # --- Optional preview image ---
    preview_path: str = image_data.get("preview_path", "")
    if preview_path and os.path.exists(preview_path):
        max_w = _PAGE_W - 2 * _MARGIN
        story.append(Image(preview_path, width=max_w, height=max_w * 0.5))
        story.append(Spacer(1, 6 * mm))

    # --- Palette table ---
    # Build zone_id → paint_hex lookup from matches
    hex_by_zone: dict[int, str] = {
        m["zone_id"]: str(m.get("paint_hex", "#FFFFFF")) for m in matches
    }

    if manual_results:
        table_data: list[list[Any]] = [
            ["Step", "Swatch", "Paint", "Brand", "ΔE", "Instruction"]
        ]
        for row in sorted(manual_results, key=lambda r: int(r["step"])):
            zid = int(row["zone_id"])
            hex_val = hex_by_zone.get(zid, "#FFFFFF")
            delta_e = next(
                (f"{m['delta_e']:.2f}" for m in matches if m["zone_id"] == zid),
                "—",
            )
            table_data.append(
                [
                    str(row["step"]),
                    _color_swatch(hex_val),
                    str(row["paint_name"]),
                    str(row["brand_name"]),
                    delta_e,
                    Paragraph(str(row["instruction"]), styles["Normal"]),
                ]
            )

        col_widths = [12 * mm, 16 * mm, 36 * mm, 28 * mm, 12 * mm, None]
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2D2D2D")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#F5F5F5")],
                    ),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 8 * mm))

    # --- Buy links section ---
    if search_results:
        story.append(Paragraph("Where to Buy", styles["Heading2"]))
        story.append(Spacer(1, 3 * mm))
        for item in search_results:
            line = (
                f"Zone {item.get('zone_id', '?')} — "
                f"{item.get('marketplace', '')}: "
                f'<link href="{item.get("url", "")}">'
                f"{item.get('paint_name', '')}</link>"
            )
            story.append(Paragraph(line, styles["Normal"]))

    doc.build(story)
    return buf.getvalue()


def _sync_upload(pdf_bytes: bytes, key: str) -> None:
    """Synchronous boto3 upload — called via asyncio.to_thread."""
    s3 = boto3.client(
        "s3",
        endpoint_url=(
            f"https://{settings.cloudflare_account_id}.r2.cloudflarestorage.com"
        ),
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    )
    s3.put_object(
        Bucket=settings.r2_bucket_name,
        Key=key,
        Body=pdf_bytes,
        ContentType="application/pdf",
    )
