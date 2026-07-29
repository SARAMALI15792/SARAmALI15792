#!/usr/bin/env python3
"""Shared macOS-style terminal chrome for the profile panels.

All three SVGs draw the same window: rounded border, a title bar with the
three traffic lights, and a centred command prompt. Kept in one place so the
panels can't drift apart visually.
"""
import html

BORDER = "#30363d"
TITLE = "#7d8590"
BG_TOP, BG_BOT = "#111722", "#0d1117"
LIGHTS = ("#ff5f56", "#ffbd2e", "#27c93f")

BAR = 28.0
PAD = 18.0


def frame(w, h, title, uid=""):
    """Return (svg_markup, content_box). content_box is (x, y, w, h) — the
    usable area below the title bar, which every caller should lay out into."""
    lights = "".join(
        f'<circle cx="{18 + i * 15}" cy="{BAR / 2:.1f}" r="4.5" fill="{c}"/>'
        for i, c in enumerate(LIGHTS)
    )
    markup = (
        f'<defs><linearGradient id="bg{uid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/>'
        f'<stop offset="1" stop-color="{BG_BOT}"/></linearGradient></defs>'
        f'<rect width="{w}" height="{h}" rx="12" fill="url(#bg{uid})"/>'
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" '
        f'fill="none" stroke="{BORDER}" stroke-width="1"/>'
        f'<line x1="0" y1="{BAR}" x2="{w}" y2="{BAR}" stroke="{BORDER}"/>'
        f"{lights}"
        f'<text x="{w / 2:.1f}" y="{BAR * 0.64:.1f}" fill="{TITLE}" font-size="11.5" '
        f'text-anchor="middle">{html.escape(title)}</text>'
    )
    return markup, (PAD, BAR + 8, w - 2 * PAD, h - BAR - 8 - PAD)
