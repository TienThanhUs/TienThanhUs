#!/usr/bin/env python3
"""Hand-author the neofetch-style info card SVG.

Each line fades and slides in on a short stagger (CSS keyframes inside
the SVG — GitHub plays them). STATIC=1 emits a frozen frame for Quick Look.

Usage: python scripts/make_info_card.py
Writes info-card.svg.
"""
import html
import os

BG = "#0d1117"
BORDER = "#30363d"
KEY = "#39d353"  # green keys, GitHub-contribution green
VAL = "#c9d1d9"
DIM = "#8b949e"
ACCENT = "#58a6ff"

W = 560
LINE_H = 27
STAGGER = 0.28

TITLE = "you@github"
ROWS = [
    ("", ""),
    ("Name", "Your Name"),
    ("Location", "Your City"),
    ("Role", "What you do"),
    ("", ""),
    ("Built", "Your best project, one line"),
    ("Also", "Other things you make"),
    ("", ""),
    ("Stack", "Your tools"),
    ("Focus", "What drives you"),
    ("", ""),
    ("Contact", "you@example.com"),
]
PALETTE = ["#ff7b72", "#ffa657", "#d29922", "#39d353", "#58a6ff", "#bc8cff", "#f778ba", "#c9d1d9"]


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    # dynamic height: header block + rows (blank rows are shorter) + palette
    blanks = sum(1 for k, v in ROWS if not k and not v)
    lines = len(ROWS) - blanks
    H = round(106 + blanks * LINE_H * 0.45 + lines * LINE_H + 6 + 16 + 24)
    anim_css = "" if static else (
        ".ln{opacity:0;transform:translateX(-8px);"
        "animation:in .45s ease-out forwards}"
        "@keyframes in{to{opacity:1;transform:none}}"
    )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="14">',
        f"<style>{anim_css}</style>",
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="8" fill="{BG}" stroke="{BORDER}"/>',
        # title bar
        f'<circle cx="22" cy="21" r="6" fill="#ff5f57"/>'
        f'<circle cx="42" cy="21" r="6" fill="#febc2e"/>'
        f'<circle cx="62" cy="21" r="6" fill="#28c840"/>',
        f'<text x="{W / 2:.0f}" y="26" text-anchor="middle" fill="{DIM}">{TITLE}</text>',
        f'<line x1="1" y1="40" x2="{W - 1}" y2="40" stroke="{BORDER}"/>',
    ]

    y = 72
    delay = 0.15
    parts.append(
        f'<g class="ln" style="animation-delay:{delay:.2f}s">'
        f'<text x="24" y="{y}" fill="{ACCENT}">{TITLE}</text>'
        f'<text x="24" y="{y + 16}" fill="{DIM}">{"-" * len(TITLE)}</text></g>'
    )
    y += 34
    for key, val in ROWS:
        delay += STAGGER * 0.55
        if not key and not val:
            y += LINE_H * 0.45
            continue
        if key:
            parts.append(
                f'<g class="ln" style="animation-delay:{delay:.2f}s">'
                f'<text x="24" y="{y}"><tspan fill="{KEY}">{html.escape(key)}</tspan>'
                f'<tspan fill="{DIM}">: </tspan>'
                f'<tspan x="130" fill="{VAL}">{html.escape(val)}</tspan></text></g>'
            )
        else:
            parts.append(
                f'<g class="ln" style="animation-delay:{delay:.2f}s">'
                f'<text x="130" y="{y}" fill="{DIM}">{html.escape(val)}</text></g>'
            )
        y += LINE_H

    # classic neofetch palette blocks
    delay += 0.3
    y += 6
    sw = 30
    x0 = (W - sw * len(PALETTE)) / 2
    blocks = "".join(
        f'<rect x="{x0 + i * sw:.0f}" y="{y}" width="{sw}" height="16" fill="{c}"/>'
        for i, c in enumerate(PALETTE)
    )
    parts.append(f'<g class="ln" style="animation-delay:{delay:.2f}s">{blocks}</g>')
    parts.append("</svg>")

    with open("info-card.svg", "w") as f:
        f.write("\n".join(parts))
    print("wrote info-card.svg")


if __name__ == "__main__":
    main()
