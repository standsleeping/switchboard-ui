"""Forbidden techniques in the theme: it never positions or transforms.

Philosophy §16 ("Forbidden and Suspicious Techniques"). The theme is paint, so it
never positions an element or moves it with a transform: positioning is
structure's coordinate-system concern, and transforms are the classic
visual-alignment hack (this also discharges the deferred alignment-anchor rule,
plan step 10). The companion structural guard ("structure carries no magic
numbers") lives with the layer it guards, in ``test_layout_css.py``.

The CSS reader is the shared :mod:`switchboard_ui.ownership` engine; the forbidden
set is the theme's paint-side policy in :mod:`ownership_policy`.
"""

import switchboard_theme as themes
from switchboard_ui import ownership
from switchboard_ui.assets import read_asset

from .ownership_policy import is_forbidden


def _theme_sheets() -> list[tuple[str, str]]:
    """``(name, css)`` for every shipped theme."""
    return [
        (name, read_asset("switchboard_theme", f"{name}.css")) for name in themes.THEMES
    ]


def test_theme_does_not_position_or_transform() -> None:
    """The theme paints; it never positions or transforms (structure owns coordinates)."""
    for name, css in _theme_sheets():
        forbidden = sorted(
            p for p in ownership.declared_properties(css) if is_forbidden(p)
        )
        assert not forbidden, (
            f"theme {name!r} uses {forbidden}; the theme does not position or transform "
            "(structure owns coordinate systems; transforms are alignment hacks)"
        )


def test_theme_never_animates_scrolling() -> None:
    """`scroll-behavior` is absent from every theme: jumps stay instant.

    Anchor landings and restorations are single-step in every engine, and a
    reader's reduced-motion preference needs nothing disabled, because no theme
    introduces an animation to disable.
    """
    for name, css in _theme_sheets():
        assert "scroll-behavior" not in ownership.declared_properties(css), (
            f"theme {name!r} declares scroll-behavior; scrolling is never animated"
        )
