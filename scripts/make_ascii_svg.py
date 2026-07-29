#!/usr/bin/env python3
"""Photo -> monochrome ASCII portrait SVG that types itself in row by row.

    python scripts/make_ascii_svg.py source-photo.jpg -o avi-ascii.svg

Animation is SMIL (a per-row clip rect that widens), because GitHub renders
README SVGs inside <img> where scripts are stripped but SMIL still runs.
"""
import argparse
import html

from PIL import Image, ImageEnhance, ImageOps

# dark -> light. rendered light-on-dark, so denser glyphs read as brighter.
RAMP = " .`:-~=+*oa#%@"

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
FONT_SIZE = 8.0
CHAR_W = FONT_SIZE * 0.6
LINE_H = FONT_SIZE
BG = "#0d1117"
FG = "#c9d1d9"
ACCENT = "#22d3ee"


def to_rows(path, cols, contrast):
    im = Image.open(path).convert("L")
    im = ImageOps.autocontrast(im, cutoff=2)
    im = ImageEnhance.Contrast(im).enhance(contrast)
    rows = max(1, round(cols * (im.height / im.width) * (CHAR_W / LINE_H)))
    im = im.resize((cols, rows), Image.LANCZOS)
    px = im.load()
    last = len(RAMP) - 1
    return ["".join(RAMP[px[x, y] * last // 255] for x in range(cols)) for y in range(rows)]


def build(rows, total_dur):
    cols = len(rows[0])
    w, h = cols * CHAR_W, len(rows) * LINE_H
    pad = 10.0
    step = total_dur / max(1, len(rows))
    # 2dp is all the SMIL attrs carry; a dur that rounds to 0.00s never runs
    dur = max(step * 2.2, 0.05)

    defs, body = [], []
    for i, row in enumerate(rows):
        y = pad + (i + 1) * LINE_H
        defs.append(
            f'<clipPath id="r{i}"><rect x="{pad:.1f}" y="{y - LINE_H:.1f}" '
            f'height="{LINE_H:.1f}" width="0">'
            f'<animate attributeName="width" from="0" to="{w:.1f}" '
            f'begin="{i * step:.2f}s" dur="{dur:.2f}s" fill="freeze"/>'
            f"</rect></clipPath>"
        )
        # textLength pins the grid: without it every column drifts on any
        # machine whose default monospace has a different advance width
        body.append(
            f'<text x="{pad:.1f}" y="{y:.1f}" clip-path="url(#r{i})" '
            f'textLength="{len(row) * CHAR_W:.1f}" lengthAdjust="spacingAndGlyphs" '
            f'xml:space="preserve">{html.escape(row)}</text>'
        )

    # blinking cursor parks on the last line once the portrait finishes
    cur_y = pad + len(rows) * LINE_H
    cursor = (
        f'<rect x="{pad:.1f}" y="{cur_y:.1f}" width="{CHAR_W:.1f}" height="{LINE_H:.1f}" '
        f'fill="{ACCENT}" opacity="0">'
        f'<animate attributeName="opacity" values="0;1;1;0;0;1" '
        f'begin="{total_dur:.2f}s" dur="1.1s" repeatCount="indefinite"/></rect>'
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w + pad * 2:.0f}" '
        f'height="{h + pad * 2 + LINE_H:.0f}" '
        f'viewBox="0 0 {w + pad * 2:.1f} {h + pad * 2 + LINE_H:.1f}" role="img">'
        f'<rect width="100%" height="100%" rx="8" fill="{BG}"/>'
        f"<defs>{''.join(defs)}</defs>"
        f'<g font-family="{FONT}" font-size="{FONT_SIZE}" fill="{FG}">'
        f"{''.join(body)}</g>{cursor}</svg>"
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("photo")
    p.add_argument("-o", "--out", default="avi-ascii.svg")
    p.add_argument("--cols", type=int, default=76)
    p.add_argument("--contrast", type=float, default=1.35)
    p.add_argument("--duration", type=float, default=2.4, help="seconds for the full type-in")
    a = p.parse_args()

    rows = to_rows(a.photo, a.cols, a.contrast)
    with open(a.out, "w") as f:
        f.write(build(rows, a.duration))
    print(f"{a.out}: {len(rows[0])}x{len(rows)} chars")


if __name__ == "__main__":
    main()
