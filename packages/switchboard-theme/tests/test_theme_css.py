"""The theme paints freely but obeys the padding allowlist: a guard, like layout.css.

This is the inverse of the layout.css guards. The theme *may* use appearance,
tokens, and light/dark theming, and *may* select non-.sb-* elements (it paints
content). What it may not do is attach box-spacing where it does not belong:
``padding`` insets a control or content surface and may never land on a layout,
mount, or region hook, and ``margin`` never appears. Padding a structural hook
fails the build.

The inset rule is read as a denylist, not an allowlist: a box's inset belongs to a
control or surface (an open set that grows with the components), so the guard asks
only that padding never target one of the mechanism's closed set of structural
hooks (``switchboard_ui.ownership.STRUCTURAL_HOOKS``). It guards the floor (never
inset a layout hook) and leaves the taste (which control insets) to the author.

Vanilla ``default.css`` stays freely editable (the theme is shaped by sight against
the showcase); this guard is the backstop that keeps a tweak from regressing the
rule, the same way ``test_layout_css.py`` backstops the structural layer. The CSS
reader and the structural-hook denylist are the shared :mod:`switchboard_ui.ownership`
engine.
"""

import switchboard_theme as themes
from switchboard_ui import ownership
from switchboard_ui.assets import read_asset


def _theme_sheets() -> list[tuple[str, str]]:
    """``(name, css)`` for every shipped theme."""
    return [
        (name, read_asset("switchboard_theme", f"{name}.css")) for name in themes.THEMES
    ]


def test_theme_never_pads_a_structural_hook() -> None:
    """Padding insets a control or surface; it never lands on a layout/mount/region hook."""
    for name, css in _theme_sheets():
        rules = ownership.rules(css)
        assert rules, f"no rules parsed from theme {name!r}; the regex or path is wrong"
        for selectors, body in rules:
            if not ownership.declares(ownership.properties(body), "padding"):
                continue
            for selector in selectors.split(","):
                hooks = ownership.subject_classes(selector) & ownership.STRUCTURAL_HOOKS
                assert not hooks, (
                    f"theme {name!r} pads structural hook(s) {sorted(hooks)} via "
                    f"{selector.strip()!r}; padding insets a control or content surface, "
                    f"never a layout, mount, or region hook"
                )


def test_the_viewport_gutter_is_reserved_for_the_flow_root_only() -> None:
    """The page that scrolls reserves its bar's width; the locked page never does.

    Reserving on every root shrinks a viewport root's initial containing block
    by one classic scrollbar, so the locked root stops one bar short of the
    window with a dead strip no bar can occupy. Every Document declares a root
    mode, so the positive form needs no default.
    """
    for name in themes.THEMES:
        css = read_asset("switchboard_theme", f"{name}.css")
        reserving = {
            selectors.strip()
            for selectors, body in ownership.rules(css)
            if "scrollbar-gutter" in body
        }
        assert reserving == {":root:has(.sb-root-flow)"}


def test_theme_uses_no_margin() -> None:
    """The theme never uses margin; rhythm is gap, inset is padding."""
    for name, css in _theme_sheets():
        for selectors, body in ownership.rules(css):
            assert not ownership.declares(ownership.properties(body), "margin"), (
                f"theme {name!r} uses margin on {selectors.strip()!r}"
            )
