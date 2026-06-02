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
from collections.abc import Sequence
from typing import Literal

from switchboard_ui.assets import read_static
from switchboard_ui.html import element, escape_attr, escape_text
from switchboard_ui.model import REGIONS, Island, Shell

RuntimeMode = Literal["inline", "linked"]

_COMPACT = (",", ":")


def render_island(island: Island) -> str:
    """Render a single island as its declarative mount-point ``<div>``."""
    attrs: dict[str, str | None] = {
        "class": "sb-island",
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


def render_shell(
    shell: Shell,
    *,
    runtime: RuntimeMode = "inline",
    asset_base: str = "",
    extra_head: str = "",
    extra_scripts: Sequence[str] = (),
) -> str:
    """Render ``shell`` to a complete ``<!doctype html>`` document string."""
    if runtime == "inline":
        styles = f"<style>{read_static('shell.css')}</style>"
        runtime_tag = f"<script>{read_static('switchboard.js')}</script>"
    else:
        styles = f'<link rel="stylesheet" href="{escape_attr(asset_base)}shell.css">'
        runtime_tag = f'<script src="{escape_attr(asset_base)}switchboard.js"></script>'

    regions = "".join(
        _render_region(region, shell.regions.get(region, ())) for region in REGIONS
    )
    body = element("div", {"class": "sb-shell"}, [regions])
    scripts = "".join(f"<script>{s}</script>" for s in extra_scripts)

    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<meta name="color-scheme" content="light dark">\n'
        f"<title>{escape_text(shell.title)}</title>\n"
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
