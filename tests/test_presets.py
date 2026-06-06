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
