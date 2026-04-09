"""Image Agent — k-means colour segmentation.

Accepts a JPEG/PNG image (≤ 20 MB), clusters its pixels into N colour zones
using k-means, and returns structured zone data plus a segmented preview PNG.

Uses Pillow for I/O (no opencv dependency) and scikit-learn for k-means.

Typical usage (inside an asyncio context):
    img, labels, centroids, zones = await asyncio.to_thread(
        segment_image, "/tmp/paintsnap/uploads/photo.jpg", 14
    )
    save_segmented_preview(img, labels, centroids, "/tmp/paintsnap/previews/out.png")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

from app.utils.color import hex_to_lab

_MAX_FILE_BYTES = 20 * 1024 * 1024  # 20 MB
_SUBSAMPLE_STEP = 16  # fit k-means on every 16th pixel for speed


def segment_image(
    image_path: str,
    n_clusters: int = 14,
) -> tuple[Any, Any, Any, list[dict[str, Any]]]:
    """Segment an image into ``n_clusters`` colour zones using k-means.

    Args:
        image_path: Absolute path to a JPEG or PNG image (≤ 20 MB).
        n_clusters: Number of colour zones, range 4–24 (default 14).

    Returns:
        ``(img_rgb, labels, centroids_rgb, zones)`` where *zones* is a list
        sorted by ``pixel_count`` descending. Each zone dict contains:
        ``zone_id``, ``hex``, ``lab_l``, ``lab_a``, ``lab_b``,
        ``pixel_count``, ``percentage``.

    Raises:
        ValueError: File not found, unreadable, or exceeds 20 MB.
    """
    path = Path(image_path)
    if not path.exists():
        raise ValueError(f"Image not found: {image_path}")
    if path.stat().st_size > _MAX_FILE_BYTES:
        raise ValueError(f"Image exceeds 20 MB: {image_path}")

    try:
        pil_img = Image.open(str(path)).convert("RGB")
    except Exception as exc:
        raise ValueError(f"Cannot decode image: {image_path}") from exc

    img_rgb: Any = np.array(pil_img, dtype=np.uint8)

    h, w = img_rgb.shape[:2]
    total_pixels: int = h * w

    pixels: Any = img_rgb.reshape(-1, 3).astype(np.float32)
    sample: Any = pixels[::_SUBSAMPLE_STEP]

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    kmeans.fit(sample)
    labels: Any = kmeans.predict(pixels)

    centroids_rgb: Any = kmeans.cluster_centers_.astype(np.uint8)

    zones: list[dict[str, Any]] = []
    for cluster_idx in range(n_clusters):
        pixel_count = int(np.sum(labels == cluster_idx))
        centroid = centroids_rgb[cluster_idx]
        r, g, b = int(centroid[0]), int(centroid[1]), int(centroid[2])
        hex_color = f"#{r:02X}{g:02X}{b:02X}"
        lab_l, lab_a, lab_b = hex_to_lab(hex_color)
        zones.append(
            {
                "zone_id": cluster_idx,  # reassigned after sorting
                "hex": hex_color,
                "lab_l": lab_l,
                "lab_a": lab_a,
                "lab_b": lab_b,
                "pixel_count": pixel_count,
                "percentage": round(pixel_count / total_pixels * 100, 2),
            }
        )

    zones.sort(key=lambda z: z["pixel_count"], reverse=True)
    for i, zone in enumerate(zones):
        zone["zone_id"] = i

    return img_rgb, labels, centroids_rgb, zones


def save_segmented_preview(
    img: Any,
    labels: Any,
    centroids_rgb: Any,
    output_path: str,
) -> None:
    """Write a preview PNG where each pixel is replaced by its cluster colour.

    Args:
        img: Original RGB image array (used for shape only).
        labels: 1-D array of cluster assignments (one per pixel).
        centroids_rgb: ``(n_clusters, 3)`` uint8 array of centroid colours.
        output_path: Absolute path for the output PNG file.
    """
    h, w = img.shape[:2]
    segmented: Any = centroids_rgb[labels].reshape(h, w, 3).astype(np.uint8)
    Image.fromarray(segmented).save(output_path)
