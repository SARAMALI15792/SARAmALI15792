#!/usr/bin/env python3
"""Extruded 3D ASCII wordmark SVG: wipes in left-to-right, then rocks on its
vertical axis.

    python scripts/make_wordmark_svg.py SARAM -o wordmark.svg

The 3D read comes from a single trick: every filled cell of a 5x7 block glyph
is repeated up-and-right D times in a dimmer glyph, then the bright face is
painted on top. See docs/3d-ascii-wordmark.md.
"""
import argparse
import html

# 5x7 block font. '#' is ink.
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

GH, GW = 7, 5
# letters need air: at GAP 1 the diagonal extrusion trails run into the
# neighbouring glyph and the word stops being readable.
GAP = 4
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
BG = "#0d1117"
FACE = "#e6edf3"
SIDE = "#356d7d"
FACE_CH, SIDE_CH = "#", ":"


def layout(text, depth):
    """Return (face_grid, side_grid) as lists of char lists."""
    cells = [(x + i * (GW + GAP), y)
             for i, ch in enumerate(text)
             for y, row in enumerate(GLYPHS[ch])
             for x, c in enumerate(row) if c == "#"]

    w = len(text) * (GW + GAP) - 1 + depth
    h = GH + depth
    face = [[" "] * w for _ in range(h)]
    side = [[" "] * w for _ in range(h)]

    # Extrusion goes up-and-right. A cell only shows side surface if the cell
    # diagonally up-right of it is empty -- otherwise that neighbour's body
    # occludes the trail, and drawing it anyway floods the counters with noise.
    solid = set(cells)
    for d in range(depth, 0, -1):
        for x, y in cells:
            if (x + 1, y - 1) in solid:
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


def build(text, depth, width, height, wipe, rock):
    face, side = layout(text, depth)
    cols, rows = len(face[0]), len(face)

    size = (width * 0.92) / (cols * 0.6)
    cw = size * 0.6
    x0 = (width - cols * cw) / 2
    y0 = (height - rows * size) / 2

    cx = width / 2
    clip = (
        f'<clipPath id="wipe"><rect x="0" y="0" height="{height}" width="0">'
        f'<animate attributeName="width" from="0" to="{width}" begin="0.2s" '
        f'dur="{wipe}s" fill="freeze"/></rect></clipPath>'
    )
    # fake a y-axis rotation by oscillating horizontal scale about the centre
    spin = (
        f'<animateTransform attributeName="transform" type="scale" '
        f'values="1 1;0.82 1;1 1;1.04 1;1 1" begin="{wipe + 0.2:.1f}s" '
        f'dur="{rock}s" repeatCount="indefinite" additive="sum"/>'
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">'
        f'<rect width="100%" height="100%" rx="8" fill="{BG}"/>'
        f"<defs>{clip}</defs>"
        f'<g transform="translate({cx},0)"><g>{spin}'
        f'<g transform="translate({-cx},0)" font-family="{FONT}" '
        f'font-size="{size:.2f}" font-weight="700">'
        f"{rows_to_text(side, size, cw, x0, y0, SIDE, 'wipe')}"
        f"{rows_to_text(face, size, cw, x0, y0, FACE, 'wipe')}"
        f"</g></g></g></svg>"
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("text")
    p.add_argument("-o", "--out", default="wordmark.svg")
    p.add_argument("--depth", type=int, default=3)
    p.add_argument("--width", type=int, default=490)
    p.add_argument("--height", type=int, default=396)
    p.add_argument("--wipe", type=float, default=1.2)
    p.add_argument("--rock", type=float, default=5.0)
    a = p.parse_args()

    text = a.text.upper()
    missing = set(text) - set(GLYPHS)
    if missing:
        p.error(f"no glyph for {sorted(missing)} (A-Z and space only)")

    with open(a.out, "w") as f:
        f.write(build(text, a.depth, a.width, a.height, a.wipe, a.rock))
    print(f"{a.out}: '{text}' depth={a.depth}")


if __name__ == "__main__":
    main()


def _selfcheck():
    """python -c 'import scripts.make_wordmark_svg as m; m._selfcheck()'"""
    face, side = layout("I", 2)
    assert len(face) == GH + 2, len(face)
    assert len(face[0]) == GW + GAP - 1 + 2, len(face[0])
    # top row of 'I' is solid; its face lands on the bottom-shifted row
    assert "".join(face[2]).startswith("#####"), face[2]
    # nothing may occupy a face cell in the side layer
    assert all(f == " " or s == " " for fr, sr in zip(face, side) for f, s in zip(fr, sr))
    # extrusion must actually stick out past the glyph box
    assert any(r[GW] != " " for r in side), "no extrusion drawn"
    print("ok")
