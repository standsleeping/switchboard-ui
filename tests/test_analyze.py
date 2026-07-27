"""The analyzer recovers a page's declared wiring and its layout policy.

The island descriptor's third consumer: after Python emits the ``data-pub`` /
``data-sub`` attributes and the browser mounts from them, :mod:`switchboard_ui.analyze`
reads them back. These tests hold the analyzer to that promise: the graph it
recovers from a rendered page is exactly the wiring the descriptors declared,
without executing anything.
"""

from switchboard_ui import Island, wiring
from switchboard_ui.analyze import Edge, MountPoint, unreachable_content
from switchboard_ui.demo import build_demo
from switchboard_ui.model import Document, Frame, Slot
from switchboard_ui.presets import workbench
from switchboard_ui.render import render_document, render_frame, render_island


def test_wiring_reads_one_mount_point() -> None:
    """A rendered island comes back as its name and declared topic tuples."""
    html = render_island(
        Island(name="counter", publishes=("count:changed",), subscribes=("reset",))
    )
    assert wiring(html).islands == (
        MountPoint(name="counter", publishes=("count:changed",), subscribes=("reset",)),
    )


def test_wiring_splits_multiple_declared_topics() -> None:
    """A comma-joined data-pub / data-sub attribute yields every topic."""
    html = render_island(
        Island(name="hub", publishes=("a:x", "b:y"), subscribes=("c:z",))
    )
    (island,) = wiring(html).islands
    assert island.publishes == ("a:x", "b:y")
    assert island.subscribes == ("c:z",)


def test_wiring_reads_an_undeclared_island_as_empty() -> None:
    """An island with no declared topics is present with empty tuples."""
    html = render_island(Island(name="brand", initial="switchboard-ui"))
    assert wiring(html).islands == (MountPoint(name="brand"),)


def test_wiring_ignores_elements_without_a_mount_point() -> None:
    """Frames, text, and ordinary markup contribute nothing to the graph."""
    html = render_frame(Frame(direction="row")) + '<p>prose</p><div class="x"></div>'
    assert wiring(html).islands == ()


def test_wiring_recovers_the_demo_graph() -> None:
    """The demo page's wiring is recoverable from its HTML alone: counter -> readout."""
    graph = wiring(render_document(build_demo()))
    assert [i.name for i in graph.islands] == ["brand", "counter", "readout", "status"]
    assert graph.topics == ("count:changed",)
    assert graph.edges == (Edge("count:changed", "counter", "readout"),)
    assert graph.dangling_publishes == ()
    assert graph.dangling_subscribes == ()


def test_wiring_deduplicates_repeated_mount_points_per_topic() -> None:
    """The same adapter mounted twice is two islands but one publisher name."""
    island = Island(name="slider", publishes=("size:changed",))
    graph = wiring(render_island(island) + render_island(island))
    assert len(graph.islands) == 2
    assert graph.publishers("size:changed") == ("slider",)


def test_wiring_pairs_every_publisher_with_every_subscriber() -> None:
    """Edges are the per-topic publisher-subscriber pairs, in a stable order."""
    html = (
        render_island(Island(name="a", publishes=("t",)))
        + render_island(Island(name="b", publishes=("t",)))
        + render_island(Island(name="c", subscribes=("t",)))
        + render_island(Island(name="d", subscribes=("t",)))
    )
    assert wiring(html).edges == (
        Edge("t", "a", "c"),
        Edge("t", "a", "d"),
        Edge("t", "b", "c"),
        Edge("t", "b", "d"),
    )


def test_wiring_reports_dangling_topics() -> None:
    """A topic declared on one side only surfaces as dangling, sorted."""
    html = render_island(
        Island(name="a", publishes=("out:b", "out:a"))
    ) + render_island(Island(name="b", subscribes=("in:only",)))
    graph = wiring(html)
    assert graph.dangling_publishes == ("out:a", "out:b")
    assert graph.dangling_subscribes == ("in:only",)
    assert graph.edges == ()


def test_wiring_lists_subscribers_in_document_order() -> None:
    """Per-topic names keep document order (the order mount points render)."""
    html = render_island(Island(name="late", subscribes=("t",))) + render_island(
        Island(name="early", subscribes=("t",))
    )
    assert wiring(html).subscribers("t") == ("late", "early")


def test_a_viewport_page_whose_frames_never_scroll_is_unreachable() -> None:
    """A locked root with no auto-overflow descendant renders content nothing reaches.

    Each frame's policy is fine on its own; the defect is the combination, which
    is why it is checked over the tree rather than expressed in the dataclasses.
    """
    doc = Document(
        body=Frame(
            direction="column",
            overflow="clip",
            children=(Frame(direction="row", overflow="visible"),),
        ),
        root="viewport",
    )
    assert unreachable_content(doc)


def test_one_auto_frame_anywhere_in_the_tree_makes_content_reachable() -> None:
    """The scroll owner may sit at any depth, including behind a Slot."""
    scroller = Frame(direction="column", overflow="auto")
    doc = Document(
        body=Frame(
            direction="column",
            overflow="clip",
            children=(Slot(Frame(direction="row", children=(scroller,))),),
        ),
        root="viewport",
    )
    assert not unreachable_content(doc)


def test_a_flow_page_is_never_unreachable() -> None:
    """The page is the scroll owner in flow, so no descendant needs to be one."""
    doc = Document(body=Frame(direction="column", overflow="clip"), root="flow")
    assert not unreachable_content(doc)


def test_the_shipped_preset_leaves_no_content_unreachable() -> None:
    """The dogfood workbench preset passes its own diagnostic."""
    assert not unreachable_content(workbench({"body-c": (Island(name="app"),)}))
