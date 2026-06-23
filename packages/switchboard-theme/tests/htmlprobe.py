"""Parse rendered HTML into ``(tag, attrs)`` structure for tests.

Asserting on parsed elements and their attributes (rather than on raw
substrings) keeps tests robust to attribute order and escaping changes
(ASSERT_STRUCTURE_NOT_CONTENT). Stdlib only.
"""

from html.parser import HTMLParser


class _Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.elements: list[tuple[str, dict[str, str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.elements.append((tag, {k: (v or "") for k, v in attrs}))


def elements(html: str) -> list[tuple[str, dict[str, str]]]:
    """All start tags in document order, as ``(tag, attrs)`` pairs."""
    collector = _Collector()
    collector.feed(html)
    return collector.elements


def find(html: str, tag: str, **attrs: str) -> list[dict[str, str]]:
    """The attrs of every ``tag`` element whose attributes match ``attrs``."""
    return [
        a
        for (t, a) in elements(html)
        if t == tag and all(a.get(k) == v for k, v in attrs.items())
    ]
