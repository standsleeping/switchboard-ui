"""Density is a mode that flows through tokens, never local corrections.

Philosophy §14 / companion §4: a density mode (compact / regular / spacious) must
alter named tokens and contracts, not introduce scattered concrete overrides. The
theme selects density with ``data-density`` on the root and reassigns only its
cause tokens; the ``--sb-fit-*`` contract reprojects automatically because the
obligations are calc over those tokens. This guard keeps a density rule honest: it
may set custom properties (``--sb-*``) and nothing else.
"""

import re

import switchboard_theme as themes
from switchboard_ui.assets import read_asset


def _rules(css: str) -> list[tuple[str, str]]:
    """``(selector-list, body)`` for each rule block, comments stripped."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    return re.findall(r"([^{}]+)\{([^{}]*)\}", css)


def _properties(body: str) -> list[str]:
    """The property names declared in a rule body."""
    names: list[str] = []
    for decl in body.split(";"):
        name, sep, _ = decl.partition(":")
        if sep:
            names.append(name.strip().lower())
    return names


def _theme_sheets() -> list[tuple[str, str]]:
    """``(name, css)`` for every shipped theme."""
    return [
        (name, read_asset("switchboard_theme", f"{name}.css")) for name in themes.THEMES
    ]


def test_density_rules_reassign_only_tokens() -> None:
    """A ``[data-density]`` rule sets custom properties only, never concrete geometry or paint."""
    found_density_rule = False
    for name, css in _theme_sheets():
        for selectors, body in _rules(css):
            if "[data-density" not in selectors:
                continue
            found_density_rule = True
            concrete = sorted(p for p in _properties(body) if not p.startswith("--"))
            assert not concrete, (
                f"theme {name!r} density rule {selectors.strip()!r} sets concrete "
                f"properties {concrete}; a mode flows through tokens, not local corrections"
            )
    assert found_density_rule, (
        "no theme defines a density mode; ship one as proof of the axis"
    )
