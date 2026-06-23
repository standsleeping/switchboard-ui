"""Forbidden techniques in the theme: it never positions or transforms.

Philosophy §16 ("Forbidden and Suspicious Techniques"). The theme is paint, so it
never positions an element or moves it with a transform: positioning is
structure's coordinate-system concern, and transforms are the classic
visual-alignment hack (this also discharges the deferred alignment-anchor rule,
plan step 10). The companion structural guard ("structure carries no magic
numbers") lives with the layer it guards, in ``test_layout_css.py``.
"""

import re

import switchboard_theme as themes
from switchboard_ui.assets import read_asset


def _declared_properties(css: str) -> list[str]:
    """Every property name declared across all rule bodies."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    props: list[str] = []
    for body in re.findall(r"\{([^{}]*)\}", css):
        for decl in body.split(";"):
            name, sep, _ = decl.partition(":")
            if sep:
                props.append(name.strip().lower())
    return props


def _theme_sheets() -> list[tuple[str, str]]:
    """``(name, css)`` for every shipped theme."""
    return [
        (name, read_asset("switchboard_theme", f"{name}.css")) for name in themes.THEMES
    ]


def test_theme_does_not_position_or_transform() -> None:
    """The theme paints; it never positions or transforms (structure owns coordinates)."""
    for name, css in _theme_sheets():
        forbidden = sorted(
            p
            for p in set(_declared_properties(css))
            if p == "position" or p == "transform" or p.startswith("transform-")
        )
        assert not forbidden, (
            f"theme {name!r} uses {forbidden}; the theme does not position or transform "
            "(structure owns coordinate systems; transforms are alignment hacks)"
        )
