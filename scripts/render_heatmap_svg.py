#!/usr/bin/env python3
"""Render data/contributions.json as an animated 53-week calendar SVG.

Rounded boxes reveal once with a diagonal line-after-line slide (CSS
keyframes that play on load, then freeze). Less→More legend + stats footer.

Usage: python scripts/render_heatmap_svg.py
Writes contrib-heatmap.svg.
"""
import datetime as dt
import json

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG = "#0d1117"
BORDER = "#30363d"
DIM = "#8b949e"
FG = "#c9d1d9"

CELL = 13
GAP = 3
LEFT = 46  # room for day labels
TOP = 38  # room for month labels
STEP = 0.011  # diagonal stagger per (week+day)


def level_for(day: dict) -> int:
    lvl = day["level"]
    # stretch level 4 days into the neon top end when they're the best days
    return min(lvl + 1, 5) if lvl == 4 else lvl


def main() -> None:
    with open("data/contributions.json") as f:
        data = json.load(f)
    days = data["days"]

    # column = week index, row = weekday (GitHub weeks start Sunday)
    first = dt.date.fromisoformat(days[0]["date"])
    start_week = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    cells, month_marks = [], []
    seen_months = set()
    for d in days:
        date = dt.date.fromisoformat(d["date"])
        week = (date - start_week).days // 7
        row = (date.weekday() + 1) % 7
        cells.append((week, row, level_for(d)))
        if date.day <= 7:
            key = date.strftime("%Y-%m")
            if key not in seen_months:
                seen_months.add(key)
                month_marks.append((week, date.strftime("%b")))

    weeks = max(c[0] for c in cells) + 1
    grid_w = weeks * (CELL + GAP)
    w = LEFT + grid_w + 14
    h = TOP + 7 * (CELL + GAP) + 46

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="12">',
        "<style>"
        ".c{opacity:0;animation:drop .5s ease-out forwards}"
        "@keyframes drop{from{opacity:0;transform:translate(-6px,-6px)}"
        "to{opacity:1;transform:none}}"
        "</style>",
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="8" fill="{BG}" stroke="{BORDER}"/>',
    ]

    for week, label in month_marks:
        parts.append(
            f'<text x="{LEFT + week * (CELL + GAP)}" y="24" fill="{DIM}">{label}</text>'
        )
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(
            f'<text x="10" y="{TOP + row * (CELL + GAP) + CELL - 2}" fill="{DIM}">{label}</text>'
        )

    for week, row, lvl in cells:
        x = LEFT + week * (CELL + GAP)
        y = TOP + row * (CELL + GAP)
        delay = (week + row) * STEP
        parts.append(
            f'<rect class="c" style="animation-delay:{delay:.3f}s" x="{x}" y="{y}" '
            f'width="{CELL}" height="{CELL}" rx="3" fill="{PALETTE[lvl]}"/>'
        )

    # footer: stats left, Less→More legend right
    fy = h - 16
    streak = data["current_streak"]
    stats = f'{data["total"]:,} contributions in the last year'
    if streak > 1:
        stats += f" · {streak}-day streak"
    parts.append(f'<text x="{LEFT}" y="{fy}" fill="{FG}">{stats}</text>')
    lx = w - 14 - 5 * (CELL + GAP) - 78
    parts.append(f'<text x="{lx - 40}" y="{fy}" fill="{DIM}">Less</text>')
    for i in range(5):
        parts.append(
            f'<rect x="{lx + i * (CELL + GAP)}" y="{fy - CELL + 2}" width="{CELL}" '
            f'height="{CELL}" rx="3" fill="{PALETTE[i]}"/>'
        )
    parts.append(f'<text x="{lx + 5 * (CELL + GAP) + 6}" y="{fy}" fill="{DIM}">More</text>')
    parts.append("</svg>")

    with open("contrib-heatmap.svg", "w") as f:
        f.write("\n".join(parts))
    print(f"wrote contrib-heatmap.svg ({weeks} weeks)")


if __name__ == "__main__":
    main()
