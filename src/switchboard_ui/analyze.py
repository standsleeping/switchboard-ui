"""Static analysis of a rendered page's island wiring.

An :class:`~switchboard_ui.model.Island` declares its pub/sub topics as data, and
the renderer emits them as ``data-pub`` / ``data-sub`` attributes on each mount
point. This module is the descriptor's third consumer (after the Python renderer
that emits it and the browser runtime that mounts from it): it reads rendered
HTML and recovers the wiring — which islands exist, which topics connect them,
and which declared topics dangle — without executing anything. The dependency
graph is a property of the page, not of a running session.

The reader is deliberately dumb: it parses attributes, never JavaScript. What it
recovers is the *declared* wiring, which the descriptors carry precisely so that
this recovery is possible. Keeping an adapter's actual publishes and subscribes
in agreement with its island's declaration is the authoring contract the
declarations record.

Everything here is stdlib-only, like the rest of the package.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from html.parser import HTMLParser


@dataclass(frozen=True)
class MountPoint:
    """One rendered island mount point: its adapter name and declared topics.

    The analyzed form of an island. Two mount points may share a ``name`` (the
    same adapter mounted twice); each rendered occurrence is one value here.
    """

    name: str
    publishes: tuple[str, ...] = ()
    subscribes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Edge:
    """One directed wiring edge: ``publisher`` announces ``topic``; ``subscriber`` reacts."""

    topic: str
    publisher: str
    subscriber: str


@dataclass(frozen=True)
class Wiring:
    """The declared wiring of one rendered page or fragment.

    ``islands`` holds every mount point in document order. Everything else is
    derived from it: the topic vocabulary, the per-topic publisher and subscriber
    sets, the edge list, and the dangling topics (declared on one side only).
    """

    islands: tuple[MountPoint, ...]

    @property
    def topics(self) -> tuple[str, ...]:
        """Every declared topic, sorted."""
        return tuple(
            sorted({t for i in self.islands for t in i.publishes + i.subscribes})
        )

    def publishers(self, topic: str) -> tuple[str, ...]:
        """The island names declaring they publish ``topic``, in document order, deduplicated."""
        return _unique(i.name for i in self.islands if topic in i.publishes)

    def subscribers(self, topic: str) -> tuple[str, ...]:
        """The island names declaring they subscribe to ``topic``, in document order, deduplicated."""
        return _unique(i.name for i in self.islands if topic in i.subscribes)

    @property
    def edges(self) -> tuple[Edge, ...]:
        """Every publisher-to-subscriber edge, one per (topic, publisher, subscriber).

        Ordered by topic, then by the publishers' and subscribers' document
        order, so the graph is stable across runs of the same page.
        """
        return tuple(
            Edge(topic, publisher, subscriber)
            for topic in self.topics
            for publisher in self.publishers(topic)
            for subscriber in self.subscribers(topic)
        )

    @property
    def dangling_publishes(self) -> tuple[str, ...]:
        """Topics some island publishes but none subscribes to, sorted.

        A dangling publish is not necessarily a bug (a control can broadcast for
        a host page to pick up later), but it is always worth seeing.
        """
        return tuple(
            t for t in self.topics if self.publishers(t) and not self.subscribers(t)
        )

    @property
    def dangling_subscribes(self) -> tuple[str, ...]:
        """Topics some island subscribes to but none publishes, sorted."""
        return tuple(
            t for t in self.topics if self.subscribers(t) and not self.publishers(t)
        )


def wiring(html: str) -> Wiring:
    """Recover the declared island wiring from rendered HTML.

    ``html`` is anything the renderer produced: a full document, a frame, or a
    single island's mount point. Elements without ``data-island`` are ignored.
    """
    reader = _MountPointReader()
    reader.feed(html)
    return Wiring(islands=tuple(reader.mount_points))


class _MountPointReader(HTMLParser):
    """Collect every ``[data-island]`` element's name and declared topics."""

    def __init__(self) -> None:
        super().__init__()
        self.mount_points: list[MountPoint] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        found = dict(attrs)
        name = found.get("data-island")
        if name is None:
            return
        self.mount_points.append(
            MountPoint(
                name=name,
                publishes=_topics(found.get("data-pub")),
                subscribes=_topics(found.get("data-sub")),
            )
        )


def _topics(value: str | None) -> tuple[str, ...]:
    """A ``data-pub`` / ``data-sub`` attribute value as its topic tuple."""
    return tuple(t for t in (value or "").split(",") if t)


def _unique(names: Iterable[str]) -> tuple[str, ...]:
    """The names deduplicated, first occurrence winning (document order kept)."""
    return tuple(dict.fromkeys(names))
