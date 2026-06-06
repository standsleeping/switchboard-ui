"""Tests for the demo page builder."""

from switchboard_ui.demo import build_demo, demo_scripts
from switchboard_ui.render import render_document
from tests.htmlprobe import find


def test_build_demo_wires_counter_to_readout() -> None:
    """The demo declares the counter -> count:changed -> readout graph."""
    html = render_document(build_demo())
    [counter] = find(html, "div", **{"data-island": "counter"})
    [readout] = find(html, "div", **{"data-island": "readout"})
    assert counter["data-pub"] == "count:changed"
    assert readout["data-sub"] == "count:changed"


def test_demo_scripts_register_both_adapters() -> None:
    """Both island adapters register against the runtime."""
    joined = "".join(demo_scripts())
    assert joined.count("window.switchboard.register") == 2


def test_demo_renders_both_islands() -> None:
    """The rendered demo carries both interactive island mount points."""
    html = render_document(build_demo(), extra_scripts=demo_scripts())
    assert find(html, "div", **{"data-island": "counter"})
    assert find(html, "div", **{"data-island": "readout"})
