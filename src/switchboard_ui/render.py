"""Render a :class:`Document` to a self-contained HTML document string.

The output is a ``str``; integration is a one-liner at the host's edge
(``HTMLResponse(render_document(doc))``, ``path.write_text(...)``, ``print(...)``)
and that one-liner lives outside this package. The package imports no framework
type, so it is independent of any backend.

Two delivery modes for the CSS + JS runtime:

- ``"inline"`` embeds them, so the output is one droppable, host-free file.
- ``"linked"`` references ``layout.css``, ``switchboard.js``, and the optional
  ``switchboard-debug.js`` overlay under ``asset_base`` for a real app to serve
  and cache.
"""

import json
from collections.abc import Iterable, Sequence
from typing import Literal

from switchboard_ui.assets import read_static
from switchboard_ui.html import element, escape_attr, escape_text
from switchboard_ui.model import Document, Frame, Island, Slot

RuntimeMode = Literal["inline", "linked"]

_COMPACT = (",", ":")


def _classes(*parts: str) -> str:
    """Join non-empty class fragments with spaces."""
    return " ".join(p for p in parts if p)


def _render_island(island: Island, *, style: str | None = None) -> str:
    """Render an island mount-point ``<div>``, optionally with a flex style."""
    attrs: dict[str, str | None] = {
        "class": _classes("sb-island", island.class_),
        "style": style,
        "data-island": island.name,
        "data-props": (
            json.dumps(island.props, sort_keys=True, separators=_COMPACT)
            if island.props
            else None
        ),
        "data-pub": ",".join(island.publishes) if island.publishes else None,
        "data-sub": ",".join(island.subscribes) if island.subscribes else None,
    }
    return element("div", attrs, [island.initial])


def render_island(island: Island) -> str:
    """Render a single island as its declarative mount-point ``<div>``."""
    return _render_island(island)


def _render_frame(
    direction: str,
    children: Iterable[str],
    *,
    extra_class: str = "",
    style: str | None = None,
) -> str:
    """Render a flex stack: a div whose children lay out along ``direction``."""
    cls = _classes("sb-frame", f"sb-frame-{direction}", extra_class)
    return element("div", {"class": cls, "style": style}, children)


def _render_node(node: Island | Frame, *, style: str | None) -> str:
    """Render an island or a frame, with an optional flex style on its root."""
    if isinstance(node, Frame):
        return _render_frame(
            node.direction,
            [_render_child(c) for c in node.children],
            extra_class=node.class_,
            style=style,
        )
    return _render_island(node, style=style)


def _render_child(child: Island | Frame | Slot) -> str:
    """Render one frame child, applying its slot sizing if it has any.

    A bare island or frame is content-sized; a :class:`Slot` pins it to a fixed
    main-axis size (``flex: 0 0 basis``) or makes it flexible (``flex: 1 1 0``).
    """
    if isinstance(child, Slot):
        flex = "1 1 0" if child.basis is None else f"0 0 {child.basis}"
        return _render_node(child.child, style=f"flex: {flex}")
    return _render_node(child, style=None)


def render_frame(frame: Frame) -> str:
    """Render a :class:`Frame` and its children recursively."""
    return _render_node(frame, style=None)


def _document(
    body: str,
    *,
    title: str,
    runtime: RuntimeMode,
    asset_base: str,
    extra_head: str,
    extra_scripts: Sequence[str],
) -> str:
    """Wrap a rendered body fragment in the HTML document envelope.

    The envelope (doctype, head, asset delivery) belongs to the root page only;
    the body is any HTML fragment. Separating the two is what lets a layout be
    rendered standalone or nested inside another.
    """
    if runtime == "inline":
        styles = f"<style>{read_static('layout.css')}</style>"
        runtime_tag = (
            f"<script>{read_static('switchboard.js')}</script>"
            f"<script>{read_static('switchboard-debug.js')}</script>"
        )
    else:
        styles = f'<link rel="stylesheet" href="{escape_attr(asset_base)}layout.css">'
        runtime_tag = (
            f'<script src="{escape_attr(asset_base)}switchboard.js"></script>'
            f'<script src="{escape_attr(asset_base)}switchboard-debug.js"></script>'
        )

    scripts = "".join(f"<script>{s}</script>" for s in extra_scripts)

    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f"<title>{escape_text(title)}</title>\n"
        f"{styles}\n"
        f"{extra_head}"
        "</head>\n"
        "<body>\n"
        f"{body}\n"
        f"{runtime_tag}\n"
        f"{scripts}"
        "</body>\n"
        "</html>\n"
    )


def _render_root(frame: Frame) -> str:
    """Render a frame as the viewport-locked document root (``sb-root``)."""
    return _render_frame(
        frame.direction,
        [_render_child(c) for c in frame.children],
        extra_class=_classes("sb-root", frame.class_),
    )


def render_document(
    document: Document,
    *,
    runtime: RuntimeMode = "inline",
    asset_base: str = "",
    extra_head: str = "",
    extra_scripts: Sequence[str] = (),
) -> str:
    """Render a :class:`Document` (a root layout frame plus a title) to a page.

    The body frame becomes the viewport-locked root. Build the document by hand,
    or from a preset such as ``three_column`` in :mod:`switchboard_ui.presets`.
    """
    return _document(
        _render_root(document.body),
        title=document.title,
        runtime=runtime,
        asset_base=asset_base,
        extra_head=extra_head,
        extra_scripts=extra_scripts,
    )
