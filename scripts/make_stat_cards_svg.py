#!/usr/bin/env python3
"""Self-hosted stats, top-languages and activity cards in the terminal frame.

    GITHUB_TOKEN=... python scripts/make_stat_cards_svg.py SARAMALI15792

Writes stats-card.svg, langs-card.svg and activity-card.svg. Replaces the
third-party vercel cards so the whole GitHub section matches the hero panels
and loads from this repo instead of someone else's paused deployment.

One GraphQL call feeds the stats and language cards; the activity card reuses
data/streak.json, already fetched by make_streak_svg.py.
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
query($login:String!){
  user(login:$login){
    followers{ totalCount }
    contributionsCollection{
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
    }
    repositoriesContributedTo(first:1,
      contributionTypes:[COMMIT,ISSUE,PULL_REQUEST,REPOSITORY]){ totalCount }
    repositories(first:100, ownerAffiliations:OWNER, isFork:false,
      orderBy:{field:STARGAZERS,direction:DESC}){
      totalCount
      nodes{
        stargazerCount
        languages(first:10, orderBy:{field:SIZE,direction:DESC}){
          edges{ size node{ name color } }
        }
      }
    }
  }
}
"""

CACHE = pathlib.Path("data/stats.json")
STREAK_CACHE = pathlib.Path("data/streak.json")

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
VALUE = "#e6edf3"
LABEL = "#7d8590"
ACCENT = "#39d353"
GRID = "#30363d"
FALLBACK = "#8b949e"


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

    u = payload["data"]["user"]
    c = u["contributionsCollection"]
    repos = u["repositories"]

    langs = {}
    for node in repos["nodes"]:
        for e in node["languages"]["edges"]:
            n = e["node"]
            langs.setdefault(n["name"], {"size": 0, "color": n["color"] or FALLBACK})
            langs[n["name"]]["size"] += e["size"]

    data = {
        "stars": sum(n["stargazerCount"] for n in repos["nodes"]),
        "repos": repos["totalCount"],
        "commits": c["totalCommitContributions"],
        "prs": c["totalPullRequestContributions"],
        "issues": c["totalIssueContributions"],
        "reviews": c["totalPullRequestReviewContributions"],
        "contributed": u["repositoriesContributedTo"]["totalCount"],
        "followers": u["followers"]["totalCount"],
        "languages": langs,
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(data, indent=1, sort_keys=True))
    return data


def load(login, token):
    if token:
        try:
            return fetch(login, token)
        except (urllib.error.URLError, RuntimeError, KeyError, TypeError) as e:
            print(f"warn: live fetch failed ({e}); using cache")
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    raise SystemExit("no GITHUB_TOKEN and no data/stats.json cache to fall back on")


def human(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1000:
        return f"{n / 1000:.1f}k".replace(".0k", "k")
    return str(n)


def stats_card(d, w, h, title):
    chrome, (bx, by, bw, bh) = frame(w, h, title, uid="st")
    rows = [
        ("Total Stars", d["stars"]), ("Public Repos", d["repos"]),
        ("Commits (yr)", d["commits"]), ("Pull Requests", d["prs"]),
        ("Issues", d["issues"]), ("Contributed To", d["contributed"]),
    ]
    out, n = [], (len(rows) + 1) // 2
    for i, (label, value) in enumerate(rows):
        col, row = i // n, i % n
        x = bx + 14 + col * (bw / 2)
        y = by + 26 + row * ((bh - 34) / n)
        out.append(
            f'<text x="{x:.1f}" y="{y:.1f}" fill="{LABEL}" font-size="12.5">{label}</text>'
            f'<text x="{x + bw / 2 - 30:.1f}" y="{y:.1f}" fill="{VALUE}" font-size="14" '
            f'font-weight="700" text-anchor="end">{human(value)}</text>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="{FONT}" role="img">'
        f"{chrome}{''.join(out)}</svg>"
    )


def langs_card(d, w, h, title, top):
    chrome, (bx, by, bw, bh) = frame(w, h, title, uid="lg")
    langs = sorted(d["languages"].items(), key=lambda kv: -kv[1]["size"])[:top]
    total = sum(v["size"] for _, v in langs) or 1

    bar_y, bar_h = by + 14, 12
    x, segs, legend = bx, [], []
    for i, (name, v) in enumerate(langs):
        seg = bw * v["size"] / total
        # round only the outer ends so the bar reads as one continuous strip
        segs.append(f'<rect x="{x:.2f}" y="{bar_y}" width="{max(seg, 0.6):.2f}" '
                    f'height="{bar_h}" fill="{v["color"]}"/>')
        x += seg

        col, row = i % 2, i // 2
        lx = bx + 6 + col * (bw / 2)
        ly = bar_y + bar_h + 26 + row * 21
        pct = 100 * v["size"] / total
        legend.append(
            f'<circle cx="{lx + 4:.1f}" cy="{ly - 4:.1f}" r="4.5" fill="{v["color"]}"/>'
            f'<text x="{lx + 15:.1f}" y="{ly:.1f}" fill="{VALUE}" font-size="11.5">'
            f'{name}</text>'
            f'<text x="{lx + bw / 2 - 14:.1f}" y="{ly:.1f}" fill="{LABEL}" '
            f'font-size="11.5" text-anchor="end">{pct:.1f}%</text>'
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="{FONT}" role="img">'
        f"{chrome}"
        f'<clipPath id="lgbar"><rect x="{bx}" y="{bar_y}" width="{bw}" '
        f'height="{bar_h}" rx="6"/></clipPath>'
        f'<g clip-path="url(#lgbar)">{"".join(segs)}</g>'
        f"{''.join(legend)}</svg>"
    )


def activity_card(days, w, h, title, weeks):
    """Weekly contribution totals as an area chart, newest at the right."""
    chrome, (bx, by, bw, bh) = frame(w, h, title, uid="ac")
    today = datetime.date.today()
    start = today - datetime.timedelta(weeks=weeks)

    buckets = {}
    for iso, n in days.items():
        d = datetime.date.fromisoformat(iso)
        if d >= start:
            wk = d - datetime.timedelta(days=(d.weekday() + 1) % 7)
            buckets[wk] = buckets.get(wk, 0) + n
    series = [buckets[k] for k in sorted(buckets)]
    if len(series) < 2:
        series = series * 2 or [0, 0]

    peak = max(series) or 1
    plot_y, plot_h = by + 16, bh - 42
    step = bw / (len(series) - 1)
    pts = [(bx + i * step, plot_y + plot_h * (1 - v / peak))
           for i, v in enumerate(series)]

    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = (f"{bx:.1f},{plot_y + plot_h:.1f} " + line +
            f" {bx + bw:.1f},{plot_y + plot_h:.1f}")

    grid = "".join(
        f'<line x1="{bx}" y1="{plot_y + plot_h * f:.1f}" x2="{bx + bw}" '
        f'y2="{plot_y + plot_h * f:.1f}" stroke="{GRID}" stroke-width="0.5"/>'
        for f in (0, 0.5, 1)
    )
    last = pts[-1]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="{FONT}" role="img">'
        f"{chrome}"
        f'<defs><linearGradient id="acg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{ACCENT}" stop-opacity="0.45"/>'
        f'<stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>'
        f"</linearGradient></defs>{grid}"
        f'<polygon points="{area}" fill="url(#acg)"/>'
        f'<polyline points="{line}" fill="none" stroke="{ACCENT}" '
        f'stroke-width="2" stroke-linejoin="round"/>'
        f'<circle cx="{last[0]:.1f}" cy="{last[1]:.1f}" r="3.5" fill="{ACCENT}"/>'
        f'<text x="{bx}" y="{by + bh - 6:.1f}" fill="{LABEL}" font-size="10.5">'
        f'{weeks} weeks</text>'
        f'<text x="{bx + bw:.1f}" y="{by + bh - 6:.1f}" fill="{LABEL}" '
        f'font-size="10.5" text-anchor="end">peak {peak}/week</text></svg>'
    )


def _selfcheck():
    assert human(999) == "999" and human(1500) == "1.5k" and human(2000) == "2k"
    assert human(1_200_000) == "1.2M"

    d = {"stars": 1, "repos": 2, "commits": 3, "prs": 4, "issues": 5,
         "contributed": 6, "followers": 7,
         "languages": {"Python": {"size": 30, "color": "#3572A5"},
                       "Rust": {"size": 10, "color": "#dea584"}}}
    svg = langs_card(d, 495, 195, "t", 8)
    # 30/40 and 10/40 -- percentages must be of the charted total, not of 100
    assert ">75.0%<" in svg and ">25.0%<" in svg, "language percentages wrong"

    today = datetime.date.today()
    days = {(today - datetime.timedelta(days=i)).isoformat(): i % 4 for i in range(90)}
    a = activity_card(days, 495, 195, "t", 8)
    assert "<polyline" in a and "polygon" in a

    # a flat-zero history must not divide by zero
    flat = {(today - datetime.timedelta(days=i)).isoformat(): 0 for i in range(30)}
    assert "<polyline" in activity_card(flat, 495, 195, "t", 4)
    print("ok")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("login")
    p.add_argument("--width", type=int, default=495)
    p.add_argument("--height", type=int, default=195)
    p.add_argument("--top", type=int, default=6, help="languages to chart")
    p.add_argument("--weeks", type=int, default=26)
    p.add_argument("--label", default="saram",
                   help="prompt name, to match the hero panels")
    a = p.parse_args()

    d = load(a.login, os.environ.get("GITHUB_TOKEN"))
    who = a.label

    pathlib.Path("stats-card.svg").write_text(
        stats_card(d, a.width, a.height, f"{who}@github: ~$ ./stats.sh"))
    pathlib.Path("langs-card.svg").write_text(
        langs_card(d, a.width, a.height, f"{who}@github: ~$ ./langs.sh", a.top))

    if STREAK_CACHE.exists():
        days = json.loads(STREAK_CACHE.read_text())
        pathlib.Path("activity-card.svg").write_text(
            activity_card(days, a.width, a.height,
                          f"{who}@github: ~$ ./activity.sh", a.weeks))
        print("activity-card.svg written")
    else:
        print("warn: data/streak.json missing; skipped activity-card.svg")

    print(f"stats-card.svg: {d['stars']} stars, {d['repos']} repos")
    print(f"langs-card.svg: {len(d['languages'])} languages")


if __name__ == "__main__":
    main()
