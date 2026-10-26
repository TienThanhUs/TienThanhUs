#!/usr/bin/env python3
"""Lấy lịch nộp bài LeetCode, ghi ra data/contributions.json (cùng định dạng bản GitHub)."""
import datetime as dt
import json
import os

import requests

USERNAME = os.environ.get("LEETCODE_USERNAME", "23F9oGHWpJ")
QUERY = """
query($u: String!) {
  allQuestionsCount { difficulty count }
  matchedUser(username: $u) {
    submitStatsGlobal {
      acSubmissionNum { difficulty count submissions }
    }
    userCalendar { submissionCalendar streak totalActiveDays }
  }
}"""


def main() -> None:
    r = requests.post(
        "https://leetcode.com/graphql",
        json={"query": QUERY, "variables": {"u": USERNAME}},
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://leetcode.com"},
        timeout=30,
    )
    r.raise_for_status()
    payload = r.json()["data"]
    user = payload["matchedUser"]
    if not user:
        raise SystemExit(f"không tìm thấy user LeetCode: {USERNAME}")

    totals_map = {item["difficulty"]: item["count"] for item in payload.get("allQuestionsCount") or []}
    ac_list = (user.get("submitStatsGlobal") or {}).get("acSubmissionNum") or []
    solved_map = {item["difficulty"]: item["count"] for item in ac_list}
    submissions_map = {item["difficulty"]: item.get("submissions", 0) for item in ac_list}

    problems = {
        "all": {"solved": solved_map.get("All", 0), "total": totals_map.get("All", 0), "submissions": submissions_map.get("All", 0)},
        "easy": {"solved": solved_map.get("Easy", 0), "total": totals_map.get("Easy", 0), "submissions": submissions_map.get("Easy", 0)},
        "medium": {"solved": solved_map.get("Medium", 0), "total": totals_map.get("Medium", 0), "submissions": submissions_map.get("Medium", 0)},
        "hard": {"solved": solved_map.get("Hard", 0), "total": totals_map.get("Hard", 0), "submissions": submissions_map.get("Hard", 0)},
    }

    cal = user.get("userCalendar") or {}
    raw = json.loads(cal.get("submissionCalendar") or "{}")

    # khoá là mốc thời gian UTC (giây), giá trị là số lần nộp trong ngày đó
    by_date = {}
    for ts, n in raw.items():
        d = dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).date().isoformat()
        by_date[d] = by_date.get(d, 0) + n

    today = dt.date.today()
    dates = [(today - dt.timedelta(days=i)).isoformat() for i in range(365, -1, -1)]
    counts = [by_date.get(d, 0) for d in dates]
    mx = max(counts) or 1

    def level(c: int) -> int:
        if c == 0:
            return 0
        return min(4, max(1, -(-c * 4 // mx)))  # chia 4 mức theo ngày nhiều nhất

    days = [{"date": d, "count": c, "level": level(c)} for d, c in zip(dates, counts)]
    total = sum(counts)
    best = max(days, key=lambda x: x["count"])

    longest = cur = 0
    for d in days:
        cur = cur + 1 if d["count"] > 0 else 0
        longest = max(longest, cur)
    current = 0
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        elif d["date"] != today.isoformat():
            break

    monthly = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]

    out = {
        "username": USERNAME,
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "total": total,
        "total_active_days": cal.get("totalActiveDays", sum(1 for d in days if d["count"] > 0)),
        "best_day": {"date": best["date"], "count": best["count"]},
        "current_streak": current,
        "longest_streak": longest,
        "problems": problems,
        "monthly": monthly,
        "days": days,
    }
    os.makedirs("data", exist_ok=True)
    with open("data/contributions.json", "w") as f:
        json.dump(out, f, indent=1)
    p_all = problems["all"]["solved"]
    print(f"wrote data/contributions.json — {p_all} solved ({problems['easy']['solved']}E/{problems['medium']['solved']}M/{problems['hard']['solved']}H), {total} submissions across {len(days)} days")


if __name__ == "__main__":
    main()