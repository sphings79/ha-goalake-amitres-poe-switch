#!/usr/bin/env python3
"""Render the brand icons (icon.png 256, icon@2x.png 512, logo.png, logo@2x.png) of the integration.

A rounded square with the front of a switch: eight ports in a row, two lit, and a PoE bolt above.
Needs Pillow:  .venv/bin/python assets/make_brand_icons.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "custom_components" / "goalake_poe_switch" / "brand"
BG, BODY, PORT, LIT, BOLT = "#0b131d", "#101b28", "#1b2b3d", "#2ae6dc", "#ffb020"


def draw(size: int) -> Image.Image:
    s = size * 4  # supersample for smooth edges
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = s / 24  # design grid: 24 x 24
    d.rounded_rectangle((0, 0, s - 1, s - 1), radius=5 * u, fill=BG)
    # switch body
    d.rounded_rectangle((2.2 * u, 12.2 * u, 21.8 * u, 19.6 * u), radius=1.6 * u, fill=BODY, outline=PORT, width=int(0.35 * u))
    # eight ports, two of them lit
    for i in range(8):
        x = 3.5 * u + i * 2.2 * u
        d.rounded_rectangle((x, 14.4 * u, x + 1.6 * u, 17.4 * u), radius=0.35 * u, fill=LIT if i in (1, 4) else PORT)
    # PoE bolt
    bolt = [(13.2, 2.6), (7.6, 10.2), (11.2, 10.2), (10.2, 15.0 - 3.4), (16.2, 7.4), (12.4, 7.4)]
    d.polygon([(x * u, y * u) for x, y in bolt], fill=BOLT)
    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, size in (("icon.png", 256), ("icon@2x.png", 512), ("logo.png", 256), ("logo@2x.png", 512)):
        draw(size).save(OUT / name, optimize=True)
        print("wrote", OUT / name)


if __name__ == "__main__":
    main()
