"""The page model: islands and the recursive frame layout.

An :class:`Island` is a *declarative* mount descriptor. It names an adapter, the
props serialized into the mount point, and the event topics it publishes and
subscribes to. That single descriptor has three consumers: Python emits it, the
browser runtime mounts and wires from it, and a static analyzer can draw the
pub/sub dependency graph from the declared topics — without executing anything.

Layout is a recursive value. A :class:`Frame` is a one-dimensional flex stack of
islands or nested frames, the general layout primitive; a :class:`Slot` sizes a
child within it, and a :class:`Document` wraps a root frame as a full page.
Presets build ready-made layouts from these pieces, addressed by the names in
:data:`REGIONS`.

Two policies that the browser decides are stated here as values rather than left
implicit. Every :class:`Frame` names its :data:`Overflow`, so scroll ownership is
a property of the frame that owns it instead of a class string assembled
elsewhere; and every :class:`Document` names its :data:`RootMode`, so a page
declares whether it is a flowing document or a viewport-locked workbench.
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
"""One of the nine named regions both layout presets accept."""

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
        class_: Extra CSS class(es) for the mount-point ``<div>``, a theming
            hook the packaged CSS leaves unpainted. Appended after ``sb-island``.
    """

    name: str
    props: Mapping[str, Json] = field(default_factory=dict)
    publishes: tuple[str, ...] = ()
    subscribes: tuple[str, ...] = ()
    initial: str = ""
    class_: str = ""

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

Overflow = Literal["visible", "clip", "auto"]
"""A frame's declared overflow policy.

``visible`` is the browser's own default: content that exceeds the frame is
painted outside it and the page's own scrolling reaches it. ``clip`` cuts
overflow off and creates *no* scroll container, so nothing (including the user
agent's own scroll-a-focused-descendant-into-view behaviour) can scroll it.
``auto`` makes the frame a scroll owner: it scrolls its own overflow.

The three are exhaustive and named, so a frame's policy is readable in the
Python value, in the rendered class, and in the stylesheet under one name.
"""

OVERFLOWS: tuple[Overflow, ...] = get_args(Overflow)
"""Every overflow policy, so a guard can prove a mapping covers all of them."""

RootMode = Literal["flow", "viewport"]
"""How a :class:`Document`'s root relates to the viewport.

``flow`` is the browser's normal document: the root is content-sized and the
*page* is the primary scroll owner, which is what every reader affordance
operates on (find-in-page, fragment anchors, the browser's own scroll
restoration, overscroll). ``viewport`` locks the root to the viewport, so the
page itself never scrolls and every scroll belongs to a frame that declared
``overflow="auto"``.

The mode is never inferred from content, region names, viewport size, or the
presence of a nav. It is a required field precisely so that every page states
which shape it is.
"""

ROOT_MODES: tuple[RootMode, ...] = get_args(RootMode)
"""Every root mode, so a guard can prove a mapping covers all of them."""


@dataclass(frozen=True)
class Frame:
    """A recursive layout node: a one-dimensional flex stack of ordered children.

    ``direction`` is the stack axis. ``children`` lay out along it; each is an
    :class:`Island` leaf or a nested :class:`Frame`, so layouts compose to
    arbitrary depth. The event bus is global, so nesting is a layout concern
    only and never affects how islands coordinate.

    ``overflow`` is the frame's declared policy for content that exceeds it, one
    of :data:`Overflow`. It defaults to ``"visible"``, the browser's own default,
    so a frame that says nothing behaves the way the platform behaves. A frame
    becomes a scroll owner only by saying ``overflow="auto"``: scroll ownership
    is never inherited from an ancestor, assembled from a class string, or won
    by cascade order.

    A frame is the general layout primitive; presets such as ``document_site``
    and ``workbench`` (in :mod:`switchboard_ui.presets`) arrange frames into
    ready-made layouts.

    ``class_`` adds CSS class(es) to the frame ``<div>``, a theming hook the
    packaged CSS leaves unpainted. It is appended after the ``sb-frame`` classes.
    """

    direction: Direction
    children: tuple["Island | Frame | Slot", ...] = ()
    overflow: Overflow = "visible"
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
    """A full page: a root layout :class:`Frame`, a root mode, and a title.

    The document is the envelope (it renders to a complete ``<!doctype html>``);
    the body is the root layout. Separating envelope from layout means a layout
    renders standalone or nested, and the envelope appears once, at the root.

    ``root`` is required, not defaulted. The two modes in :data:`RootMode` are
    different page shapes rather than a setting with an obvious default, and a
    default would privilege one shape while every call site quietly inherits it.
    Naming it at each call site is what keeps the shape reviewable in a diff.

    A document is the general page; presets such as ``document_site`` and
    ``workbench`` (in :mod:`switchboard_ui.presets`) build one for a ready-made
    layout, and each preset names its own root mode.
    """

    body: Frame
    root: RootMode
    title: str = "switchboard-ui"
