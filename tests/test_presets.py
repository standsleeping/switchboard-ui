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
    assert cell.class_ == "sb-body-c"  # region identity hook for theming


def test_three_column_rails_are_content_driven_not_fixed() -> None:
    """The head and foot rows are bare ``sb-rail`` frames, floored by the contract.

    They are deliberately *not* fixed-basis ``Slot``s: the layer floors them to
    ``--sb-fit-rail-block`` (the theme's obligation) and lets content drive above
    it. Only the middle row is a flexible ``Slot``.
    """
    doc = three_column()
    head, middle, foot = doc.body.children
    assert isinstance(middle, Slot)  # the flexible center row
    for rail in (head, foot):
        assert isinstance(rail, Frame)  # not a Slot: no fixed height guess
        assert rail.class_ == "sb-rail"  # the layer floors it to the contract
