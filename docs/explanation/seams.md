# Explanation: seams

A *seam* is the border line between two tiled regions of a layout. The three-column preset tiles the page into nine region cells (`head-l` through `foot-r`); the lines between those cells, and the frame around them, are seams. This page explains how the project draws them so that every line is crisp, uniform, and drawn exactly once.

## One line, one owner

When tiled cells share an edge, the tempting move is to give every cell a full border. That draws every interior seam *twice*, once by each neighbour, and a doubled hairline is not a thicker line: it is two 1px borders that can disagree on colour, render on a fractional boundary, or stack to an uneven weight. The weight of a seam starts to depend on how many cells happen to meet there, which is not a property a seam should have.

The rule that avoids this is **single ownership**: every seam has exactly one owner (the cell, frame, or rule responsible for drawing it), and the neighbour on the other side of that seam draws nothing there. A seam's weight is then a property of the seam itself, never of its neighbourhood.

## The layout is nested flex, not one grid

`three_column` builds nested flex frames: an outer column of three rows, each a row of three cells (see [Layout](layout.md) and [the three-column preset](../reference/three-column.md)). The nine cells never share a single parent, so there is no one grid container whose `gap` could paint every seam at once. Ownership is therefore assigned per edge: each seam is handed to one specific drawer.

## Three owners

The page's seams fall into three groups, each with one kind of owner:

| Seam | Owner | Why it stays single |
|---|---|---|
| The perimeter (the four outer edges) | the root frame, `.sb-root`, with one all-sides border | no cell sits outside the frame, so nothing shares the outer edge |
| The two internal column seams | the centre column cells, drawing both their inline-start and inline-end borders; the side columns draw neither | each vertical seam is owned by the centre, never also by the rail beside it |
| The two internal row seams | the theme's rail hairlines (the head row's bottom border, the foot row's top border) | the theme already draws these; reusing a single-owned line keeps it single-owned |

The third group is the one to dwell on. The head/body and body/foot boundaries are *semantic* seams: they separate chrome from content, and the theme draws them as part of its normal flat look. A visualization that wants the full grid does not redraw them, because redrawing is exactly the doubling the rule forbids. It reuses the theme's line and adds only the seams the flat theme leaves out (the perimeter and the columns).

## Seams are borders

A seam is a `border` on the owning box's edge, and nothing else. The border sits outside the content box, so an opaque child surface (a preview pane, a filled island) can never paint over it. The fixed root carries `box-sizing: border-box` so its border draws inside the viewport rather than pushing the frame one pixel past the edge. Colour and width come from tokens (`--sb-color-border`, `--sb-border-width-thin`), so a seam tracks the theme in both light and dark.

## Empty regions collapse

An omitted region is an empty cell that collapses (`display: none`), so optional slots leave no gap. Single-owner assignment assumes the owning cell is present: if the owner of a seam can be empty, either reassign that seam to a cell that always renders, or place content so the owner renders. The showcase fills its four corners with labels for exactly this reason, so all nine cells draw and the grid is complete.

## The guard

The rule is enforced statically. `test_seams.py` (in `switchboard-theme`) fails the build if a tiled region cell (`.sb-head-*`, `.sb-body-*`, `.sb-foot-*`, or the `.sb-frame` / `.sb-rail` hooks) carries an all-sides border. The root frame is exempt, because it is the sole owner of the perimeter and an all-sides border there is single-owned by definition. The full invariant (each seam drawn once across every adjacency) is not statically checkable; the guard catches the wholesale-doubling anti-pattern, which is the checkable part.

## Worked example: the showcase grid

The showcase outlines all nine regions so the layout reads as a 3×3. It is paint, not structure, and it lives in the showcase rather than the theme (the default theme stays flat). It is the three owners in full:

```css
/* Perimeter: the root is the sole owner. */
.sb-root {
  box-sizing: border-box;
  border: var(--sb-border-width-thin) solid var(--sb-color-border);
}

/* Column seams: the centre column owns both; the side columns draw neither. */
.sb-head-c, .sb-body-c, .sb-foot-c {
  border-inline-start: var(--sb-border-width-thin) solid var(--sb-color-border);
  border-inline-end: var(--sb-border-width-thin) solid var(--sb-color-border);
}

/* Row seams: the theme's own rail hairlines, reused (not redrawn here). */
```

## Extending the layout

The owners above are tuned to three columns, but the recipe survives a change in their number. Keep the root as the sole perimeter owner, and assign every internal seam to exactly one of its two neighbours. For more columns, the simplest uniform assignment is "every cell except the inline-end column owns the seam on its trailing edge", which scales without re-tuning. Whatever the assignment, the check is always the same: walk every internal edge and confirm exactly one side draws it.
