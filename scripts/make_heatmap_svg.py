#!/usr/bin/env python3
"""Real GitHub contribution calendar -> SVG that reveals cell by cell.

    GITHUB_TOKEN=... python scripts/make_heatmap_svg.py SARAMALI15792 -o contrib-heatmap.svg

Pulls the calendar over the GraphQL API (the only endpoint that exposes it),
caches the raw response to data/contrib.json, and falls back to that cache if
the API is unreachable so a flaky run never blanks the README.
"""
import argparse
import json
import os
import pathlib
import urllib.error
import urllib.request

QUERY = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{
        totalContributions
        weeks{ contributionDays{ date contributionCount } }
      }
    }
  }
}
"""

CACHE = pathlib.Path("data/contrib.json")

BG = "#0d1117"
TEXT = "#7d8590"
EMPTY = "#161b22"
# GitHub's own 4-step green ramp
LEVELS = ["#0e4429", "#006d32", "#26a641", "#39d353"]

CELL, GAP = 12.5, 3.0
PAD_L, PAD_T = 30.0, 20.0
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}",
                 "Content-Type": "application/json",
                 "User-Agent": "profile-art"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    cal = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cal, indent=1))
    return cal


def load(login, token):
    if token:
        try:
            return fetch(login, token)
        except (urllib.error.URLError, RuntimeError, KeyError, TypeError) as e:
            print(f"warn: live fetch failed ({e}); using cache")
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    raise SystemExit("no GITHUB_TOKEN and no data/contrib.json cache to fall back on")


def thresholds(counts):
    """Quartiles of the *active* days, which is how GitHub picks its shades.
    Scaling linearly to the year's peak instead collapses a normal year into
    the darkest green, because one 30-commit day drags every threshold up."""
    active = sorted(c for c in counts if c > 0)
    if not active:
        return (1, 2, 3)
    return tuple(active[min(len(active) - 1, int(len(active) * p))]
                 for p in (0.25, 0.5, 0.75))


def level(count, th):
    if count <= 0:
        return 0
    return 1 + sum(count > t for t in th)


def build(cal, reveal):
    weeks = cal["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    th = thresholds(d["contributionCount"] for d in days)

    w = PAD_L + len(weeks) * (CELL + GAP) + 10
    h = PAD_T + 7 * (CELL + GAP) + 24
    step = reveal / max(1, len(weeks))

    cells, labels, seen = [], [], set()
    for x, week in enumerate(weeks):
        for day in week["contributionDays"]:
            # rows are keyed off the real weekday: the first and last weeks of
            # the range are partial, so position can't come from list index
            dow = _dow(day["date"])
            cx = PAD_L + x * (CELL + GAP)
            cy = PAD_T + dow * (CELL + GAP)
            lv = level(day["contributionCount"], th)
            fill = EMPTY if lv == 0 else LEVELS[lv - 1]
            begin = x * step + dow * step * 0.12
            cells.append(
                f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{fill}" opacity="0">'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin:.2f}s" dur="0.35s" fill="freeze"/></rect>'
            )
        first = week["contributionDays"][0]["date"]
        month = first[5:7]
        if month not in seen and int(first[8:10]) <= 7:
            seen.add(month)
            labels.append(
                f'<text x="{PAD_L + x * (CELL + GAP):.1f}" y="{PAD_T - 6:.1f}">'
                f"{MONTHS[int(month) - 1]}</text>"
            )

    for i, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        labels.append(
            f'<text x="0" y="{PAD_T + i * (CELL + GAP) + CELL - 1:.1f}">{name}</text>'
        )

    total = cal["totalContributions"]
    footer = (
        f'<text x="{PAD_L:.1f}" y="{h - 6:.1f}">{total:,} contributions in the last year'
        f'</text>'
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" '
        f'viewBox="0 0 {w:.1f} {h:.1f}" role="img">'
        f'<rect width="100%" height="100%" rx="8" fill="{BG}"/>'
        f"{''.join(cells)}"
        f'<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
        f'font-size="9" fill="{TEXT}">{"".join(labels)}{footer}</g></svg>'
    )


def _dow(iso):
    """Day-of-week index, Sunday=0, without pulling in datetime parsing."""
    import datetime
    return (datetime.date.fromisoformat(iso).weekday() + 1) % 7


def main():
    p = argparse.ArgumentParser()
    p.add_argument("login")
    p.add_argument("-o", "--out", default="contrib-heatmap.svg")
    p.add_argument("--reveal", type=float, default=2.2, help="seconds for the full sweep")
    a = p.parse_args()

    cal = load(a.login, os.environ.get("GITHUB_TOKEN"))
    with open(a.out, "w") as f:
        f.write(build(cal, a.reveal))
    print(f"{a.out}: {cal['totalContributions']} contributions, {len(cal['weeks'])} weeks")


if __name__ == "__main__":
    main()
