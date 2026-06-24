"""The theme builder generates its whole control surface from the token registry.

These guard the generation logic in :func:`showcase.build.build_theme_builder`:
one control per editable token (two for a scheme-varying arm pair), the structural
``fit`` contract excluded, and the wiring islands (apply + export) present. They
run through the public ``render_document`` so they exercise the real output.
"""

from showcase.build import build_theme_builder
from switchboard_theme import REGISTRY, Category, Themed
from switchboard_ui import render_document
from tests.htmlprobe import find

_EDITABLE = tuple(t for t in REGISTRY if t.category is not Category.FIT)


def test_builder_generates_one_control_per_editable_token_arm() -> None:
    """Every non-fit token gets a control: two for a Themed arm pair, one for a value."""
    html = render_document(build_theme_builder())
    controls = find(html, "div", **{"data-island": "color-input"}) + find(
        html, "div", **{"data-island": "value-field"}
    )
    expected = sum(2 if isinstance(t.value, Themed) else 1 for t in _EDITABLE)
    assert len(controls) == expected


def test_builder_excludes_the_fit_contract() -> None:
    """The Component Geometry contract is structural, not taste; no fit token is
    bound to a control (the bindings carry the editable token set)."""
    html = render_document(build_theme_builder())
    (state,) = find(html, "div", **{"data-island": "theme-state"})
    assert "--sb-fit-" not in state["data-props"]


def test_builder_wires_an_apply_and_an_export_island() -> None:
    """The page carries the theme-state island (applies edits) and the export control."""
    html = render_document(build_theme_builder())
    assert find(html, "div", **{"data-island": "theme-state"})
    assert find(html, "div", **{"data-island": "theme-export"})


def test_builder_renders_two_preview_panes_sharing_the_scope() -> None:
    """A side-by-side light/dark preview, both panes the same scope so one edit
    repaints the matching arm in each."""
    html = render_document(build_theme_builder())
    panes = find(html, "div", **{"data-sb-scope": "builder-preview"})
    assert len(panes) == 2
