"""Layout presets: ready-made arrangements built from the Frame primitive.

A preset is an ordinary function that assembles islands into a :class:`Frame`
tree and returns a :class:`Document`. It holds no styling and no special
rendering path; it is sugar over the model, so anything a preset builds you could
build by hand. ``three_column`` is the nine-region arrangement the demo uses.

The preset is opinionated about *layout* (three columns, fixed-width side rails,
a flexible center) but never about visual *style*: nothing here sets color, type,
or theming. The side widths are plain structural lengths (how wide the nav is, a
layout choice). The rail *height* is not a structural guess: the head and foot
rows carry ``sb-rail``, which floors them to the theme's ``--sb-fit-rail-block``
obligation and lets content drive above it (see ``static/layout.css``).
"""

from collections.abc import Mapping, Sequence

from switchboard_ui.model import Document, Frame, Island, Overflow, Region, Slot

# Side-rail widths: plain structural lengths (a layout choice, above the control
# obligation a sufficiency test verifies), not design tokens.
_LEFT_WIDTH = "220px"
_RIGHT_WIDTH = "200px"


def _cell(
    region: Region,
    placed: Mapping[Region, Sequence[Island]],
    *,
    overflow: Overflow,
) -> Frame:
    """A region cell: a column stack of its islands, hooked by an ``sb-<region>``
    class (a theming hook the packaged CSS leaves unpainted).

    ``overflow`` is the cell's declared policy, passed down from the preset that
    decided it rather than assembled into a class string here.
    """
    return Frame(
        direction="column",
        children=tuple(placed.get(region, ())),
        overflow=overflow,
        class_=f"sb-{region}",
    )


def _row(
    left: Region,
    center: Region,
    right: Region,
    placed: Mapping[Region, Sequence[Island]],
    *,
    class_: str = "",
    cell_overflow: Overflow,
    left_width: str = _LEFT_WIDTH,
    right_width: str = _RIGHT_WIDTH,
) -> Frame:
    """One row: fixed-width side cells around a flexible center cell.

    ``class_`` marks the row's structural and semantic roles. The head and foot
    rows pass ``sb-rail`` so the layer floors them to the contract; all three
    rows carry an identity hook (``sb-head-row`` / ``sb-body-row`` /
    ``sb-foot-row``) so a theme can give each full-width seam one row owner.
    ``cell_overflow`` is the policy each of the three cells declares; the body
    row makes its cells scroll owners while the chrome rails clip.
    ``left_width`` / ``right_width`` are the side cells' fixed bases (one layout
    choice for the whole arrangement, so the columns line up across all rows).
    """
    return Frame(
        direction="row",
        children=(
            Slot(_cell(left, placed, overflow=cell_overflow), basis=left_width),
            Slot(_cell(center, placed, overflow=cell_overflow)),
            Slot(_cell(right, placed, overflow=cell_overflow), basis=right_width),
        ),
        overflow="clip",
        class_=class_,
    )


def three_column(
    regions: Mapping[Region, Sequence[Island]] | None = None,
    *,
    title: str = "switchboard-ui",
    left_width: str = _LEFT_WIDTH,
    right_width: str = _RIGHT_WIDTH,
) -> Document:
    """Build the nine-region three-column arrangement as a :class:`Document`.

    A column of three rows (a content-driven top and bottom, each floored to the
    theme's rail obligation, around a flexible middle), each a row of three cells
    (fixed-width sides around a flexible center). Islands are placed by region
    name (``head-l`` through ``foot-r``); an omitted region renders as an empty
    cell that collapses. Each cell carries an ``sb-<region>`` class as a theming
    hook; each row carries an ``sb-<row>-row`` hook for full-width seam ownership.
    The three body cells declare ``overflow="auto"``: they scroll their own
    overflow while the root and chrome rails clip. It is a viewport-locked page,
    so it returns ``Document(root="viewport")``. The result is an ordinary
    ``Document`` you render with :func:`switchboard_ui.render_document`.

    ``left_width`` / ``right_width`` size the side columns: a layout choice (how
    wide the nav and the inspector are), defaulting to the standard rails. A tool
    whose inspector needs more room widens the right column without leaving the
    preset.
    """
    placed = regions or {}
    body = Frame(
        direction="column",
        children=(
            _row(
                "head-l",
                "head-c",
                "head-r",
                placed,
                class_="sb-rail sb-head-row",
                cell_overflow="clip",
                left_width=left_width,
                right_width=right_width,
            ),
            Slot(
                _row(
                    "body-l",
                    "body-c",
                    "body-r",
                    placed,
                    class_="sb-body-row",
                    cell_overflow="auto",
                    left_width=left_width,
                    right_width=right_width,
                )
            ),
            _row(
                "foot-l",
                "foot-c",
                "foot-r",
                placed,
                class_="sb-rail sb-foot-row",
                cell_overflow="clip",
                left_width=left_width,
                right_width=right_width,
            ),
        ),
        overflow="clip",
    )
    return Document(body=body, root="viewport", title=title)
