# How the 3D ASCII wordmark is built

`scripts/make_wordmark_svg.py` turns a word into an extruded ASCII slab. There
is no 3D engine involved — it's a 2D grid with one occlusion rule.

## 1. Block glyphs, upscaled

Each letter is a 5x7 grid of `#` in the `GLYPHS` table. Before anything else,
every cell is blown up into an `sx` x `sy` block (default 2x3).

This upscale is the whole reason the wordmark is readable. A 1-cell stroke has
nothing behind it, so its extrusion trail smears diagonally across the letter's
own counters. A 2-cell stroke has a body, and step 2 lets that body hide its
own trail.

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

## 3. Terminal chrome

`scripts/termframe.py` draws the macOS window shared by all three panels:
rounded border, title bar, three traffic lights, and a centred prompt. It
returns the content box, and each panel scales its grid to fit inside it —
so no panel can overflow its own window.

## 4. Rendering

Rows become `<text>` elements. Each one carries:

```
textLength="<chars * cw>" lengthAdjust="spacingAndGlyphs"
```

This pins the character grid to exact coordinates. Without it the columns drift
apart on any machine whose default monospace font has a different advance width
— which, for a README rendered on other people's browsers, is most of them.

## 5. Animation

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
