"""A minimal, dependency-free HTML builder.

The renderer emits HTML strings; a string has no opinion about which backend
serves it (backend independence falls out of never returning a framework type).
This module is the smallest builder that escapes correctly:

- :func:`escape_text` escapes character data (element content).
- :func:`escape_attr` escapes a double-quoted attribute value.
- :func:`element` assembles a tag from already-rendered child fragments.

Children are treated as raw HTML (the caller has already escaped any leaf text),
so fragments compose without double-escaping.
"""

from collections.abc import Iterable, Mapping
from html import escape


def escape_text(value: str) -> str:
    """Escape ``value`` for use as element character data."""
    return escape(value, quote=False)


def escape_attr(value: str) -> str:
    """Escape ``value`` for use inside a double-quoted attribute."""
    return escape(value, quote=True)


def attributes(attrs: Mapping[str, str | None]) -> str:
    """Render attributes, omitting any whose value is ``None``.

    A leading space is included for each rendered attribute so the result drops
    directly after the tag name.
    """
    parts: list[str] = []
    for name, value in attrs.items():
        if value is None:
            continue
        parts.append(f' {name}="{escape_attr(value)}"')
    return "".join(parts)


def element(
    tag: str,
    attrs: Mapping[str, str | None] | None = None,
    children: Iterable[str] = (),
) -> str:
    """Render ``<tag ...>children</tag>`` from raw-HTML child fragments."""
    return f"<{tag}{attributes(attrs or {})}>{''.join(children)}</{tag}>"
