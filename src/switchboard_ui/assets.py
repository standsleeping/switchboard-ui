"""Read packaged static assets (the CSS/JS/fonts shipped under a ``static/`` dir).

One memoized reader for every packaged ``static/`` directory: the mechanism's
own (layout.css, switchboard.js, the switchboard-debug.js overlay, the demo
adapters) via :func:`read_static`, and any sibling subpackage's (the theme's
``static/<name>.css``) via :func:`read_asset` with that subpackage's name. The
reader takes a package *name* and never imports a subpackage, so it can serve
the theme layer without the mechanism ever depending on it.
"""

from functools import cache
from importlib.resources import files


@cache
def read_asset(package: str, name: str) -> str:
    """Read ``static/<name>`` under ``package`` as text (read once per pair)."""
    return (files(package) / "static" / name).read_text(encoding="utf-8")


@cache
def read_asset_bytes(package: str, name: str) -> bytes:
    """Read ``static/<name>`` under ``package`` as bytes (read once per pair).

    The binary sibling of :func:`read_asset`, for assets that are not text (a
    packaged font file) and are served by a host rather than inlined.
    """
    return (files(package) / "static" / name).read_bytes()


def read_static(name: str) -> str:
    """Read a packaged asset under ``switchboard_ui/static/`` as text."""
    return read_asset("switchboard_ui", name)
