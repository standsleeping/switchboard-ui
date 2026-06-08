"""State-stable geometry: an interactive state may repaint but never reshape the box.

Philosophy §9 / companion §1: state changes must not unexpectedly alter layout
geometry. A hover, focus, selected, or disabled rule in the theme may change paint
(color, background, outline) freely, but it may not declare a property that changes
the box's size or position. A second guard keeps the focus ring inside the box
(INSET_FOCUS_RING): now that every frame clips and the body cells scroll, an
outward ring would be clipped, so the offset must be non-positive (or a reserved
paint outset). These are theme guards, siblings to ``test_theme_css.py``.
"""

import re

from switchboard_ui import themes
from switchboard_ui.assets import read_asset

# Selector fragments that mark a rule as state-dependent. ``:focus`` also catches
# ``:focus-visible`` / ``:focus-within`` by substring.
_STATE_MARKERS = (
    ":hover",
    ":focus",
    ":active",
    ":disabled",
    ":enabled",
    ":checked",
    ":target",
    ":visited",
    ":indeterminate",
    "[aria-",
    "[data-state",
    "[disabled",
    "[checked",
    "[open",
)

# Properties that change a box's outer size or position. A state rule may declare
# none of these; paint (color, background, outline, box-shadow) is unrestricted.
_GEOMETRY_EXACT = frozenset(
    {
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
        "position",
        "top",
        "right",
        "bottom",
        "left",
        "gap",
        "row-gap",
        "column-gap",
        "font-size",
        "line-height",
    }
)
_GEOMETRY_PREFIX = ("padding", "margin", "inset", "flex")


def _rules(css: str) -> list[tuple[str, str]]:
    """``(selector-list, body)`` for each rule block, comments stripped."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    return re.findall(r"([^{}]+)\{([^{}]*)\}", css)


def _declarations(body: str) -> list[tuple[str, str]]:
    """``(property, value)`` pairs declared in a rule body."""
    out: list[tuple[str, str]] = []
    for decl in body.split(";"):
        name, sep, value = decl.partition(":")
        if sep:
            out.append((name.strip().lower(), value.strip()))
    return out


def _theme_sheets() -> list[tuple[str, str]]:
    """``(name, css)`` for every shipped theme."""
    return [
        (name, read_asset("switchboard_ui.themes", f"{name}.css"))
        for name in themes.THEMES
    ]


def _is_geometry(prop: str) -> bool:
    """Whether ``prop`` changes a box's outer size or position."""
    if prop in _GEOMETRY_EXACT:
        return True
    if any(prop == p or prop.startswith(p + "-") for p in _GEOMETRY_PREFIX):
        return True
    return prop == "border" or (prop.startswith("border") and prop.endswith("width"))


def _is_state_selector(selectors: str) -> bool:
    """Whether a selector list targets an interactive state."""
    return any(marker in selectors for marker in _STATE_MARKERS)


def test_theme_state_rules_do_not_change_geometry() -> None:
    """A state may repaint but never reshape the box (state-stable layout)."""
    for name, css in _theme_sheets():
        for selectors, body in _rules(css):
            if not _is_state_selector(selectors):
                continue
            offenders = sorted({p for p, _ in _declarations(body) if _is_geometry(p)})
            assert not offenders, (
                f"theme {name!r} changes geometry on state rule {selectors.strip()!r}: "
                f"{offenders}; a state repaints, it does not reshape the box"
            )


def test_theme_focus_ring_stays_inside_the_box() -> None:
    """A focus ring draws inside the box (non-positive offset), so a clipping ancestor can't clip it."""
    for name, css in _theme_sheets():
        for selectors, body in _rules(css):
            for prop, value in _declarations(body):
                if prop != "outline-offset":
                    continue
                acceptable = (
                    value.startswith("-")
                    or re.fullmatch(r"0(px|rem|em)?", value) is not None
                    or "var(--sb-fit-paint-outset" in value
                )
                assert acceptable, (
                    f"theme {name!r} uses outward focus-ring offset {value!r} on "
                    f"{selectors.strip()!r}; inset it (negative outline-offset) or "
                    "reserve --sb-fit-paint-outset (INSET_FOCUS_RING)"
                )
