"""The contract layer: --sb-fit-* obligations flow one way (theme defines, structure consumes).

The Component Geometry Contract is the treaty between structure and theme. The
theme projects its causes (padding, font, border) into outer-box obligations
named ``--sb-fit-*``, and structure consumes those obligations without ever
seeing the causes ("share the projection, not the ingredients"). These guards
keep the flow one-directional: every ``--sb-fit-*`` token is *defined* only in a
theme and *consumed* (in ``layout.css`` or within a theme) only against a real
definition. Structure never defines an obligation; an obligation consumed but
defined nowhere is a dangling contract. This is the third seam, between
``test_layout_css.py`` (structure) and ``test_theme_css.py`` (paint).
"""

import re

import switchboard_theme as themes
from switchboard_ui.assets import read_asset, read_static

# A contract token in a definition position (``--sb-fit-x: ...``) versus a
# consumption position (``var(--sb-fit-x)``).
_DEFINITION = re.compile(r"(--sb-fit-[\w-]+)\s*:")
_CONSUMPTION = re.compile(r"var\(\s*(--sb-fit-[\w-]+)")


def _theme_sheets() -> list[tuple[str, str]]:
    """``(name, css)`` for every shipped theme."""
    return [
        (name, read_asset("switchboard_theme", f"{name}.css")) for name in themes.THEMES
    ]


def _defined_obligations() -> set[str]:
    """Every contract token defined across the shipped themes."""
    return {token for _, css in _theme_sheets() for token in _DEFINITION.findall(css)}


def test_structure_never_defines_a_contract_token() -> None:
    """layout.css consumes obligations; it never defines one (the theme owns the projection)."""
    defined_in_structure = sorted(set(_DEFINITION.findall(read_static("layout.css"))))
    assert not defined_in_structure, (
        f"layout.css defines contract tokens {defined_in_structure}; "
        "obligations are the theme's to publish and structure's to consume"
    )


def test_every_consumed_obligation_is_defined_by_a_theme() -> None:
    """A --sb-fit-* consumed in structure or a theme resolves to a theme definition."""
    consumed = set(_CONSUMPTION.findall(read_static("layout.css")))
    for _, css in _theme_sheets():
        consumed |= set(_CONSUMPTION.findall(css))
    dangling = sorted(consumed - _defined_obligations())
    assert not dangling, f"contract tokens consumed but defined by no theme: {dangling}"


# A structural fact in a definition position. The fact family (``--sb-chrome-*``)
# is the treaty's other direction: structure computes the pinned chrome's depth
# from what renders; a theme may compose a fact (an anchor clearing the pinned
# chrome) but never define one.
_FACT_DEFINITION = re.compile(r"(--sb-chrome-[\w-]+)\s*:")


def test_a_theme_never_defines_a_structural_fact() -> None:
    """Themes compose --sb-chrome-* facts; only structure defines them.

    A theme that redefined the chrome depth would fork a geometry two
    consumers — the sticky rail and the anchor clearance — must agree on.
    """
    for name, css in _theme_sheets():
        defined = sorted(set(_FACT_DEFINITION.findall(css)))
        assert not defined, f"theme {name!r} defines structural facts {defined}"
