"""The page model: islands and the nine-region shell.

An :class:`Island` is a *declarative* mount descriptor. It names an adapter, the
props serialized into the mount point, and the event topics it publishes and
subscribes to. That single descriptor has three consumers: Python emits it, the
browser runtime mounts and wires from it, and a static analyzer can draw the
pub/sub dependency graph from the declared topics — without executing anything.

A :class:`Shell` places islands into the nine regions of the canonical
three-column frame (a top chrome rail, the three columns, a bottom chrome rail).
The region names match the ``grid-template-areas`` in ``static/shell.css``.
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
"""One of the nine named regions of the shell grid."""

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
