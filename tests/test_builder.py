"""The theme builder generates its whole control surface from the token registry.

These guard the generation logic in :func:`showcase.build.build_theme_builder`:
one control per editable token (two for a scheme-varying arm pair), the structural
``fit`` contract excluded, and the wiring islands (apply + export) present. They
run through the public ``render_document`` so they exercise the real output.
"""

from showcase.build import build_theme_builder
from switchboard_theme import REGISTRY, Category, Themed
from switchboard_ui import render_document
from switchboard_ui.components import preview_items
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


def test_builder_renders_each_preview_item_in_a_light_and_dark_cell() -> None:
    """The preview matrix renders every sample item in a light cell and a dark
    cell, all sharing the builder scope so one edit repaints the matching arm in
    every cell."""
    html = render_document(build_theme_builder())
    cells = find(html, "div", **{"data-sb-scope": "builder-preview"})
    items = preview_items()
    assert len(cells) == 2 * len(items)
    light = [c for c in cells if "sb-preview-light" in c.get("class", "")]
    dark = [c for c in cells if "sb-preview-dark" in c.get("class", "")]
    assert len(light) == len(items)
    assert len(dark) == len(items)


def test_builder_carries_the_shared_mode_switch() -> None:
    """The header carries the shared scheme and density toggles, and the mode-state
    applier subscribes both — view controls, not token edits (they touch no token)."""
    html = render_document(build_theme_builder())
    scheme = find(
        html, "div", **{"data-island": "segmented", "data-pub": "scheme:changed"}
    )
    density = find(
        html, "div", **{"data-island": "segmented", "data-pub": "density:changed"}
    )
    assert len(scheme) == 1 and len(density) == 1
    applier = find(
        html,
        "div",
        **{"data-island": "mode-state", "data-sub": "scheme:changed,density:changed"},
    )
    assert len(applier) == 1


def test_builder_nav_links_each_category_to_a_real_section_anchor() -> None:
    """The category nav has one link per editable category, each scrolling to a
    section that actually exists in the controls column (no dangling jumps)."""
    html = render_document(build_theme_builder())
    categories: list[Category] = []
    for token in _EDITABLE:
        if token.category not in categories:
            categories.append(token.category)
    links = find(html, "a", **{"class": "sb-builder-nav-item"})
    assert len(links) == len(categories)
    anchors = {
        span["id"]
        for span in find(html, "span", **{"class": "sb-builder-section-anchor"})
    }
    for link in links:
        assert link["href"].lstrip("#") in anchors
