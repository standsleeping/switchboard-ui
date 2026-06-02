"""Tests for the renderer (structural assertions over parsed HTML)."""

from switchboard_ui.model import REGIONS, Island, Shell
from switchboard_ui.render import render_island, render_shell
from tests.htmlprobe import find


def test_render_island_emits_full_descriptor() -> None:
    """An island with props and topics serializes every data-* attribute."""
    island = Island(
        name="counter",
        props={"start": 0},
        publishes=("count:changed",),
        subscribes=("reset:all",),
        initial="<i>seed</i>",
    )
    html = render_island(island)
    [div] = find(html, "div", **{"data-island": "counter"})
    assert div["class"] == "sb-island"
    assert div["data-props"] == '{"start":0}'  # parsed value, post-unescape
    assert div["data-pub"] == "count:changed"
    assert div["data-sub"] == "reset:all"
    assert find(html, "i")  # initial HTML is present as real structure


def test_render_island_omits_empty_attributes() -> None:
    """A bare island omits data-props/pub/sub entirely."""
    [div] = find(render_island(Island(name="brand")), "div", **{"data-island": "brand"})
    assert "data-props" not in div
    assert "data-pub" not in div
    assert "data-sub" not in div


def test_render_shell_inline_embeds_assets_and_places_islands() -> None:
    """Inline mode embeds a <style> and a srcless <script>, and places islands."""
    shell = Shell(title="Demo & Co", regions={"body-c": (Island(name="app"),)})
    html = render_shell(shell, runtime="inline")
    assert html.startswith("<!doctype html>")
    assert find(html, "title")
    assert find(html, "style")  # CSS embedded as an element
    assert any("src" not in s for s in find(html, "script"))  # runtime inline
    assert find(html, "div", **{"data-region": "body-c"})
    assert find(html, "div", **{"data-island": "app"})


def test_render_shell_renders_all_nine_regions() -> None:
    """Every region element is present even when empty (reserved geometry)."""
    html = render_shell(Shell(), runtime="inline")
    for region in REGIONS:
        assert find(html, "div", **{"data-region": region})


def test_render_shell_linked_references_assets() -> None:
    """Linked mode references the assets under asset_base; nothing embedded."""
    html = render_shell(Shell(), runtime="linked", asset_base="/static/")
    [link] = find(html, "link", rel="stylesheet")
    assert link["href"] == "/static/shell.css"
    assert find(html, "script", src="/static/switchboard.js")
    assert not find(html, "style")


def test_render_shell_includes_extra_head_and_scripts() -> None:
    """Extra head markup and island adapter scripts are injected."""
    html = render_shell(
        Shell(),
        extra_head='<meta name="x">',
        extra_scripts=("/* adapter */",),
    )
    assert find(html, "meta", name="x")
    assert "/* adapter */" in html  # script payload is content, asserted directly
