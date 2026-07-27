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


def test_state_dependent_font_weight_is_confined_to_the_monospace_axis() -> None:
    """Bolding a state is safe only where the face's advance cannot change.

    ``font-weight`` sits outside ``GEOMETRY_EXACT`` deliberately, so a state rule
    may bold its text. That is a claim about *this* face, not a general one, and
    the distinction is easy to get wrong: monospace pins one advance width per
    font instance, and says nothing about whether the advance is constant across
    positions on the weight axis. A variable font may widen with weight and still
    be monospace at every instance.

    So it was measured rather than inferred. Rendering the same string at weight
    400 and weight 700 at the axis position the nav actually inherits gave an
    identical advance (393.6015625px for a 41-character sample, delta exactly 0),
    and the current and peer nav rows measured identically at 40x196. Recursive's
    Mono holds its advance across the weight axis, which is what a code face has
    to do to stay usable in bold.

    That result only transfers while the rows really are on the monospace axis.
    This test pins that precondition: any rule that varies ``font-weight`` by
    state must not also move the element off ``MONO 1``, and no rule may override
    the axis for the nav. If a future design puts a state-bolded row on the
    proportional axis, the measurement no longer applies and this fails.
    """
    for name, css in _theme_sheets():
        for selectors, body in ownership.rules(css):
            declared = dict(ownership.declarations(body))
            if "font-weight" not in declared:
                continue
            if not is_state_selector(selectors):
                continue
            variation = declared.get("font-variation-settings", "")
            assert "MONO" not in variation or "MONO 1" in variation, (
                f"theme {name!r} bolds state rule {selectors.strip()!r} while "
                f"moving it off the monospace axis ({variation!r}); the advance "
                "invariance that makes state-dependent weight safe was measured "
                "at MONO 1 and does not transfer"
            )


def test_the_nav_inherits_the_monospace_axis_it_was_measured_on() -> None:
    """No rule takes nav rows off ``MONO 1``, where the weight measurement holds.

    The rows reach the monospace axis by inheritance — the axis token is 1 and
    the root applies it — rather than by any nav rule. That is easy to break
    silently by adding a nav rule that sets its own axis, which is why the
    absence is asserted rather than assumed.
    """
    for name, css in _theme_sheets():
        for selectors, body in ownership.rules(css):
            if "sb-nav" not in selectors:
                continue
            declared = dict(ownership.declarations(body))
            variation = declared.get("font-variation-settings")
            assert variation is None or "MONO 1" in variation, (
                f"theme {name!r} overrides the font axis on {selectors.strip()!r} "
                f"({variation!r}); nav rows must stay on the monospace axis"
            )
