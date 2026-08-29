"""Tests for layout presets (structural assertions over the model)."""

from switchboard_ui.analyze import unreachable_content
from switchboard_ui.model import REGIONS, Document, Frame, Island, Slot
from switchboard_ui.presets import document_site, workbench
from switchboard_ui.render import render_document


def test_workbench_builds_a_document_with_a_three_row_column_root() -> None:
    """The preset returns a Document whose body is a column of three rows."""
    doc = workbench(title="My page")
    assert isinstance(doc, Document)
    assert doc.title == "My page"
    assert doc.body.direction == "column"
    assert len(doc.body.children) == 3  # head, body, foot rows


def test_workbench_places_an_island_in_the_named_cell() -> None:
    """An island placed in body-c lands in the center cell of the middle row."""
    island = Island(name="app")
    doc = workbench({"body-c": (island,)})

    middle = doc.body.children[1]
    assert isinstance(middle, Slot)
    row = middle.child
    assert isinstance(row, Frame)

    center = row.children[1]
    assert isinstance(center, Slot)
    cell = center.child
    assert isinstance(cell, Frame)

    assert cell.children == (island,)
    assert "sb-body-c" in cell.class_  # region identity hook for theming


def test_workbench_side_widths_default_to_the_standard_rails() -> None:
    """The side columns default to the standard nav / inspector rail widths."""
    middle = workbench().body.children[1]
    assert isinstance(middle, Slot)
    row = middle.child
    assert isinstance(row, Frame)
    left, _, right = row.children
    assert isinstance(left, Slot)
    assert isinstance(right, Slot)
    assert (left.basis, right.basis) == ("220px", "200px")


def test_workbench_side_widths_are_overridable() -> None:
    """A tool widens the side columns without leaving the preset (e.g. a roomy inspector)."""
    middle = workbench(left_width="16rem", right_width="20rem").body.children[1]
    assert isinstance(middle, Slot)
    row = middle.child
    assert isinstance(row, Frame)
    left, _, right = row.children
    assert isinstance(left, Slot)
    assert isinstance(right, Slot)
    assert (left.basis, right.basis) == ("16rem", "20rem")


def test_workbench_rails_are_content_driven_not_fixed() -> None:
    """The head and foot rows are ``sb-rail`` frames, floored by the contract.

    They are deliberately *not* fixed-basis ``Slot``s: the layer floors them to
    ``--sb-fit-rail-block`` (the theme's obligation) and lets content drive above
    it. Only the middle row is a flexible ``Slot``.
    """
    doc = workbench()
    head, middle, foot = doc.body.children
    assert isinstance(middle, Slot)  # the flexible center row
    for rail, role in ((head, "sb-head-row"), (foot, "sb-foot-row")):
        assert isinstance(rail, Frame)  # not a Slot: no fixed height guess
        assert rail.class_ == f"sb-rail {role}"


def test_workbench_rows_have_explicit_seam_ownership_hooks() -> None:
    """Every row has a stable identity hook for full-width seam ownership."""
    doc = workbench()
    head, middle, foot = doc.body.children
    assert isinstance(head, Frame)
    assert isinstance(middle, Slot)
    assert isinstance(middle.child, Frame)
    assert isinstance(foot, Frame)
    assert "sb-head-row" in head.class_
    assert middle.child.class_ == "sb-body-row"
    assert "sb-foot-row" in foot.class_


def _cells(row: Frame) -> list[Frame]:
    """The cell frames of a row, unwrapping any slot sizing."""
    out: list[Frame] = []
    for child in row.children:
        cell = child.child if isinstance(child, Slot) else child
        assert isinstance(cell, Frame)
        out.append(cell)
    return out


def test_workbench_body_cells_own_their_scroll() -> None:
    """The three body cells declare ``overflow="auto"``; every frame above clips.

    Scroll ownership is a value on the frame that owns it, so the whole
    containment chain is readable without consulting a stylesheet: the center and
    sidebars scroll their own overflow while the rows, rails, and root clip.
    """
    doc = workbench()
    head, middle, foot = doc.body.children
    assert doc.body.overflow == "clip"
    assert isinstance(middle, Slot)
    body_row = middle.child
    assert isinstance(body_row, Frame)
    assert body_row.overflow == "clip"
    for cell in _cells(body_row):
        assert cell.overflow == "auto"
    for rail in (head, foot):
        assert isinstance(rail, Frame)
        assert rail.overflow == "clip"
        for cell in _cells(rail):
            assert cell.overflow == "clip"


def test_workbench_is_a_viewport_page() -> None:
    """The preset names its own root mode: it is a workbench, not a document."""
    assert workbench().root == "viewport"


def test_document_site_is_a_flow_page() -> None:
    """The preset names its own root mode: it is a document, not a workbench."""
    assert document_site().root == "flow"


def test_document_site_lets_the_page_own_the_article_scroll() -> None:
    """The center column is visible, so a long article extends and scrolls the page.

    This is the whole point of the shape: the reader's position lives in the
    document, where the browser restores it, rather than in an element the next
    navigation replaces.
    """
    doc = document_site()
    body_row = doc.body.children[1]
    assert isinstance(body_row, Frame)
    assert doc.body.overflow == "visible"
    assert body_row.overflow == "visible"
    center = body_row.children[1]
    assert isinstance(center, Slot)
    assert isinstance(center.child, Frame)
    assert center.child.overflow == "visible"


def test_document_site_side_cells_are_capped_sticky_scrollers() -> None:
    """Both rails stick and own their own scroll; they are the only scrollers."""
    doc = document_site()
    body_row = doc.body.children[1]
    assert isinstance(body_row, Frame)
    left, _, right = body_row.children
    for side in (left, right):
        assert isinstance(side, Slot)
        cell = side.child
        assert isinstance(cell, Frame)
        assert cell.overflow == "auto"
        assert "sb-sticky-rail" in cell.class_


def test_document_sites_body_row_is_not_a_zero_basis_slot() -> None:
    """The body row grows by role class, never by a Slot's zero basis.

    A zero basis contributes nothing to an auto-height column's intrinsic size,
    so the row would be sized from leftover viewport space and a long article
    would be crushed into it. The role class gives `flex: 1 1 auto` instead.
    """
    doc = document_site()
    body_row = doc.body.children[1]
    assert isinstance(body_row, Frame), (
        "the flow body row must not be wrapped in a Slot"
    )
    assert "sb-flow-body" in body_row.class_


def test_both_presets_share_the_region_and_seam_vocabulary() -> None:
    """One placement vocabulary and one set of row hooks across both shapes.

    Keeping the nine region names and the three row hooks identical is what lets
    a page move between shapes without relearning placement, and what keeps a
    single seam owner meaningful in both.
    """
    for build in (document_site, workbench):
        doc = build({region: (Island(name=region),) for region in REGIONS})
        head, _, foot = doc.body.children
        assert isinstance(head, Frame)
        assert isinstance(foot, Frame)
        assert "sb-head-row" in head.class_
        assert "sb-foot-row" in foot.class_
        rendered = render_document(doc)
        for region in REGIONS:
            assert f"sb-{region}" in rendered


def test_neither_preset_leaves_content_unreachable() -> None:
    """Both shapes pass the whole-tree reachability diagnostic."""
    assert not unreachable_content(document_site({"body-c": (Island(name="a"),)}))
    assert not unreachable_content(workbench({"body-c": (Island(name="a"),)}))


def test_document_sites_center_column_is_stretched_not_content_sized() -> None:
    """The center cell must keep stretch alignment, so cell-owned seams stay full-height.

    A column seam drawn on the center cell's inline edges runs exactly as far as
    that cell is tall. Under a viewport-locked root the cell was the full-height
    flex cell of a locked row, so the line ran the row's whole height for free.
    That guarantee has to be re-established under flow, and here it comes from
    three facts acting together rather than from the root being locked:

      * the body row is a flex row whose default ``align-items: stretch`` sizes
        the center cell to the row's cross size, so the cell is never merely
        content-height;
      * the row carries ``sb-flow-body`` (``flex: 1 1 auto``), so it grows into
        the slack a short article leaves;
      * the root floors at ``100svb``, so that slack exists on a short page.

    Remove any one and a short article beside a long rail truncates both vertical
    rules partway down the page. This test pins the two structural facts the
    preset owns; the third is pinned in ``test_layout_css``.
    """
    doc = document_site()
    body_row = doc.body.children[1]
    assert isinstance(body_row, Frame)
    assert "sb-flow-body" in body_row.class_
    center = body_row.children[1]
    assert isinstance(center, Slot)
    cell = center.child
    assert isinstance(cell, Frame)
    # No role class may opt the center out of stretch; only the side rails do
    # that, and they draw no seam.
    assert "sb-sticky-rail" not in cell.class_
    assert cell.class_ == "sb-body-c"


def test_a_region_given_a_frame_supplies_the_cell_itself() -> None:
    """A host frame in a region becomes the cell: hooked, roled, and its own policy.

    The preset adds the region hook (and the sticky-rail role where the cell has
    one) and leaves the frame's overflow as the host declared it, so a rail can
    be a scrolling part over a pinned part with the boundary a frame edge.
    """
    scroller = Frame(
        direction="column", children=(Island(name="nav"),), overflow="auto"
    )
    pinned = Frame(direction="column", children=(Island(name="lens"),), overflow="clip")
    rail = Frame(
        direction="column",
        children=(Slot(scroller), pinned),
        overflow="clip",
        class_="host-rail",
    )
    doc = document_site({"body-l": rail, "body-c": (Island(name="article"),)})
    body_row = doc.body.children[1]
    assert isinstance(body_row, Frame)
    left = body_row.children[0]
    assert isinstance(left, Slot)
    cell = left.child
    assert isinstance(cell, Frame)
    assert cell.overflow == "clip"
    assert cell.class_ == "sb-body-l sb-sticky-rail host-rail"
    assert cell.children == (Slot(scroller), pinned)
    # The workbench hands the same frame its hook and no role.
    tool = workbench({"body-l": rail, "body-c": (Island(name="stage"),)})
    tool_row = tool.body.children[1]
    assert isinstance(tool_row, Slot) and isinstance(tool_row.child, Frame)
    tool_left = tool_row.child.children[0]
    assert isinstance(tool_left, Slot) and isinstance(tool_left.child, Frame)
    assert tool_left.child.class_ == "sb-body-l host-rail"
    assert tool_left.child.overflow == "clip"
