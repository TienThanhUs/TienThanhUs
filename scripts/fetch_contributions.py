#!/usr/bin/env python3
"""Fetch the public contribution calendar — no token needed.

GitHub serves the calendar as public HTML at
https://github.com/users/<username>/contributions (the same fragment the
profile page uses). Parse day cells + tooltips, derive stats, write
data/contributions.json.
"""
import datetime as dt
import json
import re

import requests
from bs4 import BeautifulSoup

import os

USERNAME = os.environ.get("GITHUB_USERNAME", "octocat")
URL = f"https://github.com/users/{USERNAME}/contributions"


def main() -> None:
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Tooltips carry the counts: "3 contributions on July 4th." / "No contributions on ..."
    counts = {}
    for tip in soup.select("tool-tip"):
        target = tip.get("for", "")
        m = re.match(r"(\d+|No) contribution", tip.get_text(strip=True))
        if m and target:
            counts[target] = 0 if m.group(1) == "No" else int(m.group(1))

    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        date = td["data-date"]
        level = int(td.get("data-level", 0))
        count = counts.get(td.get("id", ""), 0)
        if count == 0 and level > 0:
            # tooltip missing/unparsed: estimate from level so totals stay sane
            count = level
        days.append({"date": date, "count": count, "level": level})
    days.sort(key=lambda d: d["date"])
    if not days:
        raise SystemExit("no day cells parsed — GitHub markup may have changed")

    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])

    # streaks (a day counts if count > 0); current streak may still be alive today
    longest = cur = 0
    for d in days:
        cur = cur + 1 if d["count"] > 0 else 0
        longest = max(longest, cur)
    current = 0
    today = dt.date.today().isoformat()
    for d in reversed(days):
        if d["date"] > today:
            continue
        if d["count"] > 0:
            current += 1
        elif d["date"] != today:  # an empty today doesn't break the streak yet
            break

    monthly = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]

    out = {
        "username": USERNAME,
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "total": total,
        "best_day": {"date": best["date"], "count": best["count"]},
        "current_streak": current,
        "longest_streak": longest,
        "monthly": monthly,
        "days": days,
    }
    with open("data/contributions.json", "w") as f:
        json.dump(out, f, indent=1)
    print(f"wrote data/contributions.json — {total} contributions across {len(days)} days")


if __name__ == "__main__":
    main()
