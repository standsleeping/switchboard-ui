"""Page chrome: the theme's opt-in paint for the layout's own regions.

The shipped theme sheet paints components; it may never inset or otherwise dress
a *region* of the layout, because a region is the mechanism's structural
vocabulary and a box's inset belongs to a control or content surface (the
``STRUCTURAL_HOOKS`` denylist in :mod:`switchboard_ui.ownership` holds that line,
and ``test_theme_css.py`` enforces it). Chrome that dresses a region therefore
ships here instead: a host opts it in through ``extra_head``, exactly as it opts
in :func:`switchboard_theme.modes.mode_switch_styles` for the head rail.

:func:`content_column_styles` is the document shape — the reading column every
docs-and-listings site converges on. A host with a different shape (a gallery
that wants the full viewport width) simply does not call it, or overrides the
few declarations after it; nothing here is load-bearing for the layout, which
stands up unpainted.
"""

# The center column as a document surface. It insets itself squarely at the
# document scale and separates its islands with one gap. Its islands stretch to
# the column but cap at the content measure, so a wide viewport lengthens the
# margins rather than the lines.
#
# A wide island may opt out of the measure cap and *bleed*: it keeps its start
# edge on the prose line and widens by exactly the column's end inset, so its
# scroll window runs to the column's end seam and a row cut by scrolling ends
# at a line the reader can see, never mid-air. Two grades: `sb-bleed-column`
# keeps the grid at the inset width (cells wrap; only an unbreakable cell
# widens into the bleed), `sb-bleed-content` lets the grid size to its content
# from that floor. The bleed is measured with the same token as the inset, so
# the two cannot drift apart. The class sits on the island, whose cap the
# island-specific rule releases so the bleed spans the column at every width —
# or on a block-level wrapper inside one (a host whose islands are whole
# sections bleeds the one wide block within), where it is measured from the
# island, which keeps its cap: the wrapper overhangs the prose line by the
# inset, and its edge meets the column's end seam only while the column is no
# wider than the measure. Past that width the margins grow and the overhang
# ends inside them — still a deliberate, token-sized edge, no longer the seam.
#
# An anchored element clears the scroll owner's top edge plus whatever chrome
# is pinned above it: the structural sheet publishes the pinned chrome's depth
# (`--sb-chrome-block-start`), which is unset outside a flowing root, so a
# workbench's anchors clear only the breathing space.
# The column's two seams are not drawn here: the theme sheet draws them in both
# shapes, each only where a rendered neighbour shares the edge.
_CONTENT_CSS = """
.sb-body-c {
  gap: var(--sb-space-lg);
  padding: var(--sb-space-3xl);
}
.sb-body-c > .sb-island {
  inline-size: 100%;
  max-inline-size: var(--sb-fit-content-inline);
}
.sb-body-c [id] {
  scroll-margin-block-start: calc(var(--sb-chrome-block-start, 0px) + var(--sb-space-md));
}
.sb-body-c > .sb-island.sb-bleed-column,
.sb-body-c > .sb-island.sb-bleed-content {
  max-inline-size: none;
}
.sb-body-c .sb-bleed-column,
.sb-body-c .sb-bleed-content {
  inline-size: calc(100% + var(--sb-space-3xl));
  min-inline-size: 0;
}
.sb-bleed-column .sb-table,
.sb-bleed-content .sb-table {
  min-inline-size: 0;
}
.sb-bleed-column .sb-table-grid {
  inline-size: calc(100% - var(--sb-space-3xl));
}
.sb-bleed-content .sb-table-grid {
  inline-size: max-content;
  min-inline-size: calc(100% - var(--sb-space-3xl));
}
"""


def content_column_styles() -> str:
    """The content column's chrome CSS, for a host to inline in ``extra_head``."""
    return f"<style>{_CONTENT_CSS}</style>"
