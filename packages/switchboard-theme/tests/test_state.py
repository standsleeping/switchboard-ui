"""State-stable geometry: an interactive state may repaint but never reshape the box.

Philosophy §9 / companion §1: state changes must not unexpectedly alter layout
geometry. A hover, focus, selected, or disabled rule in the theme may change paint
(color, background, outline) freely, but it may not declare a property that changes
the box's size or position. A second guard keeps the focus ring inside the box:
now that every frame clips and the body cells scroll, an
outward ring would be clipped, so the offset must be non-positive (or a reserved
paint outset). These are theme guards, siblings to ``test_theme_css.py``.

The CSS reader is the shared :mod:`switchboard_ui.ownership` engine; the
state-markers and the geometry set are the theme's paint-side policy in
:mod:`ownership_policy`.
"""

import re

import switchboard_theme as themes
from switchboard_ui import ownership
from switchboard_ui.assets import read_asset

from .ownership_policy import is_geometry, is_state_selector


def _theme_sheets() -> list[tuple[str, str]]:
    """``(name, css)`` for every shipped theme."""
    return [
        (name, read_asset("switchboard_theme", f"{name}.css")) for name in themes.THEMES
    ]


def test_theme_state_rules_do_not_change_geometry() -> None:
    """A state may repaint but never reshape the box (state-stable layout)."""
    for name, css in _theme_sheets():
        for selectors, body in ownership.rules(css):
            if not is_state_selector(selectors):
                continue
            offenders = sorted(
                {p for p, _ in ownership.declarations(body) if is_geometry(p)}
            )
            assert not offenders, (
                f"theme {name!r} changes geometry on state rule {selectors.strip()!r}: "
                f"{offenders}; a state repaints, it does not reshape the box"
            )


def test_theme_focus_ring_stays_inside_the_box() -> None:
    """A focus ring draws inside the box (non-positive offset), so a clipping ancestor can't clip it."""
    for name, css in _theme_sheets():
        for selectors, body in ownership.rules(css):
            for prop, value in ownership.declarations(body):
                if prop != "outline-offset":
                    continue
                acceptable = (
                    value.startswith("-")
                    # A negated token (calc(-1 * var(...))) is inset by the same
                    # reading: the leading term makes the whole expression negative.
                    or value.startswith("calc(-")
                    or re.fullmatch(r"0(px|rem|em)?", value) is not None
                    or "var(--sb-fit-paint-outset" in value
                )
                assert acceptable, (
                    f"theme {name!r} uses outward focus-ring offset {value!r} on "
                    f"{selectors.strip()!r}; inset it (negative outline-offset) or "
                    "reserve --sb-fit-paint-outset"
                )
