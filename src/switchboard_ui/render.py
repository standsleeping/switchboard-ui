"""Render a :class:`Shell` to a self-contained HTML document string.

The output is a ``str``; integration is a one-liner at the host's edge
(``HTMLResponse(render_shell(shell))``, ``path.write_text(...)``, ``print(...)``)
and that one-liner lives outside this package. The package imports no framework
type, so it is independent of any backend.

Two delivery modes for the CSS + JS runtime:

- ``"inline"`` embeds both, so the output is one droppable, host-free file.
- ``"linked"`` references ``shell.css`` / ``switchboard.js`` under ``asset_base``
  for a real app to serve and cache.
"""

import json
from collections.abc import Iterable, Sequence
from typing import Literal

from switchboard_ui.assets import read_static
from switchboard_ui.html import element, escape_attr, escape_text
from switchboard_ui.model import REGIONS, Document, Frame, Island, Shell, Slot

RuntimeMode = Literal["inline", "linked"]

_COMPACT = (",", ":")


def _render_island(island: Island, *, style: str | None = None) -> str:
    """Render an island mount-point ``<div>``, optionally with a flex style."""
    attrs: dict[str, str | None] = {
        "class": "sb-island",
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


def _render_region(region: str, islands: Sequence[Island]) -> str:
    """Render one grid region as a div carrying its islands.

    The div is emitted even when empty: it holds its geometry at first paint
    and collapses via CSS ``:empty`` when it hosts nothing.
    """
    attrs: dict[str, str | None] = {
        "class": f"sb-region sb-{region}",
        "data-region": region,
    }
    return element("div", attrs, [render_island(i) for i in islands])


def _render_frame(
    direction: str,
    children: Iterable[str],
    *,
    extra_class: str = "",
    style: str | None = None,
) -> str:
    """Render a flex stack: a div whose children lay out along ``direction``."""
    cls = f"sb-frame sb-frame-{direction}"
    if extra_class:
        cls = f"{cls} {extra_class}"
    return element("div", {"class": cls, "style": style}, children)


def _render_node(node: Island | Frame, *, style: str | None) -> str:
    """Render an island or a frame, with an optional flex style on its root."""
    if isinstance(node, Frame):
        return _render_frame(
            node.direction,
            [_render_child(c) for c in node.children],
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


def _render_shell_body(shell: Shell) -> str:
    """Render the nine-region shell as nested flex frames (the canonical preset).

    An outer column of three rows, each a flex row of three region cells. This
    is the general :func:`render_frame` primitive arranged into the standard
    application frame, so the layout is one mechanism (flex) at every level.
    """
    rows = [
        _render_frame(
            "row",
            [
                _render_region(region, shell.regions.get(region, ()))
                for region in REGIONS[start : start + 3]
            ],
            extra_class=f"sb-{row}",
        )
        for start, row in ((0, "head"), (3, "body"), (6, "foot"))
    ]
    return _render_frame("column", rows, extra_class="sb-shell")


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
        styles = f"<style>{read_static('shell.css')}</style>"
        runtime_tag = f"<script>{read_static('switchboard.js')}</script>"
    else:
        styles = f'<link rel="stylesheet" href="{escape_attr(asset_base)}shell.css">'
        runtime_tag = f'<script src="{escape_attr(asset_base)}switchboard.js"></script>'

    scripts = "".join(f"<script>{s}</script>" for s in extra_scripts)

    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<meta name="color-scheme" content="light dark">\n'
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


def render_shell(
    shell: Shell,
    *,
    runtime: RuntimeMode = "inline",
    asset_base: str = "",
    extra_head: str = "",
    extra_scripts: Sequence[str] = (),
) -> str:
    """Render ``shell`` to a complete ``<!doctype html>`` document string."""
    return _document(
        _render_shell_body(shell),
        title=shell.title,
        runtime=runtime,
        asset_base=asset_base,
        extra_head=extra_head,
        extra_scripts=extra_scripts,
    )


def _render_root(frame: Frame) -> str:
    """Render a frame as the viewport-locked document root (``sb-shell``)."""
    return _render_frame(
        frame.direction,
        [_render_child(c) for c in frame.children],
        extra_class="sb-shell",
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

    The body frame becomes the viewport-locked root; the envelope and keyword
    options are shared with :func:`render_shell`, so a general layout and the
    nine-region shell preset produce the same kind of page.
    """
    return _document(
        _render_root(document.body),
        title=document.title,
        runtime=runtime,
        asset_base=asset_base,
        extra_head=extra_head,
        extra_scripts=extra_scripts,
    )
