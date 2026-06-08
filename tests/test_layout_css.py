"""The packaged stylesheet is structural layout only, with no visual style.

The CSS controls geometry (size, position, flow) and nothing else. Four static
guards below keep it honest, so the layout layer cannot: name an appearance
property, use box-spacing (`margin` / `padding`), smuggle a design token into a
geometry value, or reach outside its own `.sb-*` elements.

  1. property names are geometry-only (the whitelist), excluding box-spacing;
  2. `margin` and `padding` are explicitly banned (the delegation note below);
  3. property values carry no tokens or theming (the blacklist);
  4. selectors target only `.sb-*`, never the host's `body` / `html` / `:root`.
"""

import re

from switchboard_ui.assets import read_static

# The only properties the layout layer may declare: those that determine size,
# position, and flow. Two deliberate exclusions, stricter than "no appearance":
#
#   margin  — banned outright (NEVER_MARGIN). Inter-element rhythm belongs to the
#             parent's `gap`; explicit gaps between regions to a structural
#             spacer; centering to `place-*` / `justify-*` / `align-*`. Banning it
#             removes margin collapsing (a top layout-bug source) and the
#             last-child-override dance, and makes spacing ownership unambiguous.
#   padding — also excluded (maximum-strict). `gap` is structural distribution; a
#             box's inset is a visual-density decision the theme owns, not the
#             structure. The layout layer distributes and sizes; it never insets.
#
# Appearance properties (color, background, border, font, box-shadow, ...) are
# absent for the same reason: adding any of these fails the build.
_LAYOUT_PROPERTIES = frozenset(
    {
        "display",
        # flexbox (sibling distribution lives here, via `gap`)
        "flex",
        "flex-direction",
        "flex-grow",
        "flex-shrink",
        "flex-basis",
        "flex-wrap",
        "flex-flow",
        "gap",
        "row-gap",
        "column-gap",
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


def _selectors(css: str) -> list[str]:
    """Every selector (comma-separated lists split out), comments stripped."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    out: list[str] = []
    for chunk in re.findall(r"([^{}]+)\{", css):
        for sel in chunk.split(","):
            sel = sel.strip()
            if sel:
                out.append(sel)
    return out


def test_layout_css_declares_only_layout_properties() -> None:
    """Every property in layout.css is a geometry property, never appearance."""
    declared = _declared_properties(read_static("layout.css"))
    assert declared, "no properties parsed; the regex or file path is wrong"
    non_layout = declared - _LAYOUT_PROPERTIES
    assert not non_layout, (
        f"layout.css declares non-layout properties: {sorted(non_layout)}"
    )


def test_layout_css_bans_margin_and_padding() -> None:
    """Box-spacing is delegated: rhythm is `gap`, insets are the theme's."""
    declared = _declared_properties(read_static("layout.css"))
    spacing = {p for p in declared if p.split("-", 1)[0] in {"margin", "padding"}}
    assert not spacing, f"layout.css uses banned box-spacing: {sorted(spacing)}"


def test_layout_css_selects_only_sb_classes() -> None:
    """The layer styles only its own .sb-* elements, never the host's body/:root."""
    foreign = [
        s for s in _selectors(read_static("layout.css")) if not s.startswith(".sb-")
    ]
    assert not foreign, f"layout.css selects non-sb elements: {foreign}"


def test_layout_css_is_flex_not_grid() -> None:
    """The layout is built from flex frames; no CSS grid template remains."""
    css = read_static("layout.css")
    assert ".sb-frame" in css
    assert "display: flex" in css
    assert "grid-template-areas" not in css


def test_layout_css_admits_only_contract_tokens() -> None:
    """Structure may consume contract obligations (--sb-fit-*), no other token, never theming.

    The three-way split: the layout layer stays free of paint tokens and of
    light/dark theming (those are *causes*, the theme's to own), but it may
    consume the projected *obligations* the theme publishes as ``--sb-fit-*``
    (a rail floors itself to ``--sb-fit-rail-block`` rather than guessing a
    fixed height). ``test_contract.py`` enforces that the flow is one-way.
    """
    css = read_static("layout.css")
    assert "light-dark(" not in css  # theming is a cause, never consumed by structure
    referenced = re.findall(r"var\(\s*(--[\w-]+)", css)
    non_contract = sorted({t for t in referenced if not t.startswith("--sb-fit-")})
    assert not non_contract, (
        f"layout.css references non-contract tokens {non_contract}; "
        "structure may consume only --sb-fit-* obligations"
    )
