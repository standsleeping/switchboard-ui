"""Shared edges are single-owned: a seam is one line, never drawn by both neighbours.

When tiled regions share an edge, drawing a full border
(or an all-sides inset ``box-shadow`` ring) on every cell doubles every interior
seam, and a seam's weight starts to depend on how many boxes meet there. The
theme draws seams *per edge* (a directional border or a directional inset shadow)
so each line has a single owner. This guard bans the all-sides anti-pattern on the
tiled layout hooks; the outer frame (``.sb-root``) is exempt — it is the sole
owner of the layout's perimeter, so an all-sides border there is single-owned by
definition. The full invariant (each seam drawn once across every adjacency) is
not statically checkable; this catches the wholesale-doubling anti-pattern, the
checkable part.

The CSS reader is the shared :mod:`switchboard_ui.ownership` engine; the tiled-hook
sets are the theme's paint-side policy in :mod:`ownership_policy`.
"""

import re

import switchboard_theme as themes
from switchboard_ui import ownership
from switchboard_ui.assets import read_asset

from .ownership_policy import REGION_HOOKS, TILED_HOOKS


def _theme_sheets() -> list[tuple[str, str]]:
    """``(name, css)`` for every shipped theme."""
    return [
        (name, read_asset("switchboard_theme", f"{name}.css")) for name in themes.THEMES
    ]


def _targets_a_tiled_hook(selectors: str) -> bool:
    """Whether any selector in the list targets a tiled region cell (root exempt)."""
    for selector in selectors.split(","):
        classes = ownership.subject_classes(selector)
        if "sb-root" not in classes and classes & TILED_HOOKS:
            return True
    return False


def _declarations_for_hook(css: str, hook: str) -> list[tuple[str, str]]:
    """Declarations whose subject carries ``hook``."""
    out: list[tuple[str, str]] = []
    for selectors, body in ownership.rules(css):
        if any(hook in ownership.subject_classes(s) for s in selectors.split(",")):
            out.extend(ownership.declarations(body))
    return out


def _is_all_sides_ring(box_shadow: str) -> bool:
    """Whether a ``box-shadow`` value is an inset ring (zero x/y offset → all sides).

    A directional seam shadow carries a non-zero x or y offset (it hugs one edge);
    a ring has zero offsets and a spread, so it outlines all four sides at once.
    """
    return any(
        re.match(r"inset\s+0(?:px|rem|em)?\s+0(?:px|rem|em)?\b", shadow.strip())
        for shadow in box_shadow.lower().split(",")
    )


def test_tiled_hooks_carry_no_all_sides_border() -> None:
    """A tiled region cell draws seams per edge, never an all-sides border shorthand."""
    for name, css in _theme_sheets():
        for selectors, body in ownership.rules(css):
            if not _targets_a_tiled_hook(selectors):
                continue
            properties = {p for p, _ in ownership.declarations(body)}
            offenders = properties & {"border", "border-width", "border-style"}
            assert not offenders, (
                f"theme {name!r} puts an all-sides {sorted(offenders)} on a tiled hook "
                f"({selectors.strip()!r}); draw seams per edge so each is single-owned"
            )


def test_root_remains_exempt_when_selector_is_compound() -> None:
    """The perimeter owner is not mistaken for a tiled frame."""
    assert not _targets_a_tiled_hook(".sb-frame.sb-root")
    assert _targets_a_tiled_hook(".app-shell > .sb-frame.sb-head-row")


def test_horizontal_seams_are_owned_by_rows_not_cell_fragments() -> None:
    """Each horizontal seam is one continuous logical border on its row."""
    expected = "var(--sb-border-width-thin) solid var(--sb-color-border)"
    for name, css in _theme_sheets():
        head = _declarations_for_hook(css, "sb-head-row")
        body = _declarations_for_hook(css, "sb-body-row")
        foot = _declarations_for_hook(css, "sb-foot-row")

        assert ("border-block-end", expected) in head, (
            f"theme {name!r} does not give the head/body seam to .sb-head-row"
        )
        assert ("border-block-start", expected) in foot, (
            f"theme {name!r} does not give the body/foot seam to .sb-foot-row"
        )

        assert not {p for p, _ in head} & {"border-block", "border-block-start"}
        assert not {p for p, _ in body} & {
            "border-block",
            "border-block-start",
            "border-block-end",
        }
        assert not {p for p, _ in foot} & {"border-block", "border-block-end"}

        for hook in REGION_HOOKS:
            properties = {p for p, _ in _declarations_for_hook(css, hook)}
            fragments = properties & {
                "border-block",
                "border-block-start",
                "border-block-end",
                "border-top",
                "border-bottom",
            }
            assert not fragments, (
                f"theme {name!r} fragments a horizontal row seam across .{hook}: "
                f"{sorted(fragments)}"
            )


def test_tiled_hooks_carry_no_all_sides_box_shadow_ring() -> None:
    """A tiled region cell draws a directional seam shadow, never an all-sides ring."""
    for name, css in _theme_sheets():
        for selectors, body in ownership.rules(css):
            if not _targets_a_tiled_hook(selectors):
                continue
            for prop, value in ownership.declarations(body):
                if prop != "box-shadow":
                    continue
                assert not _is_all_sides_ring(value), (
                    f"theme {name!r} rings a tiled hook ({selectors.strip()!r}) with an "
                    f"all-sides inset box-shadow {value!r}; offset it to one edge so the "
                    "seam is single-owned"
                )
