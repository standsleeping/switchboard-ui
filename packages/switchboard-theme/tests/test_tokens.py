"""Themed tokens are authored per arm: light-dark() composes -light / -dark leaves.

A scheme-varying token splits into editable arm tokens (``--sb-x-light`` /
``--sb-x-dark``) composed into a public ``--sb-x`` with ``light-dark()``. The
theme-builder edits the arms (one ``setProperty`` per scheme value); the composed
token reprojects, so light-dark()'s dual value is never patched in place. These
guards keep every light-dark() in that exact shape with both arms defined, so the
builder (and any host) can always reach each scheme value through a single-valued
arm token. See PF ``planning/switchboard-ui/theme-layer.md`` (the token model).
"""

import re

import switchboard_theme as themes
from switchboard_ui.assets import read_asset

# A composed token: ``--sb-X: light-dark(var(--sb-X-light), var(--sb-X-dark))``.
_COMPOSED = re.compile(
    r"--sb-([\w-]+?)\s*:\s*light-dark\(\s*var\(--sb-\1-light\)\s*,\s*var\(--sb-\1-dark\)\s*\)"
)
_ANY_LIGHT_DARK = re.compile(r"light-dark\(")
_DEFINITION = re.compile(r"(--sb-[\w-]+)\s*:")


def _strip_comments(css: str) -> str:
    """Drop ``/* ... */`` blocks so prose mentioning light-dark() is not counted."""
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def _theme_sheets() -> list[tuple[str, str]]:
    """``(name, css)`` for every shipped theme, comments stripped."""
    return [
        (name, _strip_comments(read_asset("switchboard_theme", f"{name}.css")))
        for name in themes.THEMES
    ]


def test_every_light_dark_composes_matching_arms() -> None:
    """Every light-dark() is light-dark(var(--sb-X-light), var(--sb-X-dark)), never literal arms."""
    for name, css in _theme_sheets():
        composed = len(_COMPOSED.findall(css))
        total = len(_ANY_LIGHT_DARK.findall(css))
        assert composed == total, (
            f"theme {name!r} has {total - composed} light-dark() call(s) not in the form "
            "light-dark(var(--sb-X-light), var(--sb-X-dark)); a scheme-varying token must be "
            "authored as -light / -dark arms so the builder can edit each scheme value"
        )


def test_every_composed_token_defines_both_arms() -> None:
    """A composed --sb-X resolves to defined --sb-X-light and --sb-X-dark arm tokens."""
    for name, css in _theme_sheets():
        defined = set(_DEFINITION.findall(css))
        bases = set(_COMPOSED.findall(css))
        assert bases, (
            f"theme {name!r} composes no light-dark() arms; the model expects some"
        )
        for base in bases:
            for arm in (f"--sb-{base}-light", f"--sb-{base}-dark"):
                assert arm in defined, (
                    f"theme {name!r}: composed --sb-{base} references undefined {arm}"
                )
