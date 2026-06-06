"""Layout presets: ready-made arrangements built from the Frame primitive.

A preset is an ordinary function that assembles islands into a :class:`Frame`
tree and returns a :class:`Document`. It holds no styling and no special
rendering path; it is sugar over the model, so anything a preset builds you could
build by hand. ``three_column`` is the nine-region arrangement the demo uses.

The preset is opinionated about *layout* (three columns, fixed side rails, a
flexible center) but never about visual *style*: the sizes below are plain CSS
lengths, not design tokens, and nothing here sets color, type, or theming.
"""

from collections.abc import Mapping, Sequence

from switchboard_ui.model import Document, Frame, Island, Region, Slot

# Layout sizes for the three-column arrangement: plain lengths, not design tokens.
_RAIL_HEIGHT = "2.5rem"
_LEFT_WIDTH = "220px"
_RIGHT_WIDTH = "200px"


def _cell(region: Region, placed: Mapping[Region, Sequence[Island]]) -> Frame:
    """A region cell: a column stack of its islands, hooked by an ``sb-<region>``
    class (a theming hook the packaged CSS leaves unpainted)."""
    return Frame(
        direction="column",
        children=tuple(placed.get(region, ())),
        class_=f"sb-{region}",
    )


def _row(
    left: Region,
    center: Region,
    right: Region,
    placed: Mapping[Region, Sequence[Island]],
) -> Frame:
    """One row: fixed-width side cells around a flexible center cell."""
    return Frame(
        direction="row",
        children=(
            Slot(_cell(left, placed), basis=_LEFT_WIDTH),
            Slot(_cell(center, placed)),
            Slot(_cell(right, placed), basis=_RIGHT_WIDTH),
        ),
    )


def three_column(
    regions: Mapping[Region, Sequence[Island]] | None = None,
    *,
    title: str = "switchboard-ui",
) -> Document:
    """Build the nine-region three-column arrangement as a :class:`Document`.

    A column of three rows (a fixed-height top and bottom around a flexible
    middle), each a row of three cells (fixed-width sides around a flexible
    center). Islands are placed by region name (``head-l`` through ``foot-r``);
    an omitted region renders as an empty cell that collapses. Each cell carries
    an ``sb-<region>`` class as a theming hook. The result is an ordinary
    ``Document`` you render with :func:`switchboard_ui.render_document`.
    """
    placed = regions or {}
    body = Frame(
        direction="column",
        children=(
            Slot(_row("head-l", "head-c", "head-r", placed), basis=_RAIL_HEIGHT),
            Slot(_row("body-l", "body-c", "body-r", placed)),
            Slot(_row("foot-l", "foot-c", "foot-r", placed), basis=_RAIL_HEIGHT),
        ),
    )
    return Document(body=body, title=title)
