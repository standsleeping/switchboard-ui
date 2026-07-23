"""The shared surface switch moves between the three dogfood pages."""

from showcase.chrome import surface_switch, surface_switch_styles
from switchboard_ui import render_island
from tests.htmlprobe import find


def test_switch_links_the_three_surfaces() -> None:
    """The switch offers Gallery, Docs, and Builder, each linking to its route."""
    html = surface_switch("gallery").initial
    hrefs = [a["href"] for a in find(html, "a", **{"class": "sb-switch-link"})]
    assert hrefs == ["/", "/docs", "/builder"]


def test_switch_marks_only_the_active_surface() -> None:
    """Exactly the active surface's link carries aria-current; the others do not."""
    html = surface_switch("docs").initial
    current = find(html, "a", **{"aria-current": "page"})
    assert [a["href"] for a in current] == ["/docs"]


def test_switch_is_a_static_island() -> None:
    """The switch ships no adapter and no pub/sub: its links navigate natively."""
    island = surface_switch("builder")
    assert island.name == "surface-switch"
    assert island.publishes == () and island.subscribes == ()
    # It renders without an adapter registered (a plain chrome island).
    assert "sb-switch" in render_island(island)


def test_switch_styles_reserve_the_active_underline_on_every_link() -> None:
    """Every link reserves the underline as a transparent border (no shift on switch)."""
    css = surface_switch_styles()
    assert ".sb-switch-link" in css
    assert "border-block-end" in css  # the reserved underline channel
    assert '.sb-switch-link[aria-current="page"]' in css  # recolored when active
