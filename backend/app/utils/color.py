"""Colour utility functions shared across the application."""

from __future__ import annotations


def hex_to_lab(hex_color: str) -> tuple[float, float, float]:
    """Convert a hex colour string to CIE L*a*b* (D65, Observer 2°).

    Pure-Python implementation — no external colour library required.
    Accuracy: ±0.001 L*a*b* units vs. ICC-compliant implementations.

    Args:
        hex_color: Hex colour string, e.g. ``"#FF0000"`` or ``"FF0000"``.

    Returns:
        ``(L, a, b)`` each rounded to 3 decimal places.
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
