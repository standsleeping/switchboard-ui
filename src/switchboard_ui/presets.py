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

from switchboard_ui.model import Document, Frame, Island, Region, Slot

# Side-rail widths: plain structural lengths (a layout choice, above the control
# obligation a sufficiency test verifies), not design tokens.
_LEFT_WIDTH = "220px"
_RIGHT_WIDTH = "200px"


def _cell(
    region: Region,
    placed: Mapping[Region, Sequence[Island]],
    *,
    scroll: bool = False,
) -> Frame:
    """A region cell: a column stack of its islands, hooked by an ``sb-<region>``
    class (a theming hook the packaged CSS leaves unpainted).

    ``scroll`` marks the cell as a scroll owner (``sb-scroll``): it scrolls its
    own overflow while every frame above it clips (see ``static/layout.css``).
    """
    cls = f"sb-{region} sb-scroll" if scroll else f"sb-{region}"
    return Frame(
        direction="column",
        children=tuple(placed.get(region, ())),
        class_=cls,
    )


def _row(
    left: Region,
    center: Region,
    right: Region,
    placed: Mapping[Region, Sequence[Island]],
    *,
    class_: str = "",
    scroll: bool = False,
) -> Frame:
    """One row: fixed-width side cells around a flexible center cell.

    ``class_`` marks the row's structural and semantic roles. The head and foot
    rows pass ``sb-rail`` so the layer floors them to the contract; all three
    rows carry an identity hook (``sb-head-row`` / ``sb-body-row`` /
    ``sb-foot-row``) so a theme can give each full-width seam one row owner.
    ``scroll`` makes the row's cells scroll owners; the body row passes it so the
    center and sidebars scroll while the chrome rails clip.
    """
    return Frame(
        direction="row",
        children=(
            Slot(_cell(left, placed, scroll=scroll), basis=_LEFT_WIDTH),
            Slot(_cell(center, placed, scroll=scroll)),
            Slot(_cell(right, placed, scroll=scroll), basis=_RIGHT_WIDTH),
        ),
        class_=class_,
    )


def three_column(
    regions: Mapping[Region, Sequence[Island]] | None = None,
    *,
    title: str = "switchboard-ui",
) -> Document:
    """Build the nine-region three-column arrangement as a :class:`Document`.

    A column of three rows (a content-driven top and bottom, each floored to the
    theme's rail obligation, around a flexible middle), each a row of three cells
    (fixed-width sides around a flexible center). Islands are placed by region
    name (``head-l`` through ``foot-r``); an omitted region renders as an empty
    cell that collapses. Each cell carries an ``sb-<region>`` class as a theming
    hook; each row carries an ``sb-<row>-row`` hook for full-width seam ownership.
    The three body cells are scroll owners (``sb-scroll``): they scroll their own
    overflow while the root and chrome rails clip. The result is an ordinary
    ``Document`` you render with :func:`switchboard_ui.render_document`.
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
            ),
            Slot(
                _row(
                    "body-l",
                    "body-c",
                    "body-r",
                    placed,
                    class_="sb-body-row",
                    scroll=True,
                )
            ),
            _row(
                "foot-l",
                "foot-c",
                "foot-r",
                placed,
                class_="sb-rail sb-foot-row",
            ),
        ),
    )
    return Document(body=body, title=title)
