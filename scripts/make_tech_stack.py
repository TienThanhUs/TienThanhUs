#!/usr/bin/env python3
"""Render a terminal-styled Tech Stack & Tools SVG card.

Matches the dark GitHub / neofetch terminal aesthetic (#0d1117 background,
#30363d border, macOS window dots, colored category pills & skill badges).

Usage: python scripts/make_tech_stack.py
Writes tech-stack.svg.
"""
import html
import os

BG = "#0d1117"
PANEL_BG = "#161b22"
BORDER = "#30363d"
DIM = "#8b949e"
FG = "#c9d1d9"
BRIGHT = "#f0f6fc"

W = 908
H = 192

CATEGORIES = [
    (
        "LANGUAGES",
        "#58a6ff",
        [
            ("C++", "#00599C", "⚡"),
            ("Java", "#f89820", "☕"),
            ("JavaScript", "#f7df1e", "JS"),
            ("SQL", "#336791", "DB"),
            ("HTML5 / CSS3", "#e34f26", "</>"),
        ],
    ),
    (
        "BACKEND & FRAMEWORKS",
        "#39d353",
        [
            ("Spring Boot", "#6db33f", "🌱"),
            ("Spring Security", "#6db33f", "🛡️"),
            ("RESTful API", "#39d353", "🔌"),
            ("JWT Auth", "#d63aff", "🔑"),
            ("JPA / Hibernate", "#bcae79", "📦"),
        ],
    ),
    (
        "DEVOPS, DB & TOOLS",
        "#ffa657",
        [
            ("Docker", "#2496ed", "🐳"),
            ("MySQL / PostgreSQL", "#4479a1", "🗄️"),
            ("Git & GitHub", "#f05032", "🌿"),
            ("Maven", "#c71a36", "⚙️"),
            ("Linux / Postman", "#ff6c37", "🚀"),
        ],
    ),
]


def badge_width(label: str, icon: str) -> int:
    # Monospace 12px is ~7.3px per character + icon space + padding
    return int(len(label) * 7.6 + (28 if icon else 14) + 18)


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    anim_css = (
        ""
        if static
        else (
            ".row{opacity:0;transform:translateY(6px);animation:fade .45s ease-out forwards}"
            "@keyframes fade{to{opacity:1;transform:none}}"
        )
    )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="12">',
        f"<style>{anim_css}</style>",
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="8" fill="{BG}" stroke="{BORDER}"/>',
        # Terminal window bar
        f'<circle cx="22" cy="20" r="6" fill="#ff5f57"/>'
        f'<circle cx="42" cy="20" r="6" fill="#febc2e"/>'
        f'<circle cx="62" cy="20" r="6" fill="#28c840"/>',
        f'<text x="{W / 2:.0f}" y="24" text-anchor="middle" fill="{DIM}" font-size="13">'
        f'TienThanhUs@github — ~/tech-stack</text>',
        f'<line x1="1" y1="38" x2="{W - 1}" y2="38" stroke="{BORDER}"/>',
    ]

    y = 62
    for idx, (cat_name, cat_color, items) in enumerate(CATEGORIES):
        delay = 0.15 + idx * 0.14
        parts.append(f'<g class="row" style="animation-delay:{delay:.2f}s">')
        # Category label on the left
        parts.append(
            f'<text x="24" y="{y + 18}" fill="{cat_color}" font-size="11" font-weight="700">'
            f'▸ {html.escape(cat_name)}</text>'
        )

        # Render badges starting at x = 215
        bx = 215
        for label, dot_color, _icon in items:
            bw = int(len(label) * 7.6 + 34)
            bh = 28
            parts.append(
                f'<rect x="{bx}" y="{y}" width="{bw}" height="{bh}" rx="6" '
                f'fill="{PANEL_BG}" stroke="{BORDER}"/>'
            )
            # Colored indicator bar/dot on left of badge
            parts.append(
                f'<circle cx="{bx + 13}" cy="{y + bh / 2:.0f}" r="4.5" fill="{dot_color}"/>'
            )
            parts.append(
                f'<text x="{bx + 24}" y="{y + 18}" fill="{BRIGHT}" font-size="12" font-weight="600">'
                f'{html.escape(label)}</text>'
            )
            bx += bw + 10

        parts.append("</g>")
        y += 44

    parts.append("</svg>")

    with open("tech-stack.svg", "w") as f:
        f.write("\n".join(parts))
    print(f"wrote tech-stack.svg ({W}x{H})")


if __name__ == "__main__":
    main()
