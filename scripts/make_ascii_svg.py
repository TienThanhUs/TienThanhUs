#!/usr/bin/env python3
"""Convert source-prepped.png into a self-typing monochrome ASCII SVG.

Each row wipes in left-to-right with a block cursor riding the edge,
staggered top to bottom. SMIL only — GitHub plays it inside <img>.

Usage: python scripts/make_ascii_svg.py [--cols 100]
Writes ascii-portrait.svg.
"""
import html
import sys

import numpy as np
from PIL import Image

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); leading space = blank bg
COLS = 100
CHAR_W = 7.2  # px per glyph at font-size 12 monospace
CHAR_H = 12.6
FG = "#c9d1d9"
BG = "#0d1117"
ROW_WIPE = 0.55  # seconds each row takes to print
ROW_STAGGER = 0.075  # delay between row starts


def main() -> None:
    cols = COLS
    if "--cols" in sys.argv:
        cols = int(sys.argv[sys.argv.index("--cols") + 1])

    img = Image.open("source-prepped.png").convert("L")
    # A monospace cell is ~1.75x taller than wide; correct the aspect
    rows = max(1, round(img.height / img.width * cols * (CHAR_W / CHAR_H)))
    small = np.array(img.resize((cols, rows), Image.LANCZOS), dtype=np.float64)

    idx = ((255 - small) / 255 * (len(RAMP) - 1)).round().astype(int)
    lines = ["".join(RAMP[i] for i in r).rstrip() for r in idx]

    w = round(cols * CHAR_W + 24)
    h = round(rows * CHAR_H + 24)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
        f'font-size="12">',
        f'<rect width="{w}" height="{h}" rx="8" fill="{BG}"/>',
        "<defs>",
    ]
    for i in range(len(lines)):
        begin = i * ROW_STAGGER
        parts.append(
            f'<clipPath id="r{i}"><rect x="0" y="0" width="0" height="{CHAR_H + 2:.1f}">'
            f'<animate attributeName="width" from="0" to="{w}" begin="{begin:.2f}s" '
            f'dur="{ROW_WIPE}s" fill="freeze"/></rect></clipPath>'
        )
    parts.append("</defs>")

    for i, line in enumerate(lines):
        if not line:
            continue
        y = 12 + (i + 1) * CHAR_H - 3
        begin = i * ROW_STAGGER
        parts.append(
            f'<g clip-path="url(#r{i})" transform="translate(12 {y - CHAR_H + 3:.1f})">'
            f'<text x="0" y="{CHAR_H - 3:.1f}" xml:space="preserve" fill="{FG}" '
            f'textLength="{len(line) * CHAR_W:.1f}">{html.escape(line)}</text></g>'
        )
        # Block cursor riding the wipe edge of this row
        parts.append(
            f'<rect x="0" y="{y - CHAR_H + 4:.1f}" width="{CHAR_W:.1f}" height="{CHAR_H:.1f}" '
            f'fill="{FG}" opacity="0">'
            f'<set attributeName="opacity" to="0.9" begin="{begin:.2f}s"/>'
            f'<animate attributeName="x" from="12" to="{w - 14}" begin="{begin:.2f}s" '
            f'dur="{ROW_WIPE}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + ROW_WIPE:.2f}s"/></rect>'
        )

    parts.append("</svg>")
    out = "\n".join(parts)
    with open("ascii-portrait.svg", "w") as f:
        f.write(out)
    print(f"wrote ascii-portrait.svg ({cols}x{rows} chars, {len(out) // 1024} KiB)")


if __name__ == "__main__":
    main()
