#!/usr/bin/env python3
"""Render the brand icons (icon.png 256, icon@2x.png 512, logo.png, logo@2x.png) of the integration.

A bright blue rounded square with the front of a switch (eight ports, two lit) and a PoE bolt above.
Needs Pillow:  .venv/bin/python assets/make_brand_icons.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "custom_components" / "goalake_poe_switch" / "brand"
BG_TOP, BG_BOTTOM = (34, 197, 238), (13, 110, 224)  # bright blue gradient
BODY, PORT, LIT, BOLT, BOLT_EDGE = "#ffffff", "#c9d6e4", "#ff8a00", "#ffd23f", "#b86e00"


def draw(size: int) -> Image.Image:
    s = size * 4  # supersample for smooth edges
    u = s / 24  # design grid: 24 x 24
    # vertical gradient background in a rounded square
    gradient = Image.new("RGBA", (s, s))
    gd = ImageDraw.Draw(gradient)
    for y in range(s):
        t = y / (s - 1)
        gd.line([(0, y), (s, y)], fill=tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3)) + (255,))
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, s - 1, s - 1), radius=5 * u, fill=255)
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    img.paste(gradient, (0, 0), mask)
    d = ImageDraw.Draw(img)
    # switch body, white with a soft shadow line
    d.rounded_rectangle((2.2 * u, 14.0 * u, 21.8 * u, 21.4 * u), radius=1.6 * u, fill=(0, 0, 0, 50))
    d.rounded_rectangle((2.2 * u, 13.4 * u, 21.8 * u, 20.8 * u), radius=1.6 * u, fill=BODY)
    # eight ports, two of them lit
    for i in range(8):
        x = 3.5 * u + i * 2.2 * u
        d.rounded_rectangle((x, 15.6 * u, x + 1.6 * u, 18.6 * u), radius=0.35 * u, fill=LIT if i in (1, 4) else PORT)
    # PoE bolt with a dark edge so it stays readable on any background
    bolt = [(13.8, 1.6), (7.2, 9.6), (11.0, 9.6), (9.6, 12.4), (16.8, 6.2), (12.8, 6.2)]
    pts = [(x * u, y * u) for x, y in bolt]
    d.polygon(pts, fill=BOLT, outline=BOLT_EDGE, width=int(0.28 * u))
    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, size in (("icon.png", 256), ("icon@2x.png", 512), ("logo.png", 256), ("logo@2x.png", 512)):
        draw(size).save(OUT / name, optimize=True)
        print("wrote", OUT / name)


if __name__ == "__main__":
    main()
