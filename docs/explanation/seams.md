# Seams

A *seam* is the border line between two tiled regions of a layout. The three-column preset tiles the page into nine region cells (`head-l` through `foot-r`); the lines between those cells, and the frame around them, are seams. This page explains how the project draws them so that every line is crisp, uniform, and drawn exactly once.

## One line, one owner

When tiled cells share an edge, the tempting move is to give every cell a full border. That draws every interior seam *twice*, once by each neighbour, and a doubled hairline is not a thicker line: it is two 1px borders that can disagree on color, render on a fractional boundary, or stack to an uneven weight. The weight of a seam starts to depend on how many cells happen to meet there, which is not a property a seam should have.

The rule that avoids this is **single ownership**: every seam has exactly one owner (the cell, frame, or rule responsible for drawing it), and the neighbour on the other side of that seam draws nothing there. A seam's weight is then a property of the seam itself, never of its neighbourhood.

Single ownership is not specific to borders. It is the organizing rule across every layer of the page: each spatial or visual decision has exactly one owning layer. See [Ownership](ownership.md) for the general principle this page is one instance of.

## The layout is nested flex, not one grid

`three_column` builds nested flex frames: an outer column of three rows, each a row of three cells (see [Layout](layout.md) and [the three-column preset](../reference/three-column.md)). The nine cells never share a single parent, so there is no one grid container whose `gap` could paint every seam at once. Ownership is therefore assigned per edge: each seam is handed to one specific drawer. This page is the accepted cost of building the tiling from the recursive frame rather than one grid; [Layout](layout.md#why-nested-flex-not-grid) explains that choice.

## Three owners

The page's seams use three ownership patterns:

| Seam | Owner | Why it stays single |
|---|---|---|
| The perimeter (the four outer edges) | the root frame, `.sb-root`, with one all-sides border | no cell sits outside the frame, so nothing shares the outer edge |
| The two internal column seams | the center column cells, drawing both their inline-start and inline-end borders; the side columns draw neither | each vertical seam is owned by the center, never also by the rail beside it |
| The head/body seam | `.sb-head-row`, with `border-block-end` | one continuous row border replaces three cell-border fragments |
| The body/foot seam | `.sb-foot-row`, with `border-block-start` | one continuous row border replaces three cell-border fragments |

The horizontal boundaries are *semantic* seams: they separate chrome from content, and the theme draws them as part of its normal flat look. The preset gives the three rows explicit `.sb-head-row`, `.sb-body-row`, and `.sb-foot-row` hooks so the theme can assign each full-width seam to a row rather than repeating the border on its three cells. A visualization that wants the full grid reuses those row lines and adds only the seams the flat theme leaves out (the perimeter and the columns).

## Seams are borders

A seam is a `border` on the owning box's edge, and nothing else. The border sits outside the content box, so an opaque child surface (a preview pane, a filled island) can never paint over it. The fixed root carries `box-sizing: border-box` so its perimeter draws inside the viewport rather than pushing the frame past the edge. The two bordered rail rows are border-box too, keeping each hairline inside the rail's promised block size. Color and width come from tokens (`--sb-color-border`, `--sb-border-width-thin`), so a seam tracks the theme in both light and dark.

## Empty regions collapse

An omitted region is an empty cell that collapses (`display: none`), so optional slots leave no gap. The horizontal seams are unaffected because their row owners always render. A cell-owned vertical seam still requires its owner to render. The showcase already has real content in all three center cells, and a narrowly scoped CSS override reveals its empty corner cells for the 3×3 visualization. No placeholder islands are added: paint changes visibility, not application topology.

## The guard

The rule is enforced statically. `test_seams.py` (in `switchboard-theme`) rejects all-sides borders and rings on tiled cells and rows. It also verifies the stronger horizontal invariant directly: `.sb-head-row` owns the head/body seam, `.sb-foot-row` owns the body/foot seam, `.sb-body-row` owns neither, and no region cell draws a horizontal fragment. The root frame is exempt from the all-sides ban because it is the sole owner of the perimeter.

## Worked example: the showcase grid

The showcase outlines all nine regions so the layout reads as a 3×3. It is paint, not structure, and it lives in the showcase rather than the theme (the default theme stays flat). It is the three owners in full:

```css
/* Perimeter: the root is the sole owner. */
.sb-root {
  box-sizing: border-box;
  border: var(--sb-border-width-thin) solid var(--sb-color-border);
}

/* Empty demo cells remain structural cells without receiving fake content. */
.sb-head-row > .sb-frame:empty,
.sb-body-row > .sb-frame:empty,
.sb-foot-row > .sb-frame:empty {
  display: flex;
}

/* Column seams: the center column owns both; the side columns draw neither. */
.sb-head-c, .sb-body-c, .sb-foot-c {
  border-inline-start: var(--sb-border-width-thin) solid var(--sb-color-border);
  border-inline-end: var(--sb-border-width-thin) solid var(--sb-color-border);
}

/* Row seams come from the theme and are reused, not redrawn by the showcase. */
.sb-head-row {
  border-block-end: var(--sb-border-width-thin) solid var(--sb-color-border);
}
.sb-foot-row {
  border-block-start: var(--sb-border-width-thin) solid var(--sb-color-border);
}
```

## Extending the layout

The column owners above are tuned to three columns, but the recipe survives a change in their number. Keep the root as the sole perimeter owner, let row containers own full-width horizontal seams, and assign every internal column seam to exactly one of its two neighbouring cells. For more columns, the simplest uniform assignment is "every cell except the inline-end column owns the seam on its trailing edge". Whatever the assignment, walk every internal edge and confirm exactly one box draws it.
