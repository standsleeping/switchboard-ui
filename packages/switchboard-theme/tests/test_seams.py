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
"""

import re

import switchboard_theme as themes
from switchboard_ui.assets import read_asset

# The tiled layout cells — they share edges with siblings. `.sb-root` (the outer
# frame) and `.sb-island` (a mount point, not a tiled region) are not cells.
_TILED = re.compile(r"^\.sb-(?:head|body|foot)-[lcr]$|^\.sb-(?:frame|rail)$")


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
            out.append((name.strip().lower(), value.strip().lower()))
    return out


def _subject(selector: str) -> str:
    """The rightmost compound selector, stripped of pseudos and attributes."""
    last = re.split(r"\s*[>+~]\s*|\s+", selector.strip())[-1]
    return re.split(r"::|:|\[", last)[0]


def _targets_a_tiled_hook(selectors: str) -> bool:
    """Whether any selector in the list targets a tiled region cell."""
    return any(_TILED.match(_subject(s)) for s in selectors.split(","))


def _is_all_sides_ring(box_shadow: str) -> bool:
    """Whether a ``box-shadow`` value is an inset ring (zero x/y offset → all sides).

    A directional seam shadow carries a non-zero x or y offset (it hugs one edge);
    a ring has zero offsets and a spread, so it outlines all four sides at once.
    """
    return any(
        re.match(r"inset\s+0(?:px|rem|em)?\s+0(?:px|rem|em)?\b", shadow.strip())
        for shadow in box_shadow.split(",")
    )


def _theme_sheets() -> list[tuple[str, str]]:
    """``(name, css)`` for every shipped theme."""
    return [
        (name, read_asset("switchboard_theme", f"{name}.css")) for name in themes.THEMES
    ]


def test_tiled_hooks_carry_no_all_sides_border() -> None:
    """A tiled region cell draws seams per edge, never an all-sides border shorthand."""
    for name, css in _theme_sheets():
        for selectors, body in _rules(css):
            if not _targets_a_tiled_hook(selectors):
                continue
            properties = {p for p, _ in _declarations(body)}
            offenders = properties & {"border", "border-width"}
            assert not offenders, (
                f"theme {name!r} puts an all-sides {sorted(offenders)} on a tiled hook "
                f"({selectors.strip()!r}); draw seams per edge so each is single-owned"
            )


def test_tiled_hooks_carry_no_all_sides_box_shadow_ring() -> None:
    """A tiled region cell draws a directional seam shadow, never an all-sides ring."""
    for name, css in _theme_sheets():
        for selectors, body in _rules(css):
            if not _targets_a_tiled_hook(selectors):
                continue
            for prop, value in _declarations(body):
                if prop != "box-shadow":
                    continue
                assert not _is_all_sides_ring(value), (
                    f"theme {name!r} rings a tiled hook ({selectors.strip()!r}) with an "
                    f"all-sides inset box-shadow {value!r}; offset it to one edge so the "
                    "seam is single-owned"
                )
