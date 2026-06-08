"""The page model: islands and the recursive frame layout.

An :class:`Island` is a *declarative* mount descriptor. It names an adapter, the
props serialized into the mount point, and the event topics it publishes and
subscribes to. That single descriptor has three consumers: Python emits it, the
browser runtime mounts and wires from it, and a static analyzer can draw the
pub/sub dependency graph from the declared topics — without executing anything.

Layout is a recursive value. A :class:`Frame` is a one-dimensional flex stack of
islands or nested frames, the general layout primitive; a :class:`Slot` sizes a
child within it, and a :class:`Document` wraps a root frame as a full page.
Presets build ready-made layouts from these pieces: ``three_column`` (in
:mod:`switchboard_ui.presets`) arranges islands into a nine-region three-column
page, addressed by the names in :data:`REGIONS`.
"""

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal, get_args

type Json = str | int | float | bool | None | Mapping[str, Json] | Sequence[Json]
"""A JSON-serializable value (the shape props serialize to)."""

Region = Literal[
    "head-l",
    "head-c",
    "head-r",
    "body-l",
    "body-c",
    "body-r",
    "foot-l",
    "foot-c",
    "foot-r",
]
"""One of the nine named regions of the three-column preset."""

REGIONS: tuple[Region, ...] = get_args(Region)
"""All nine regions, in document (row-major) order."""


@dataclass(frozen=True)
class SpatialEscape:
    """A declared exception to an island's governed mount point (philosophy §17).

    An island is governed by default: a mount point whose content the surrounding
    frames size and the cell clips. When an island's content must do more than the
    governed contract allows, it declares the exception here, so the escape is
    explicit and inspectable (rendered as ``data-escape``) rather than a silent
    overflow. Every exception declares its authority.

    Attributes:
        overflow: How the island handles its own overflow. ``"clip"`` contains it,
            ``"scroll"`` makes the island its own scroll container, ``"visible"``
            lets content bleed past the island's box (the cell still clips at its
            own edge).
        paint_outset: How far paint (shadow, ring, badge) may escape the box, as a
            CSS length or token; ``""`` declares none. Documented for structure to
            honor; it reserves no space on its own.
    """

    overflow: Literal["clip", "scroll", "visible"] = "clip"
    paint_outset: str = ""


@dataclass(frozen=True)
class Island:
    """A declarative mount point for a self-contained interactive island.

    Attributes:
        name: The adapter key the browser registry mounts (``data-island``).
        props: JSON-serializable values handed to the adapter (``data-props``).
        publishes: Topics this island emits onto the bus (``data-pub``).
        subscribes: Topics this island listens for (``data-sub``).
        initial: Server-rendered inner HTML, present at first paint before any
            adapter mounts. Treated as trusted raw HTML.
        class_: Extra CSS class(es) for the mount-point ``<div>``, a theming
            hook the packaged CSS leaves unpainted. Appended after ``sb-island``.
        escape: A declared :class:`SpatialEscape` when the island's content must
            step outside the governed mount point (own its scroll, bleed paint).
            ``None`` (the default) keeps the island fully governed.
    """

    name: str
    props: Mapping[str, Json] = field(default_factory=dict)
    publishes: tuple[str, ...] = ()
    subscribes: tuple[str, ...] = ()
    initial: str = ""
    class_: str = ""
    escape: "SpatialEscape | None" = None

    def __post_init__(self) -> None:
        """Validate that props serialize to JSON at the authoring boundary.

        Moves the failure from deep inside rendering to the point the island is
        constructed, where the bad value was supplied.
        """
        try:
            json.dumps(dict(self.props), separators=(",", ":"))
        except TypeError as exc:
            msg = f"Island {self.name!r} has non-JSON-serializable props: {exc}"
            raise ValueError(msg) from exc


Direction = Literal["row", "column"]
"""The axis of a :class:`Frame`'s flex stack."""


@dataclass(frozen=True)
class Frame:
    """A recursive layout node: a one-dimensional flex stack of ordered children.

    ``direction`` is the stack axis. ``children`` lay out along it; each is an
    :class:`Island` leaf or a nested :class:`Frame`, so layouts compose to
    arbitrary depth. The event bus is global, so nesting is a layout concern
    only and never affects how islands coordinate.

    A frame is the general layout primitive; presets such as ``three_column``
    (in :mod:`switchboard_ui.presets`) arrange frames into ready-made layouts.

    ``class_`` adds CSS class(es) to the frame ``<div>``, a theming hook the
    packaged CSS leaves unpainted. It is appended after the ``sb-frame`` classes.
    """

    direction: Direction
    children: tuple["Island | Frame | Slot", ...] = ()
    class_: str = ""


@dataclass(frozen=True)
class Slot:
    """A sized position in a frame: a child plus its main-axis size.

    ``basis`` is a fixed CSS length or token, rendered as ``flex: 0 0 <basis>``.
    ``None`` makes the child flexible, growing to share the remaining space
    (``flex: 1 1 0``). A child placed in a frame *without* a slot is content-
    sized (the browser default).
    """

    child: "Island | Frame"
    basis: str | None = None


@dataclass(frozen=True)
class Document:
    """A full page: a root layout :class:`Frame` and a document title.

    The document is the envelope (it renders to a complete ``<!doctype html>``);
    the body is the root layout. Separating envelope from layout means a layout
    renders standalone or nested, and the envelope appears once, at the root.

    A document is the general page; presets such as ``three_column`` (in
    :mod:`switchboard_ui.presets`) build one for a ready-made layout.
    """

    body: Frame
    title: str = "switchboard-ui"
