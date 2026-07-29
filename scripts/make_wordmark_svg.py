#!/usr/bin/env python3
"""Extruded 3D ASCII wordmark SVG in a macOS terminal window: wipes in
left-to-right, then rocks on its vertical axis.

    python scripts/make_wordmark_svg.py SARAM -o wordmark.svg

The letterforms are upscaled before extruding. A 1-cell stroke extrudes into
an unreadable diagonal smear; a thick stroke reads as a solid slab, because the
body of the letter occludes its own trail. See docs/3d-ascii-wordmark.md.
"""
import argparse
import html

from termframe import frame

# 5x7 block font, upscaled at render time. '#' is ink.
GLYPHS = {
    "A": (" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "B": ("#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "),
    "C": (" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"),
    "D": ("#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "),
    "E": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
    "F": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
    "G": (" ####", "#    ", "#    ", "#  ##", "#   #", "#   #", " ####"),
    "H": ("#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "I": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "#####"),
    "J": ("#####", "    #", "    #", "    #", "    #", "#   #", " ### "),
    "K": ("#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"),
    "L": ("#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"),
    "M": ("#   #", "## ##", "# # #", "#   #", "#   #", "#   #", "#   #"),
    "N": ("#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"),
    "O": (" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "P": ("#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "),
    "Q": (" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"),
    "R": ("#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"),
    "S": (" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "),
    "T": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    "U": ("#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "V": ("#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "),
    "W": ("#   #", "#   #", "#   #", "#   #", "# # #", "## ##", "#   #"),
    "X": ("#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"),
    "Y": ("#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "),
    "Z": ("#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"),
    " ": ("     ",) * 7,
}

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
FACE = "#e6edf3"
SIDE = "#2b6172"
FACE_CH, SIDE_CH = "#", "s"

GAP = 2  # blank source columns between letters, before upscaling


def upscale(rows, sx, sy):
    """Blow each source cell up into an sx-by-sy block."""
    return [line for r in rows
            for line in ["".join(ch * sx for ch in r)] * sy]


def layout(text, depth, sx, sy):
    """Return (face_grid, side_grid) as lists of char lists."""
    glyphs = [upscale(GLYPHS[c], sx, sy) for c in text]
    gw, gh = len(glyphs[0][0]), len(glyphs[0])
    adv = gw + GAP * sx

    cells = {(x + i * adv, y)
             for i, g in enumerate(glyphs)
             for y, row in enumerate(g)
             for x, c in enumerate(row) if c == "#"}

    w = (len(text) - 1) * adv + gw + depth
    h = gh + depth
    face = [[" "] * w for _ in range(h)]
    side = [[" "] * w for _ in range(h)]

    # Extrusion goes up-and-right. A cell only shows side surface if the cell
    # diagonally up-right of it is empty -- otherwise that neighbour's body
    # occludes the trail. With thick strokes this suppresses nearly every
    # interior trail, which is what leaves the letters readable.
    for d in range(depth, 0, -1):
        for x, y in cells:
            if (x + 1, y - 1) in cells:
                continue
            side[y + depth - d][x + d] = SIDE_CH
    for x, y in cells:
        face[y + depth][x] = FACE_CH
        side[y + depth][x] = " "
    return face, side


def rows_to_text(grid, size, cw, x0, y0, fill, clip):
    out = []
    for i, row in enumerate(grid):
        line = "".join(row).rstrip()
        if line:
            # textLength pins the grid: without it every column drifts on any
            # machine whose default monospace has a different advance width
            out.append(
                f'<text x="{x0:.1f}" y="{y0 + (i + 1) * size:.1f}" fill="{fill}" '
                f'textLength="{len(line) * cw:.1f}" lengthAdjust="spacingAndGlyphs" '
                f'clip-path="url(#{clip})" xml:space="preserve">{html.escape(line)}</text>'
            )
    return "".join(out)


def build(text, depth, sx, sy, width, height, wipe, rock, title):
    face, side = layout(text, depth, sx, sy)
    cols, rows = len(face[0]), len(face)

    chrome, (bx, by, bw, bh) = frame(width, height, title, uid="w")

    # fit to whichever axis runs out first, so the word never overflows
    size = min(bw / (cols * 0.6), bh / rows)
    cw = size * 0.6
    x0 = bx + (bw - cols * cw) / 2
    y0 = by + (bh - rows * size) / 2

    cx = width / 2
    clip = (
        f'<clipPath id="wipe"><rect x="{bx}" y="{by}" height="{bh}" width="0">'
        f'<animate attributeName="width" from="0" to="{width}" begin="0.2s" '
        f'dur="{wipe}s" fill="freeze"/></rect></clipPath>'
    )
    # fake a y-axis rotation by oscillating horizontal scale about the centre
    spin = (
        f'<animateTransform attributeName="transform" type="scale" '
        f'values="1 1;0.88 1;1 1;1.03 1;1 1" begin="{wipe + 0.2:.1f}s" '
        f'dur="{rock}s" repeatCount="indefinite" additive="sum"/>'
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{FONT}" role="img">'
        f"{chrome}<defs>{clip}</defs>"
        f'<g transform="translate({cx},0)"><g>{spin}'
        f'<g transform="translate({-cx},0)" font-size="{size:.2f}" font-weight="700">'
        f"{rows_to_text(side, size, cw, x0, y0, SIDE, 'wipe')}"
        f"{rows_to_text(face, size, cw, x0, y0, FACE, 'wipe')}"
        f"</g></g></g></svg>"
    )


def _selfcheck():
    assert upscale(("#.",), 2, 3) == ["##..", "##..", "##.."]

    face, side = layout("I", 4, 3, 2)
    assert len(face) == 7 * 2 + 4, len(face)
    assert len(face[0]) == 5 * 3 + 4, len(face[0])
    # a face cell and a side cell may never occupy the same position
    assert all(f == " " or s == " "
               for fr, sr in zip(face, side) for f, s in zip(fr, sr))
    assert any(r[5 * 3] != " " for r in side), "no extrusion past the glyph box"

    # the occlusion rule must actually suppress trails: a solid 3x3 block has
    # only 5 silhouette cells, so depth 3 draws 15 side glyphs, not 27
    saved = GLYPHS.copy()
    try:
        GLYPHS["X"] = ("###", "###", "###")
        _, s2 = layout("X", 3, 1, 1)
        assert sum(c != " " for r in s2 for c in r) == 15
    finally:
        GLYPHS.clear()
        GLYPHS.update(saved)
    print("ok")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("text")
    p.add_argument("-o", "--out", default="wordmark.svg")
    p.add_argument("--depth", type=int, default=5)
    p.add_argument("--sx", type=int, default=2, help="horizontal glyph upscale")
    p.add_argument("--sy", type=int, default=3, help="vertical glyph upscale")
    p.add_argument("--width", type=int, default=490)
    p.add_argument("--height", type=int, default=396)
    p.add_argument("--wipe", type=float, default=1.2)
    p.add_argument("--rock", type=float, default=5.0)
    p.add_argument("--title", default="saram@github: ~$ ./wordmark.sh --3d")
    a = p.parse_args()

    text = a.text.upper()
    missing = set(text) - set(GLYPHS)
    if missing:
        p.error(f"no glyph for {sorted(missing)} (A-Z and space only)")

    with open(a.out, "w") as f:
        f.write(build(text, a.depth, a.sx, a.sy, a.width, a.height,
                      a.wipe, a.rock, a.title))
    print(f"{a.out}: '{text}' depth={a.depth} scale={a.sx}x{a.sy}")


if __name__ == "__main__":
    main()
