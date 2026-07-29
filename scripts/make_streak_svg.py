#!/usr/bin/env python3
"""Self-hosted GitHub streak card.

    GITHUB_TOKEN=... python scripts/make_streak_svg.py SARAMALI15792 -o streak-card.svg

Replaces streak-stats.demolab.com, which cold-starts past GitHub's camo proxy
timeout and so renders as a broken image most of the time. This is generated
once a day into the repo, so it always loads.

The calendar API only returns one year per call, so totals are summed across a
call per year since the account was created, cached to data/streak.json.
"""
import argparse
import datetime
import json
import os
import pathlib
import urllib.error
import urllib.request

from termframe import frame

QUERY = """
query($login:String!,$from:DateTime!,$to:DateTime!){
  user(login:$login){
    contributionsCollection(from:$from,to:$to){
      contributionCalendar{ weeks{ contributionDays{ date contributionCount } } }
    }
  }
}
"""

CACHE = pathlib.Path("data/streak.json")

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
BIG = "#e6edf3"
LABEL = "#7d8590"
FLAME = "#f78166"
ACCENT = "#39d353"


def _api(url, data=None, token=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode() if data else None,
        headers={"Authorization": f"bearer {token}",
                 "Content-Type": "application/json",
                 "User-Agent": "profile-art"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch(login, token):
    created = _api(f"https://api.github.com/users/{login}", token=token)["created_at"]
    start, today = int(created[:4]), datetime.date.today()

    days = {}
    for yr in range(start, today.year + 1):
        payload = _api("https://api.github.com/graphql", {
            "query": QUERY,
            "variables": {"login": login,
                          "from": f"{yr}-01-01T00:00:00Z",
                          "to": f"{yr}-12-31T23:59:59Z"},
        }, token)
        if "errors" in payload:
            raise RuntimeError(payload["errors"])
        cal = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        for w in cal["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = d["contributionCount"]

    # the API pads the calendar to whole weeks, so it can run past today
    days = {k: v for k, v in days.items() if k <= today.isoformat()}
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(days, indent=0, sort_keys=True))
    return days


def load(login, token):
    if token:
        try:
            return fetch(login, token)
        except (urllib.error.URLError, RuntimeError, KeyError, TypeError) as e:
            print(f"warn: live fetch failed ({e}); using cache")
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    raise SystemExit("no GITHUB_TOKEN and no data/streak.json cache to fall back on")


def streaks(days):
    """Return (total, current_streak, longest_streak, longest_range).

    A streak is consecutive calendar days with at least one contribution. Today
    counts as neutral rather than breaking: the day isn't over, so a still-empty
    today must not zero out a live streak."""
    dates = sorted(days)
    total = sum(days.values())
    today = datetime.date.today()

    best = cur = 0
    cur_start = prev = None
    best_range = (None, None)

    for iso in dates:
        d = datetime.date.fromisoformat(iso)
        if days[iso] > 0:
            # a missing date is a gap, not a bridge -- never assume the dict is
            # dense, or an absent day silently welds two streaks together
            if cur and prev and (d - prev).days == 1:
                cur += 1
            else:
                cur, cur_start = 1, d
            if cur > best:
                best, best_range = cur, (cur_start, d)
            prev = d
        elif d != today:
            cur, cur_start, prev = 0, None, d

    # the trailing run is only "current" if it reaches today or yesterday
    current, cur_range = 0, (None, None)
    if cur:
        last_active = max((datetime.date.fromisoformat(i)
                           for i in dates if days[i] > 0), default=None)
        if last_active and (today - last_active).days <= 1:
            current = cur
            cur_range = (cur_start, last_active)
    # anchor the total on the first *active* day, not the first fetched one --
    # years are fetched whole, so dates[0] is a Jan 1 that predates the account
    active = [i for i in dates if days[i] > 0]
    first = datetime.date.fromisoformat(active[0]) if active else None
    return total, current, best, best_range, cur_range, first


def fmt(d1, d2):
    if not d1:
        return "-"
    m = "%b %-d"
    if d1 == d2:
        return d1.strftime(f"{m}, %Y")
    if d1.year == d2.year:
        return f"{d1.strftime(m)} - {d2.strftime(m)}, {d2.year}"
    return f"{d1.strftime(f'{m}, %Y')} - {d2.strftime(f'{m}, %Y')}"


def build(stats, width, height, title):
    total, current, best, best_range, cur_range, first = stats
    chrome, (bx, by, bw, bh) = frame(width, height, title, uid="s")

    cy = by + bh / 2
    cols = [
        (total, "Total Contributions",
         f"{first.strftime('%b %-d, %Y')} - Present" if first else "-", BIG),
        (current, "Current Streak", fmt(*cur_range), FLAME),
        (best, "Longest Streak", fmt(*best_range), ACCENT),
    ]

    out = []
    for i, (value, label, sub, colour) in enumerate(cols):
        x = bx + bw * (i + 0.5) / 3
        out.append(
            f'<text x="{x:.1f}" y="{cy - 12:.1f}" fill="{colour}" font-size="34" '
            f'font-weight="700" text-anchor="middle">{value}</text>'
            f'<text x="{x:.1f}" y="{cy + 14:.1f}" fill="{BIG}" font-size="13" '
            f'text-anchor="middle">{label}</text>'
            f'<text x="{x:.1f}" y="{cy + 34:.1f}" fill="{LABEL}" font-size="10.5" '
            f'text-anchor="middle">{sub}</text>'
        )
        if i:  # divider to the left of every column but the first
            dx = bx + bw * i / 3
            out.append(
                f'<line x1="{dx:.1f}" y1="{by + 18:.1f}" x2="{dx:.1f}" '
                f'y2="{by + bh - 18:.1f}" stroke="#30363d"/>'
            )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{FONT}" role="img">'
        f"{chrome}{''.join(out)}</svg>"
    )


def _selfcheck():
    day = datetime.date.today()
    d = lambda n: (day - datetime.timedelta(days=n)).isoformat()

    # a 3-day run ending today is both the current and the longest streak
    total, cur, best, _, _, _ = streaks({d(0): 1, d(1): 2, d(2): 1, d(4): 5})
    assert (total, cur, best) == (9, 3, 3), (total, cur, best)

    # an empty today must not break a streak that ran through yesterday
    total, cur, best, _, _, _ = streaks({d(0): 0, d(1): 1, d(2): 1})
    assert (cur, best) == (2, 2), (cur, best)

    # a gap of two days ends the current streak entirely
    _, cur, best, _, _, _ = streaks({d(3): 1, d(4): 1, d(5): 1})
    assert cur == 0 and best == 3, (cur, best)
    print("ok")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("login")
    p.add_argument("-o", "--out", default="streak-card.svg")
    p.add_argument("--width", type=int, default=495)
    p.add_argument("--height", type=int, default=195)
    p.add_argument("--title", default="saram@github: ~$ ./streak.sh")
    a = p.parse_args()

    days = load(a.login, os.environ.get("GITHUB_TOKEN"))
    stats = streaks(days)
    with open(a.out, "w") as f:
        f.write(build(stats, a.width, a.height, a.title))
    print(f"{a.out}: total={stats[0]} current={stats[1]} longest={stats[2]}")


if __name__ == "__main__":
    main()
