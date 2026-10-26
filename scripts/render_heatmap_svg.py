#!/usr/bin/env python3
"""Render data/contributions.json as an animated LeetCode dashboard + 53-week calendar SVG.

Top panel:
- Multi-segment Donut chart showing total solved problems & Easy/Medium/Hard distribution
- Difficulty progress bars (Easy #00b8a3, Medium #ffc01e, Hard #ff375f) with solved/total & %
- Activity metrics grid (Submissions, Active Days, Streaks, Best Day)

Bottom panel:
- Rounded 53-week heatmap calendar with diagonal staggered drop animation
- Less -> More legend + summary footer

Usage: python scripts/render_heatmap_svg.py
Writes contrib-heatmap.svg.
"""
import datetime as dt
import html
import json
import math
import os

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG = "#0d1117"
PANEL_BG = "#161b22"
BORDER = "#30363d"
DIM = "#8b949e"
FG = "#c9d1d9"
BRIGHT = "#f0f6fc"

EASY_C = "#00b8a3"
EASY_BG = "#0e332e"
MED_C = "#ffc01e"
MED_BG = "#3d3113"
HARD_C = "#ff375f"
HARD_BG = "#3d1721"

CELL = 13
GAP = 3
LEFT = 46  # room for day labels
DASH_H = 196  # height of top dashboard section
TOP = DASH_H + 34  # room for month labels below divider
STEP = 0.011  # diagonal stagger per (week+day)


def level_for(day: dict) -> int:
    lvl = day["level"]
    return min(lvl + 1, 5) if lvl == 4 else lvl


def render_donut(cx: float, cy: float, r: float, probs: dict) -> list[str]:
    circ = 2 * math.pi * r
    all_s = probs.get("all", {}).get("solved", 0)
    all_t = probs.get("all", {}).get("total", 1) or 1
    easy_s = probs.get("easy", {}).get("solved", 0)
    med_s = probs.get("medium", {}).get("solved", 0)
    hard_s = probs.get("hard", {}).get("solved", 0)

    out = [
        # Base track
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#21262d" stroke-width="10"/>'
    ]

    # Segment lengths proportional to solved problems so the ring shows the full breakdown cleanly,
    # while filling ~78% of the ring for aesthetic balance (or proportional if desired).
    # Let's make the colored segments represent the breakdown across 82% of the circle (with small gaps),
    # or exact difficulty shares of the solved count!
    total_solved = max(easy_s + med_s + hard_s, 1)
    usable_circ = circ * 0.88  # leave small breathing room for rounded caps
    gap = 10.0

    segments = [
        (easy_s, EASY_C, 0.15),
        (med_s, MED_C, 0.30),
        (hard_s, HARD_C, 0.45),
    ]
    offset = 0.0
    for count, color, delay in segments:
        if count <= 0:
            continue
        seg_len = max(4.0, (count / total_solved) * (usable_circ - gap * 2))
        out.append(
            f'<circle class="seg" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" '
            f'stroke-width="10" stroke-linecap="round" '
            f'stroke-dasharray="{seg_len:.1f} {circ:.1f}" '
            f'stroke-dashoffset="{-offset:.1f}" '
            f'transform="rotate(-90 {cx} {cy})" '
            f'style="animation-delay:{delay:.2f}s"/>'
        )
        offset += seg_len + gap

    # Center text
    out.append(
        f'<text x="{cx}" y="{cy - 4}" text-anchor="middle" fill="{BRIGHT}" '
        f'font-size="26" font-weight="700">{all_s}</text>'
    )
    out.append(
        f'<text x="{cx}" y="{cy + 15}" text-anchor="middle" fill="{DIM}" '
        f'font-size="11">/ {all_t:,}</text>'
    )
    out.append(
        f'<text x="{cx}" y="{cy + 31}" text-anchor="middle" fill="#39d353" '
        f'font-size="10" font-weight="600">✓ SOLVED</text>'
    )
    return out


def render_diff_bars(x0: float, y0: float, bar_w: float, probs: dict) -> list[str]:
    all_s = max(probs.get("all", {}).get("solved", 0), 1)
    rows = [
        ("Easy", "easy", EASY_C, EASY_BG, 0.20),
        ("Medium", "medium", MED_C, MED_BG, 0.32),
        ("Hard", "hard", HARD_C, HARD_BG, 0.44),
    ]
    out = []
    for idx, (label, key, color, track_c, delay) in enumerate(rows):
        y = y0 + idx * 44
        s = probs.get(key, {}).get("solved", 0)
        t = probs.get(key, {}).get("total", 1) or 1
        share_pct = s / all_s * 100
        # Visual bar width scaled by share of solved problems (with a minimum so Hard is clearly visible)
        # Or scaled against total? In LeetCode's new UI, bar shows solved/total, wait: 6/986 is 0.6% (1.6px).
        # Let's show a dual-layer bar: bright bar = share of user's solved problems (or boosted scale),
        # and display both `solved / total` and `(share_pct% of solved)`!
        # Even better: scale bar by `solved / total` with a generous visual curve or relative to max solved difficulty,
        # so Easy (37), Medium (59), Hard (6) look visually proportional to each other!
        fill_ratio = min(1.0, s / max(all_s, 1))
        fill_w = max(6.0, bar_w * fill_ratio) if s > 0 else 0.0

        out.append(f'<g class="fade" style="animation-delay:{delay:.2f}s">')
        out.append(
            f'<text x="{x0}" y="{y}" fill="{color}" font-size="13" font-weight="600">{label}</text>'
        )
        out.append(
            f'<text x="{x0 + bar_w}" y="{y}" text-anchor="end" fill="{BRIGHT}" font-size="13" font-weight="600">'
            f'{s} <tspan fill="{DIM}" font-weight="400" font-size="12">/ {t:,}</tspan>'
            f'<tspan fill="{DIM}" font-weight="400" font-size="11"> ({share_pct:.0f}%)</tspan></text>'
        )
        # Background track
        out.append(
            f'<rect x="{x0}" y="{y + 8}" width="{bar_w}" height="8" rx="4" fill="{track_c}"/>'
        )
        if fill_w > 0:
            out.append(
                f'<rect x="{x0}" y="{y + 8}" width="{fill_w:.1f}" height="8" rx="4" fill="{color}"/>'
            )
        out.append("</g>")
    return out


def render_stat_boxes(x0: float, y0: float, data: dict) -> list[str]:
    total_sub = data.get("total", 0)
    active_days = data.get("total_active_days") or sum(1 for d in data.get("days", []) if d.get("count", 0) > 0)
    cur_streak = data.get("current_streak", 0)
    max_streak = data.get("longest_streak", 0)
    best = data.get("best_day", {"date": "-", "count": 0})
    best_date_str = best.get("date", "-")
    try:
        best_date_fmt = dt.date.fromisoformat(best_date_str).strftime("%b %d, %Y")
    except ValueError:
        best_date_fmt = best_date_str

    cards = [
        ("SUBMISSIONS (1Y)", f"{total_sub:,}", "Total accepted & tried", "#58a6ff", 0, 0),
        ("ACTIVE DAYS", f"{active_days}", "Days with submissions", "#39d353", 1, 0),
        ("STREAK", f"{cur_streak}d", f"Longest: {max_streak} days", "#ffa657", 0, 1),
        ("BEST DAY", f"{best.get('count', 0)} subs", best_date_fmt, "#bc8cff", 1, 1),
    ]
    box_w = 152
    box_h = 58
    gap_x = 12
    gap_y = 12
    out = []
    for title, val, sub, accent, col, row in cards:
        bx = x0 + col * (box_w + gap_x)
        by = y0 + row * (box_h + gap_y)
        delay = 0.25 + (col + row) * 0.1
        out.append(f'<g class="fade" style="animation-delay:{delay:.2f}s">')
        out.append(
            f'<rect x="{bx}" y="{by}" width="{box_w}" height="{box_h}" rx="6" '
            f'fill="{PANEL_BG}" stroke="{BORDER}"/>'
        )
        out.append(
            f'<line x1="{bx}" y1="{by + 12}" x2="{bx}" y2="{by + box_h - 12}" '
            f'stroke="{accent}" stroke-width="3" stroke-linecap="round"/>'
        )
        out.append(
            f'<text x="{bx + 12}" y="{by + 17}" fill="{DIM}" font-size="10" font-weight="600">{html.escape(title)}</text>'
        )
        out.append(
            f'<text x="{bx + 12}" y="{by + 36}" fill="{BRIGHT}" font-size="15" font-weight="700">{html.escape(val)}</text>'
        )
        out.append(
            f'<text x="{bx + 12}" y="{by + 50}" fill="{DIM}" font-size="10">{html.escape(sub)}</text>'
        )
        out.append("</g>")
    return out


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    with open("data/contributions.json") as f:
        data = json.load(f)
    days = data["days"]
    probs = data.get("problems") or {
        "all": {"solved": 0, "total": 4000},
        "easy": {"solved": 0, "total": 950},
        "medium": {"solved": 0, "total": 2100},
        "hard": {"solved": 0, "total": 950},
    }

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

    anim_style = (
        ""
        if static
        else (
            ".c{opacity:0;animation:drop .5s ease-out forwards}"
            ".fade{opacity:0;transform:translateY(6px);animation:fadeIn .5s ease-out forwards}"
            ".seg{opacity:0;animation:segIn .6s ease-out forwards}"
            "@keyframes drop{from{opacity:0;transform:translate(-6px,-6px)}to{opacity:1;transform:none}}"
            "@keyframes fadeIn{to{opacity:1;transform:none}}"
            "@keyframes segIn{to{opacity:1}}"
        )
    )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="12">',
        f"<style>{anim_style}</style>",
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="8" fill="{BG}" stroke="{BORDER}"/>',
        # Terminal window header bar
        f'<circle cx="22" cy="20" r="6" fill="#ff5f57"/>'
        f'<circle cx="42" cy="20" r="6" fill="#febc2e"/>'
        f'<circle cx="62" cy="20" r="6" fill="#28c840"/>',
        f'<text x="{w / 2:.0f}" y="24" text-anchor="middle" fill="{DIM}" font-size="13">'
        f'leetcode-cli — @{data.get("username", "user")} — stats &amp; activity</text>',
        f'<line x1="1" y1="38" x2="{w - 1}" y2="38" stroke="{BORDER}"/>',
    ]

    # Top dashboard: Donut chart (left), Difficulty bars (middle), Stat boxes (right)
    parts.extend(render_donut(cx=96, cy=117, r=54, probs=probs))
    parts.extend(render_diff_bars(x0=190, y0=68, bar_w=305, probs=probs))
    parts.extend(render_stat_boxes(x0=534, y0=54, data=data))

    # Divider between dashboard and heatmap
    parts.append(f'<line x1="18" y1="{DASH_H}" x2="{w - 18}" y2="{DASH_H}" stroke="{BORDER}" stroke-dasharray="4 4"/>')

    # Month labels
    for week, label in month_marks:
        parts.append(
            f'<text x="{LEFT + week * (CELL + GAP)}" y="{TOP - 10}" fill="{DIM}">{label}</text>'
        )
    # Day of week labels
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(
            f'<text x="10" y="{TOP + row * (CELL + GAP) + CELL - 2}" fill="{DIM}">{label}</text>'
        )

    # Heatmap cells
    for week, row, lvl in cells:
        x = LEFT + week * (CELL + GAP)
        y = TOP + row * (CELL + GAP)
        delay = (week + row) * STEP
        parts.append(
            f'<rect class="c" style="animation-delay:{delay:.3f}s" x="{x}" y="{y}" '
            f'width="{CELL}" height="{CELL}" rx="3" fill="{PALETTE[lvl]}"/>'
        )

    # Footer: stats left, Less->More legend right
    fy = h - 16
    all_solved = probs.get("all", {}).get("solved", 0)
    easy_s = probs.get("easy", {}).get("solved", 0)
    med_s = probs.get("medium", {}).get("solved", 0)
    hard_s = probs.get("hard", {}).get("solved", 0)
    footer_left = (
        f'{data["total"]:,} submissions in the last year · '
        f'{all_solved} solved ({easy_s} Easy · {med_s} Medium · {hard_s} Hard)'
    )
    parts.append(f'<text x="{LEFT}" y="{fy}" fill="{FG}">{footer_left}</text>')
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
    print(f"wrote contrib-heatmap.svg ({weeks} weeks, {w}x{h})")


if __name__ == "__main__":
    main()
