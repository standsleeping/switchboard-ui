"""The page model: islands, the recursive frame layout, and presets.

An :class:`Island` is a *declarative* mount descriptor. It names an adapter, the
props serialized into the mount point, and the event topics it publishes and
subscribes to. That single descriptor has three consumers: Python emits it, the
browser runtime mounts and wires from it, and a static analyzer can draw the
pub/sub dependency graph from the declared topics — without executing anything.

Layout is a recursive value. A :class:`Frame` is a one-dimensional flex stack of
islands or nested frames, the general layout primitive; a :class:`Slot` sizes a
child within it. The nine-region :class:`Shell` is an example preset of that primitive,
placing islands into a top chrome rail, the three columns, and a bottom chrome
rail. The region names match the placement classes in ``static/shell.css``.
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
"""One of the nine named regions of the shell preset."""

REGIONS: tuple[Region, ...] = get_args(Region)
"""All nine regions, in document (row-major) order."""


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
    """

    name: str
    props: Mapping[str, Json] = field(default_factory=dict)
    publishes: tuple[str, ...] = ()
    subscribes: tuple[str, ...] = ()
    initial: str = ""

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


@dataclass(frozen=True)
class Shell:
    """A three-column page: a title plus islands placed by region.

    Attributes:
        title: The document ``<title>``.
        regions: A mapping of region name to the islands it hosts, in order.
    """

    title: str = "switchboard-ui"
    regions: Mapping[Region, Sequence[Island]] = field(default_factory=dict)


Direction = Literal["row", "column"]
"""The axis of a :class:`Frame`'s flex stack."""


@dataclass(frozen=True)
class Frame:
    """A recursive layout node: a one-dimensional flex stack of ordered children.

    ``direction`` is the stack axis. ``children`` lay out along it; each is an
    :class:`Island` leaf or a nested :class:`Frame`, so layouts compose to
    arbitrary depth. The event bus is global, so nesting is a layout concern
    only and never affects how islands coordinate.

    The nine-region :class:`Shell` is an example preset arranged from frames; a frame
    is the general layout primitive beneath it.
    """

    direction: Direction
    children: tuple["Island | Frame | Slot", ...] = ()


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

    The nine-region :class:`Shell` is a sibling preset for the standard
    application frame; a document is the general page beneath it.
    """

    body: Frame
    title: str = "switchboard-ui"
