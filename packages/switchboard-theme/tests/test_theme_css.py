"""The theme paints freely but obeys the padding allowlist: a guard, like layout.css.

This is the inverse of the layout.css guards. The theme *may* use appearance,
tokens, and light/dark theming, and *may* select non-.sb-* elements (it paints
content). What it may not do is attach box-spacing where it does not belong:
``padding`` may target only an allowlisted control (the subject of its rule), and
``margin`` never appears. Padding on a layout, mount, or region
hook fails the build.

Vanilla ``default.css`` stays freely editable (the theme is shaped by sight against
the showcase); this guard is the backstop that keeps a tweak from regressing the
rule, the same way ``test_layout_css.py`` backstops the structural layer.
"""

import re

import switchboard_theme as themes
from switchboard_ui.assets import read_asset

# The only selectors padding may target: controls, where padding is the hit
# target. Widen deliberately, and never to a layout / mount / region selector, as
# real controls and tables arrive (input, select, textarea, td, th).
# `.sb-segmented-option` is a control (a tab button); the class is its subject
# because its paint overrides the base `button` rule by specificity.
# `.sb-color-input-text` is the hex field, a control whose inset is the theme's.
# `.sb-value-field-text` is the general value field, the same kind of control.
# `.sb-popover-panel` is a floating content surface that insets its own content.
# `th` / `td` are table cells, whose inset is the cell's own (the canonical case).
_PADDABLE_SUBJECTS = frozenset(
    {
        "button",
        ".sb-segmented-option",
        ".sb-color-input-text",
        ".sb-value-field-text",
        ".sb-popover-panel",
        "th",
        "td",
    }
)


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


def _declares(properties: list[str], prop: str) -> bool:
    """Whether ``prop`` or any ``prop-*`` longhand is declared."""
    return any(p == prop or p.startswith(prop + "-") for p in properties)


def _subject(selector: str) -> str:
    """The rightmost compound selector, stripped of pseudos and attributes."""
    last = re.split(r"\s*[>+~]\s*|\s+", selector.strip())[-1]
    return re.split(r"::|:|\[", last)[0]


def _theme_sheets() -> list[tuple[str, str]]:
    """``(name, css)`` for every shipped theme."""
    return [
        (name, read_asset("switchboard_theme", f"{name}.css")) for name in themes.THEMES
    ]


def test_theme_padding_only_targets_allowlisted_controls() -> None:
    """Padding appears only on an allowlisted control, never on an .sb-* hook."""
    for name, css in _theme_sheets():
        rules = _rules(css)
        assert rules, f"no rules parsed from theme {name!r}; the regex or path is wrong"
        for selectors, body in rules:
            if not _declares(_properties(body), "padding"):
                continue
            for selector in selectors.split(","):
                subject = _subject(selector)
                assert subject in _PADDABLE_SUBJECTS, (
                    f"theme {name!r} pads {selector.strip()!r} (subject {subject!r}); "
                    f"padding allowlist: {sorted(_PADDABLE_SUBJECTS)}"
                )


def test_theme_uses_no_margin() -> None:
    """The theme never uses margin; rhythm is gap, inset is padding."""
    for name, css in _theme_sheets():
        for selectors, body in _rules(css):
            assert not _declares(_properties(body), "margin"), (
                f"theme {name!r} uses margin on {selectors.strip()!r}"
            )
