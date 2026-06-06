"""The packaged stylesheet is structural layout only, with no visual style.

The CSS exists to make a Frame tree render as flex stacks. It controls geometry
(size, position, flow) and nothing else: no color, no type, no theming, no design
tokens. Visual style belongs to the host application, not to this package. The
two checks below enforce that from both sides: property *names* must be geometry
properties (this whitelist), and property *values* must carry no tokens or
theming (the blacklist below).
"""

import re

from switchboard_ui.assets import read_static

# The only properties the layout layer may declare: those that determine size,
# position, and flow. Appearance properties (color, background, border, font,
# box-shadow, ...) are deliberately absent, so adding one fails the build.
_LAYOUT_PROPERTIES = frozenset(
    {
        "display",
        # flexbox
        "flex",
        "flex-direction",
        "flex-grow",
        "flex-shrink",
        "flex-basis",
        "flex-wrap",
        "flex-flow",
        # grid
        "grid",
        "grid-template",
        "grid-template-rows",
        "grid-template-columns",
        "grid-template-areas",
        "grid-auto-rows",
        "grid-auto-columns",
        "grid-auto-flow",
        "grid-row",
        "grid-column",
        "grid-area",
        # alignment & distribution
        "gap",
        "row-gap",
        "column-gap",
        "align-items",
        "align-self",
        "align-content",
        "justify-items",
        "justify-self",
        "justify-content",
        "place-items",
        "place-self",
        "place-content",
        "order",
        # sizing (physical and logical)
        "width",
        "height",
        "min-width",
        "max-width",
        "min-height",
        "max-height",
        "inline-size",
        "block-size",
        "min-inline-size",
        "max-inline-size",
        "min-block-size",
        "max-block-size",
        "box-sizing",
        "aspect-ratio",
        # overflow / scroll
        "overflow",
        "overflow-x",
        "overflow-y",
        "overflow-inline",
        "overflow-block",
        # positioning
        "position",
        "top",
        "right",
        "bottom",
        "left",
        "inset",
        "inset-block",
        "inset-inline",
        "z-index",
        # box spacing (geometry)
        "margin",
        "margin-block",
        "margin-inline",
        "padding",
        "padding-block",
        "padding-inline",
    }
)


def _declared_properties(css: str) -> set[str]:
    """Every property declared inside a rule block (selectors excluded)."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    props: set[str] = set()
    for block in re.findall(r"\{([^{}]*)\}", css):
        for decl in block.split(";"):
            name, _, value = decl.partition(":")
            if value:
                props.add(name.strip().lower())
    return props


def test_layout_css_declares_only_layout_properties() -> None:
    """Every property in layout.css is a geometry property, never appearance."""
    declared = _declared_properties(read_static("layout.css"))
    assert declared, "no properties parsed; the regex or file path is wrong"
    non_layout = declared - _LAYOUT_PROPERTIES
    assert not non_layout, (
        f"layout.css declares non-layout properties: {sorted(non_layout)}"
    )


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
