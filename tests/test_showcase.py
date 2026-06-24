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


def test_showcase_css_reveals_only_direct_empty_region_cells() -> None:
    """The demo grid uncollapses row cells through scoped paint-only CSS."""
    css = showcase_styles()
    for row in ("head", "body", "foot"):
        assert f".sb-{row}-row > .sb-frame:empty" in css
    assert "display: flex" in css
