"""Tests for the renderer (structural assertions over parsed HTML)."""

import pytest

from switchboard_ui import model
from switchboard_ui.model import REGIONS, Document, Frame, Island, Slot
from switchboard_ui.presets import workbench
from switchboard_ui.render import (
    DOCUMENT_CLASS,
    render_document,
    render_frame,
    render_island,
)
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


def test_workbench_inline_embeds_assets_and_places_islands() -> None:
    """Inline mode embeds a <style> and a srcless <script>, and places islands."""
    doc = workbench({"body-c": (Island(name="app"),)}, title="Demo & Co")
    html = render_document(doc, runtime="inline")
    assert html.startswith("<!doctype html>")
    assert find(html, "title")
    assert find(html, "style")  # CSS embedded as an element
    assert any("src" not in s for s in find(html, "script"))  # runtime inline
    assert "sb-debug-overlay" in html  # debug overlay module inlined too
    assert find(html, "div", **{"data-island": "app"})


def test_workbench_places_an_island_in_every_region() -> None:
    """Every region accepts an island; all nine appear in the output."""
    regions = {region: (Island(name=region),) for region in REGIONS}
    html = render_document(workbench(regions), runtime="inline")
    for region in REGIONS:
        assert find(html, "div", **{"data-island": region})


def test_render_document_linked_references_assets() -> None:
    """Linked mode references the assets under asset_base; nothing embedded."""
    html = render_document(workbench(), runtime="linked", asset_base="/static/")
    [link] = find(html, "link", rel="stylesheet")
    assert link["href"] == "/static/layout.css"
    assert find(html, "script", src="/static/switchboard.js")
    assert find(html, "script", src="/static/switchboard-debug.js")
    assert not find(html, "style")


def test_render_document_includes_extra_head_and_scripts() -> None:
    """Extra head markup and island adapter scripts are injected."""
    html = render_document(
        workbench(),
        extra_head='<meta name="x">',
        extra_scripts=("/* adapter */",),
    )
    assert find(html, "meta", name="x")
    assert "/* adapter */" in html  # script payload is content, asserted directly


def test_render_appends_user_classes_to_frame_and_island() -> None:
    """A `class_` on a frame or island is appended after the package classes."""
    html = render_frame(
        Frame(
            direction="row", class_="grid", children=(Island(name="a", class_="card"),)
        )
    )
    assert find(
        html, "div", **{"class": "sb-frame sb-frame-row sb-overflow-visible grid"}
    )
    assert find(html, "div", **{"class": "sb-island card"})


def test_render_frame_renders_an_empty_flex_stack() -> None:
    """A childless frame is an empty flex stack carrying its direction class."""
    html = render_frame(Frame(direction="row"))
    assert html == '<div class="sb-frame sb-frame-row sb-overflow-visible"></div>'


def test_render_frame_nests_frames_and_islands() -> None:
    """Frames compose to depth; leaves are islands, branches are nested frames."""
    inner = Frame(direction="row", children=(Island(name="a"), Island(name="b")))
    html = render_frame(Frame(direction="column", children=(inner, Island(name="c"))))
    assert find(
        html, "div", **{"class": "sb-frame sb-frame-column sb-overflow-visible"}
    )
    assert find(html, "div", **{"class": "sb-frame sb-frame-row sb-overflow-visible"})
    for name in ("a", "b", "c"):
        assert find(html, "div", **{"data-island": name})


def test_render_document_wraps_a_frame_root_in_the_envelope() -> None:
    """A document renders its body frame as the viewport-locked page root."""
    doc = Document(
        body=Frame(direction="row", children=(Island(name="a"), Island(name="b"))),
        root="flow",
        title="Doc & Co",
    )
    html = render_document(doc)
    assert html.startswith("<!doctype html>")
    assert find(html, "title")  # escaped title present
    [root] = find(
        html,
        "div",
        **{"class": "sb-frame sb-frame-row sb-overflow-visible sb-root sb-root-flow"},
    )
    assert root
    assert find(html, "style")  # inline assets embedded by default
    for name in ("a", "b"):
        assert find(html, "div", **{"data-island": name})


def test_render_frame_sizes_children_with_slots() -> None:
    """A Slot pins a child's flex; a bare child is content-sized."""
    html = render_frame(
        Frame(
            direction="row",
            children=(
                Slot(Island(name="nav"), basis="16rem"),  # fixed rail
                Slot(Island(name="main")),  # flexible (basis None)
                Island(name="aside"),  # bare = content-sized
            ),
        )
    )
    [nav] = find(html, "div", **{"data-island": "nav"})
    [main] = find(html, "div", **{"data-island": "main"})
    [aside] = find(html, "div", **{"data-island": "aside"})
    assert nav["style"] == "flex: 0 0 16rem"
    assert main["style"] == "flex: 1 1 0"
    assert "style" not in aside


def test_render_frame_sizes_a_nested_frame_slot() -> None:
    """A Slot sizes a nested frame, not only an island."""
    inner = Frame(direction="column", children=(Island(name="x"),))
    html = render_frame(Frame(direction="row", children=(Slot(inner, basis="200px"),)))
    [stack] = find(
        html, "div", **{"class": "sb-frame sb-frame-column sb-overflow-visible"}
    )
    assert stack["style"] == "flex: 0 0 200px"


def test_every_overflow_policy_and_root_mode_renders_a_class() -> None:
    """The class mappings are total over the model's literals.

    A dict cannot be proved exhaustive by the type checker, so the guard is a
    test: if a policy or mode is added to the model without a class, this fails
    rather than the renderer raising at some caller's page.
    """
    for policy in model.OVERFLOWS:
        html = render_frame(Frame(direction="row", overflow=policy))
        assert f"sb-overflow-{policy}" in html
    for mode in model.ROOT_MODES:
        html = render_document(Document(body=Frame(direction="row"), root=mode))
        assert f"sb-root-{mode}" in html


def test_a_policy_outside_the_model_fails_loudly() -> None:
    """An untyped caller gets a KeyError, never a frame with no policy class.

    Silently rendering no overflow class would put the frame back on whatever the
    stylesheet's cascade happened to give it — the failure mode typing this was
    meant to end.
    """
    with pytest.raises(KeyError):
        render_frame(Frame(direction="row", overflow="scroll"))  # type: ignore[arg-type]


def test_every_frame_carries_exactly_one_overflow_class() -> None:
    """No rendered frame is missing a policy, and none carries two."""
    html = render_document(workbench({"body-c": (Island(name="app"),)}))
    for div in find(html, "div"):
        names = div["class"].split()
        if "sb-frame" not in names:
            continue
        policies = [n for n in names if n.startswith("sb-overflow-")]
        assert len(policies) == 1, f"frame has policies {policies}: {names}"


def test_the_envelope_body_carries_the_owned_document_class() -> None:
    """The renderer names the envelope it generates, so the reset has a target."""
    html = render_document(workbench())
    assert f'<body class="{DOCUMENT_CLASS}">' in html
