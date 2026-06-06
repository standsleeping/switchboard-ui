"""Tests for the demo page builder."""

from switchboard_ui.demo import build_demo, demo_scripts
from switchboard_ui.render import render_shell
from tests.htmlprobe import find


def test_build_demo_wires_counter_to_readout() -> None:
    """The demo declares the counter -> count:changed -> readout graph."""
    shell = build_demo()
    counter = shell.regions["body-c"][0]
    readout = shell.regions["body-r"][0]
    assert counter.name == "counter"
    assert counter.publishes == ("count:changed",)
    assert readout.name == "readout"
    assert readout.subscribes == ("count:changed",)


def test_demo_scripts_register_both_adapters() -> None:
    """Both island adapters register against the runtime."""
    joined = "".join(demo_scripts())
    assert joined.count("window.switchboard.register") == 2


def test_demo_renders_both_islands() -> None:
    """The rendered demo carries both interactive island mount points."""
    html = render_shell(build_demo(), extra_scripts=demo_scripts())
    assert find(html, "div", **{"data-island": "counter"})
    assert find(html, "div", **{"data-island": "readout"})
