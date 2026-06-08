"""Forbidden techniques: the theme never positions or transforms; structure has no magic numbers.

Philosophy §16 ("Forbidden and Suspicious Techniques"), two seams. The theme is
paint, so it never positions an element or moves it with a transform: positioning
is structure's coordinate-system concern, and transforms are the classic
visual-alignment hack (this also discharges the deferred alignment-anchor rule,
plan step 10). Structure carries no magic numbers: every dimension is a token, a
keyword, zero, or a percentage, never a bare absolute length, which would be an
un-owned number (the rail-height mistake the contract layer fixed).
"""

import re

from switchboard_ui import themes
from switchboard_ui.assets import read_asset, read_static


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
        (name, read_asset("switchboard_ui.themes", f"{name}.css"))
        for name in themes.THEMES
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


def test_structure_has_no_magic_number_lengths() -> None:
    """layout.css carries no bare absolute length: every dimension is a token, keyword, 0, or %."""
    css = re.sub(r"/\*.*?\*/", "", read_static("layout.css"), flags=re.DOTALL)
    css = re.sub(r"var\([^)]*\)", "", css)  # token contents are owned, not magic
    bodies = " ".join(re.findall(r"\{([^{}]*)\}", css))
    lengths = re.findall(r"(\d*\.?\d+)(px|rem|em|cm|mm|pt|pc|in)\b", bodies)
    magic = sorted({f"{n}{unit}" for n, unit in lengths if float(n) != 0})
    assert not magic, (
        f"layout.css has bare absolute lengths {magic}; a structural dimension must be a "
        "token, keyword, 0, or %, never an un-owned number (use a --sb-fit-* obligation)"
    )
