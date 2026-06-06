"""The packaged stylesheet is structural layout only, with no visual style.

The CSS exists to make a Frame tree render as flex stacks. It carries no design
tokens, no theming, and no color: visual style belongs to the host application,
not to this package.
"""

from switchboard_ui.assets import read_static


def test_layout_css_is_flex_not_grid() -> None:
    """The layout is built from flex frames; no CSS grid template remains."""
    css = read_static("layout.css")
    assert ".sb-frame" in css
    assert "display: flex" in css
    assert "grid-template-areas" not in css


def test_layout_css_carries_no_design_tokens_or_theming() -> None:
    """The stylesheet holds layout structure only: no tokens, no theming."""
    css = read_static("layout.css")
    assert "var(--" not in css  # no design tokens
    assert "light-dark(" not in css  # no light/dark theming
