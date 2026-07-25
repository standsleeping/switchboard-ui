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

# The center column as a document surface. It owns both of its inline seams
# (single-owner: the side columns draw neither), insets itself squarely at the
# document scale, and separates its islands with one gap. Its islands stretch to
# the column but cap at the content measure, so a wide viewport lengthens the
# margins rather than the lines. An anchored element clears the scroll owner's
# top edge, so following an in-page link never lands a heading flush against it.
_CONTENT_CSS = """
.sb-body-c {
  border-inline-start: var(--sb-border-width-thin) solid var(--sb-color-border);
  border-inline-end: var(--sb-border-width-thin) solid var(--sb-color-border);
  gap: var(--sb-space-lg);
  padding: var(--sb-space-3xl);
}
.sb-body-c > .sb-island {
  inline-size: 100%;
  max-inline-size: var(--sb-fit-content-inline);
}
.sb-body-c [id] {
  scroll-margin-block-start: var(--sb-space-md);
}
"""


def content_column_styles() -> str:
    """The content column's chrome CSS, for a host to inline in ``extra_head``."""
    return f"<style>{_CONTENT_CSS}</style>"
