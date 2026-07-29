# How the 3D ASCII wordmark is built

`scripts/make_wordmark_svg.py` turns a word into an extruded ASCII slab. There
is no 3D engine involved — it's a 2D grid with one occlusion rule.

## 1. Block glyphs

Each letter is a 5x7 grid of `#` in the `GLYPHS` table. `SARAM` becomes a list
of filled `(x, y)` cells, with `GAP` blank columns between letters.

`GAP` is 4, not 1. The extrusion runs diagonally, so at `GAP 1` each letter's
depth trail lands on top of its neighbour and the word stops being readable.

## 2. Extrusion

Every filled cell repeats up-and-right `depth` times in a dimmer glyph (`:`),
deepest layer drawn first so nearer layers paint over it.

The rule that makes it look solid rather than like confetti:

```
if (x + 1, y - 1) in solid:
    continue
```

A cell only shows a side face if the cell diagonally up-right of it is empty.
Otherwise that neighbour's body is in the way. Without this test you draw the
interior of the solid, and every letter's counter fills with noise.

Then the bright face (`#`) is painted on top, and any side glyph sharing a cell
with a face is cleared.

## 3. Rendering

Rows become `<text>` elements. Each one carries:

```
textLength="<chars * cw>" lengthAdjust="spacingAndGlyphs"
```

This pins the character grid to exact coordinates. Without it the columns drift
apart on any machine whose default monospace font has a different advance width
— which, for a README rendered on other people's browsers, is most of them.

## 4. Animation

Both effects are SMIL, because GitHub renders README SVGs inside `<img>`, where
scripts are stripped but SMIL still runs.

- **Wipe in**: a `<clipPath>` rect animates `width` from 0 to full.
- **Rock**: `animateTransform type="scale"` oscillates the horizontal scale
  (`1 → 0.82 → 1 → 1.04 → 1`), wrapped in `translate(cx) … translate(-cx)` so it
  pivots about the centre instead of the origin. Squashing horizontally is
  enough to read as a rotation about the vertical axis.

## Gotcha

SMIL attributes here are written to 2 decimal places. A `dur` that rounds to
`0.00s` never runs and the element stays at its `from` value — which is how you
get a blank panel. `make_ascii_svg.py` clamps its per-row duration to `0.05s`
for exactly this reason.

## Regenerating

```sh
python scripts/make_wordmark_svg.py SARAM -o wordmark.svg
python scripts/make_wordmark_svg.py SARAM --depth 4 --rock 3   # deeper, faster rock
```
