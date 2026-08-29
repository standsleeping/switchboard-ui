"""Layout presets: ready-made arrangements built from the Frame primitive.

A preset is an ordinary function that assembles islands into a :class:`Frame`
tree and returns a :class:`Document`. It holds no styling and no special
rendering path; it is sugar over the model, so anything a preset builds you could
build by hand.

There are two, named for the page shapes they build rather than for the number of
columns they happen to have:

:func:`document_site` is a flowing document. The page is the primary scroll
owner, because that is what the browser's normal document does and what every
reader affordance operates on: find-in-page, fragment anchors, the browser's own
scroll restoration, overscroll. The side rails are sticky and capped, and they
are the only contained scrollers.

:func:`workbench` is a viewport-locked application shell. The page itself never
scrolls; the three body cells own their scroll independently, so a reader's place
in one region does not move because another region changed.

They are two assemblies rather than one constructor with a flag, because a flag
would keep two page semantics hidden inside one convenient name. They share the
nine region names so a page can be moved from one to the other without learning a
second placement vocabulary, and so the three row hooks that carry seam ownership
mean the same thing in both.

Both are opinionated about *layout* (three columns, fixed-width side rails, a
flexible center) but never about visual *style*: nothing here sets color, type,
or theming. The side widths are plain structural lengths (how wide the nav is, a
layout choice). The rail *height* is not a structural guess: the head and foot
rows carry ``sb-rail``, which floors them to the theme's ``--sb-fit-rail-block``
obligation and lets content drive above it (see ``static/layout.css``).
"""

from collections.abc import Mapping, Sequence
from dataclasses import replace

from switchboard_ui.model import Document, Frame, Island, Overflow, Region, Slot

# Side-rail widths: plain structural lengths (a layout choice, above the control
# obligation a sufficiency test verifies), not design tokens.
_LEFT_WIDTH = "220px"
_RIGHT_WIDTH = "200px"

Placement = Mapping[Region, Sequence[Island] | Frame]
"""What each region holds, by region name: the placement both presets accept.

A region holds a sequence of islands, stacked in a column the preset builds, or
a :class:`Frame` the host built, which becomes the cell itself: the preset adds
the region's hook class (and its structural role) and leaves the frame's own
overflow policy in force, so a rail can be a scrolling part over a pinned part,
with the boundary between them a frame edge rather than a line drawn inside a
scroll owner.
"""


def _cell(
    region: Region,
    placed: Placement,
    *,
    overflow: Overflow,
    role: str = "",
) -> Frame:
    """A region cell: a column stack of its islands, hooked by an ``sb-<region>``
    class (a theming hook the packaged CSS leaves unpainted).

    ``overflow`` is the cell's declared policy, decided by the preset that placed
    it. ``role`` adds a structural role class where the cell has one (a sticky
    rail in a flowing document); the region hook always comes first.

    A region given a :class:`Frame` instead of islands supplies the cell itself:
    it keeps its own overflow policy (the host declared it, knowing what is
    inside) and gains the hook and role classes, so the theme and the structural
    sheet address it exactly as they would the preset's own cell.
    """
    hook = f"sb-{region} {role}" if role else f"sb-{region}"
    content = placed.get(region, ())
    if isinstance(content, Frame):
        return replace(content, class_=f"{hook} {content.class_}".strip())
    return Frame(
        direction="column",
        children=tuple(content),
        overflow=overflow,
        class_=hook,
    )


def _chrome_row(
    left: Region,
    center: Region,
    right: Region,
    placed: Placement,
    *,
    class_: str,
    left_width: str,
    right_width: str,
) -> Frame:
    """A head or foot rail: fixed-width side cells around a flexible center.

    Identical in both presets, because chrome behaves the same in both shapes: it
    is content-driven with a floor, it clips rather than scrolling, and it owns
    its full-width seam. ``class_`` carries ``sb-rail`` plus the row's identity
    hook (``sb-head-row`` / ``sb-foot-row``) so a theme can give each horizontal
    seam one row owner.
    """
    return Frame(
        direction="row",
        children=(
            Slot(_cell(left, placed, overflow="clip"), basis=left_width),
            Slot(_cell(center, placed, overflow="clip")),
            Slot(_cell(right, placed, overflow="clip"), basis=right_width),
        ),
        overflow="clip",
        class_=class_,
    )


def document_site(
    regions: Placement | None = None,
    *,
    title: str = "switchboard-ui",
    left_width: str = _LEFT_WIDTH,
    right_width: str = _RIGHT_WIDTH,
) -> Document:
    """Build a flowing document site as a :class:`Document`.

    A column of three rows: content-driven head and foot rails around a body row
    that grows into whatever slack a short page leaves. Islands are placed by
    region name (``head-l`` through ``foot-r``); an omitted region renders as an
    empty cell that collapses.

    The center column declares ``overflow="visible"``, so a long article extends
    the page and the *page* scrolls it. That is the whole point of the shape: the
    reader's position lives in the document, where the browser can restore it,
    rather than in an element the next navigation replaces.

    The two side cells are sticky rails: they declare ``overflow="auto"`` and
    carry ``sb-sticky-rail``, so each stays in view as the article scrolls past
    and scrolls within itself only when it is taller than the screen.

    Returns ``Document(root="flow")``. Render it with
    :func:`switchboard_ui.render_document`.
    """
    placed = regions or {}
    # The body row takes the slack a short page leaves, so the foot rail sits at
    # the bottom rather than partway up; `sb-flow-body` gives it `flex: 1 1 auto`
    # rather than a Slot's `1 1 0`, because a zero basis would size the row from
    # the leftover viewport space and crush a long article into it.
    body_row = Frame(
        direction="row",
        children=(
            Slot(
                _cell("body-l", placed, overflow="auto", role="sb-sticky-rail"),
                basis=left_width,
            ),
            Slot(_cell("body-c", placed, overflow="visible")),
            Slot(
                _cell("body-r", placed, overflow="auto", role="sb-sticky-rail"),
                basis=right_width,
            ),
        ),
        overflow="visible",
        class_="sb-body-row sb-flow-body",
    )
    body = Frame(
        direction="column",
        children=(
            _chrome_row(
                "head-l",
                "head-c",
                "head-r",
                placed,
                class_="sb-rail sb-head-row",
                left_width=left_width,
                right_width=right_width,
            ),
            body_row,
            _chrome_row(
                "foot-l",
                "foot-c",
                "foot-r",
                placed,
                class_="sb-rail sb-foot-row",
                left_width=left_width,
                right_width=right_width,
            ),
        ),
        overflow="visible",
    )
    return Document(body=body, root="flow", title=title)


def workbench(
    regions: Placement | None = None,
    *,
    title: str = "switchboard-ui",
    left_width: str = _LEFT_WIDTH,
    right_width: str = _RIGHT_WIDTH,
) -> Document:
    """Build a viewport-locked application shell as a :class:`Document`.

    A column of three rows (content-driven head and foot rails, each floored to
    the theme's rail obligation, around a flexible middle), each a row of three
    cells (fixed-width sides around a flexible center). Islands are placed by
    region name (``head-l`` through ``foot-r``); an omitted region renders as an
    empty cell that collapses.

    The three body cells declare ``overflow="auto"``: each owns its scroll
    independently, while every frame above them clips, so nothing escapes the
    locked root. That independence is the shape's purpose — a tool's regions hold
    their own positions — and its accepted cost is that those positions are
    client-held state a forward navigation does not carry.

    ``left_width`` / ``right_width`` size the side columns: a layout choice (how
    wide the nav and the inspector are), defaulting to the standard rails. A tool
    whose inspector needs more room widens the right column without leaving the
    preset.

    Returns ``Document(root="viewport")``. Render it with
    :func:`switchboard_ui.render_document`.
    """
    placed = regions or {}
    body_row = Frame(
        direction="row",
        children=(
            Slot(_cell("body-l", placed, overflow="auto"), basis=left_width),
            Slot(_cell("body-c", placed, overflow="auto")),
            Slot(_cell("body-r", placed, overflow="auto"), basis=right_width),
        ),
        overflow="clip",
        class_="sb-body-row",
    )
    body = Frame(
        direction="column",
        children=(
            _chrome_row(
                "head-l",
                "head-c",
                "head-r",
                placed,
                class_="sb-rail sb-head-row",
                left_width=left_width,
                right_width=right_width,
            ),
            Slot(body_row),
            _chrome_row(
                "foot-l",
                "foot-c",
                "foot-r",
                placed,
                class_="sb-rail sb-foot-row",
                left_width=left_width,
                right_width=right_width,
            ),
        ),
        overflow="clip",
    )
    return Document(body=body, root="viewport", title=title)
