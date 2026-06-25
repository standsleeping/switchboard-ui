"""The dogfood showcase visualizes layout without changing application topology."""

from showcase.build import build_showcase, showcase_styles
from switchboard_ui import render_document
from switchboard_ui.model import Frame, Slot
from tests.htmlprobe import find


def test_showcase_keeps_corner_regions_empty() -> None:
    """Grid paint must not invent placeholder islands to keep empty cells visible."""
    document = build_showcase()
    head, _, foot = document.body.children
    assert isinstance(head, Frame)
    assert isinstance(foot, Frame)
    for row in (head, foot):
        for position in (0, 2):
            cell = row.children[position]
            assert isinstance(cell, Slot)
            assert isinstance(cell.child, Frame)
            assert cell.child.children == ()

    html = render_document(document)
    assert not find(html, "div", **{"data-island": "region"})
    for region in ("head-l", "head-r", "foot-l", "foot-r"):
        assert find(
            html,
            "div",
            **{"class": f"sb-frame sb-frame-column sb-{region}"},
        )


def test_showcase_styles_carry_the_three_column_chrome() -> None:
    """The gallery paints its own column seams, nav, and inspector (host chrome)."""
    css = showcase_styles()
    assert ".sb-body-c" in css  # the centre column owns both column seams
    assert ".sb-gallery-nav" in css
    assert ".sb-gallery-inspector" in css


_EXPECTED_IDS = [
    "segmented",
    "slider",
    "color-picker",
    "popover",
    "modal",
    "value-field",
    "preview",
    "table",
    "code-block",
]


def test_showcase_nav_publishes_selection_and_inspector_subscribes() -> None:
    """The nav publishes gallery:select across regions; the inspector subscribes it."""
    html = render_document(build_showcase())
    (nav,) = find(html, "div", **{"data-island": "gallery-nav"})
    assert nav["data-pub"] == "gallery:select"
    (inspector,) = find(html, "div", **{"data-island": "gallery-inspector"})
    assert inspector["data-sub"] == "gallery:select"


def test_showcase_nav_lists_every_component_with_the_first_active() -> None:
    """The nav has one in-page anchor per specimen; the first specimen is active."""
    html = render_document(build_showcase())
    items = find(html, "a", **{"class": "sb-gallery-nav-item"})
    assert [it["data-id"] for it in items] == _EXPECTED_IDS
    assert [it["href"] for it in items] == [f"#sec-{i}" for i in _EXPECTED_IDS]
    active = [it["data-id"] for it in items if it.get("aria-current") == "true"]
    assert active == ["segmented"]


def test_showcase_inspector_shows_only_the_active_panel_at_first_paint() -> None:
    """Every component gets an inspector panel; only the first is unhidden initially."""
    html = render_document(build_showcase())
    panels = find(html, "div", **{"class": "sb-gallery-inspector-panel"})
    assert [p["data-id"] for p in panels] == _EXPECTED_IDS
    visible = [p["data-id"] for p in panels if "hidden" not in p]
    assert visible == ["segmented"]


def test_showcase_content_anchors_match_the_nav_targets() -> None:
    """Each specimen heading carries the id its nav anchor scrolls to."""
    html = render_document(build_showcase())
    headings = find(html, "div", **{"class": "sb-gallery-heading"})
    assert [h["id"] for h in headings] == [f"sec-{i}" for i in _EXPECTED_IDS]
