"""The dogfood showcase visualizes layout without changing application topology."""

from http import HTTPStatus

import pytest

from showcase.build import (
    DisplayProp,
    _gallery_specs,
    build_showcase,
    render_specimen,
    showcase_styles,
)
from showcase.server import render_island_response
from switchboard_ui import render_document, wiring
from switchboard_ui.model import Frame, Slot
from tests.htmlprobe import find


def test_showcase_keeps_unplaced_corner_regions_empty() -> None:
    """Grid paint must not invent placeholder islands to keep empty cells visible.

    ``head-r`` holds the mode switch, so the empty corners are ``head-l`` and
    both foot sides.
    """
    document = build_showcase()
    head, _, foot = document.body.children
    assert isinstance(head, Frame)
    assert isinstance(foot, Frame)
    empty = ((head, (0,)), (foot, (0, 2)))
    for row, positions in empty:
        for position in positions:
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
    assert ".sb-body-c" in css  # the center column owns both column seams
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
    "breadcrumb",
    "collapsible",
    "nav",
    "toc",
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


def test_inspector_editable_props_render_live_controls() -> None:
    """Each control specimen exposes its value prop as a live inspector control
    publishing on `<id>:prop:value` (a full mount point, so its adapter mounts)."""
    html = render_document(build_showcase())
    expected = {
        "slider": "slider:prop:value",
        "segmented": "segmented:prop:value",
        "color-input": "color-picker:prop:value",
        "value-field": "value-field:prop:value",
    }
    for island, topic in expected.items():
        controls = find(html, "div", **{"data-island": island})
        assert any(c.get("data-pub") == topic for c in controls), (island, topic)


def test_inspector_renders_one_row_per_prop_with_display_props_as_text() -> None:
    """Every prop yields one inspector row; a DisplayProp renders as read-only text."""
    specs = _gallery_specs()
    html = render_document(build_showcase())
    rows = find(html, "div", **{"class": "sb-gallery-inspector-prop"})
    assert len(rows) == sum(len(spec.props) for spec in specs)
    values = find(html, "div", **{"class": "sb-gallery-inspector-prop-value"})
    displays = sum(
        1 for spec in specs for prop in spec.props if isinstance(prop, DisplayProp)
    )
    assert len(values) == displays


def test_inspector_prop_edits_drive_the_specimens() -> None:
    """Every `:prop:` topic has both a publisher (the inspector control) and a
    subscriber (the specimen), so an inspector edit updates the live component.
    The analyzer recovers the whole wiring from the rendered HTML alone."""
    html = render_document(build_showcase())
    graph = wiring(html)
    prop_topics = [t for t in graph.topics if ":prop:" in t]
    assert prop_topics == [
        "breadcrumb:prop:current",
        "collapsible:prop:count",
        "collapsible:prop:title",
        "color-picker:prop:value",
        "modal:prop:title",
        "segmented:prop:value",
        "slider:prop:value",
        "value-field:prop:value",
    ]
    for topic in prop_topics:
        assert graph.publishers(topic), topic
        assert graph.subscribers(topic), topic


def test_inspector_controls_follow_the_specimens() -> None:
    """Each wired specimen's own publish topic has a subscriber (the inspector
    control follows it), so interacting with the specimen moves the control."""
    graph = wiring(render_document(build_showcase()))
    for topic in ("view:changed", "weight:changed", "token:accent", "token:radius"):
        assert graph.subscribers(topic), topic


def test_structural_edits_subscribe_the_remount_island() -> None:
    """Every structural prop topic's subscriber is the remount island, and its
    tracked state starts from the specs' own initial values."""
    html = render_document(build_showcase())
    graph = wiring(html)
    for topic in (
        "modal:prop:title",
        "collapsible:prop:title",
        "collapsible:prop:count",
        "breadcrumb:prop:current",
    ):
        assert graph.subscribers(topic) == ("gallery-remount",), topic
    (remount,) = find(html, "div", **{"data-island": "gallery-remount"})
    assert '"modal":{"title":"Dialog"}' in remount["data-props"]


def test_render_specimen_reruns_the_factory_with_edits() -> None:
    """A structural edit re-renders through the factory: the default render
    matches the gallery's own body, and an edited title lands in the markup."""
    (title,) = find(render_specimen("modal", {}), "div", role="heading")
    assert title["class"] == "sb-modal-title"
    edited = render_specimen("modal", {"title": "Renamed"})
    assert ">Renamed</div>" in edited
    assert 'sb-specimen-modal"' in edited


def test_render_specimen_rejects_unknown_and_non_structural_specimens() -> None:
    """An unknown id and a spec without structural props both fail loudly."""
    with pytest.raises(KeyError):
        render_specimen("no-such", {})
    with pytest.raises(KeyError):
        render_specimen("slider", {})


def test_render_specimen_surfaces_factory_validation() -> None:
    """A bad edit value fails in the factory (never silently in the browser)."""
    with pytest.raises(ValueError):
        render_specimen("collapsible", {"count": "not-a-number"})


def test_render_endpoint_maps_failure_modes_onto_statuses() -> None:
    """The endpoint's envelope: OK returns the fragment; malformed 400; unknown
    404; a factory-rejected edit 422."""
    ok, html = render_island_response(b'{"id": "modal", "props": {"title": "Renamed"}}')
    assert ok == HTTPStatus.OK
    assert "Renamed" in html
    assert render_island_response(b"not json")[0] == HTTPStatus.BAD_REQUEST
    assert render_island_response(b'{"id": "modal"}')[0] == HTTPStatus.BAD_REQUEST
    assert (
        render_island_response(b'{"id": "modal", "props": {"title": 3}}')[0]
        == HTTPStatus.BAD_REQUEST
    )
    assert (
        render_island_response(b'{"id": "no-such", "props": {}}')[0]
        == HTTPStatus.NOT_FOUND
    )
    assert (
        render_island_response(b'{"id": "collapsible", "props": {"count": "x"}}')[0]
        == HTTPStatus.UNPROCESSABLE_ENTITY
    )
