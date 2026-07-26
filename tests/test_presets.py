"""Tests for layout presets (structural assertions over the model)."""

from switchboard_ui.model import Document, Frame, Island, Slot
from switchboard_ui.presets import three_column


def test_three_column_builds_a_document_with_a_three_row_column_root() -> None:
    """The preset returns a Document whose body is a column of three rows."""
    doc = three_column(title="My page")
    assert isinstance(doc, Document)
    assert doc.title == "My page"
    assert doc.body.direction == "column"
    assert len(doc.body.children) == 3  # head, body, foot rows


def test_three_column_places_an_island_in_the_named_cell() -> None:
    """An island placed in body-c lands in the center cell of the middle row."""
    island = Island(name="app")
    doc = three_column({"body-c": (island,)})

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


def test_three_column_side_widths_default_to_the_standard_rails() -> None:
    """The side columns default to the standard nav / inspector rail widths."""
    middle = three_column().body.children[1]
    assert isinstance(middle, Slot)
    row = middle.child
    assert isinstance(row, Frame)
    left, _, right = row.children
    assert isinstance(left, Slot)
    assert isinstance(right, Slot)
    assert (left.basis, right.basis) == ("220px", "200px")


def test_three_column_side_widths_are_overridable() -> None:
    """A tool widens the side columns without leaving the preset (e.g. a roomy inspector)."""
    middle = three_column(left_width="16rem", right_width="20rem").body.children[1]
    assert isinstance(middle, Slot)
    row = middle.child
    assert isinstance(row, Frame)
    left, _, right = row.children
    assert isinstance(left, Slot)
    assert isinstance(right, Slot)
    assert (left.basis, right.basis) == ("16rem", "20rem")


def test_three_column_rails_are_content_driven_not_fixed() -> None:
    """The head and foot rows are ``sb-rail`` frames, floored by the contract.

    They are deliberately *not* fixed-basis ``Slot``s: the layer floors them to
    ``--sb-fit-rail-block`` (the theme's obligation) and lets content drive above
    it. Only the middle row is a flexible ``Slot``.
    """
    doc = three_column()
    head, middle, foot = doc.body.children
    assert isinstance(middle, Slot)  # the flexible center row
    for rail, role in ((head, "sb-head-row"), (foot, "sb-foot-row")):
        assert isinstance(rail, Frame)  # not a Slot: no fixed height guess
        assert rail.class_ == f"sb-rail {role}"


def test_three_column_rows_have_explicit_seam_ownership_hooks() -> None:
    """Every row has a stable identity hook for full-width seam ownership."""
    doc = three_column()
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


def test_three_column_body_cells_own_their_scroll() -> None:
    """The three body cells declare ``overflow="auto"``; every frame above clips.

    Scroll ownership is a value on the frame that owns it, so the whole
    containment chain is readable without consulting a stylesheet: the center and
    sidebars scroll their own overflow while the rows, rails, and root clip.
    """
    doc = three_column()
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


def test_three_column_is_a_viewport_page() -> None:
    """The preset names its own root mode: it is a workbench, not a document."""
    assert three_column().root == "viewport"
