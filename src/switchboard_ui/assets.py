"""Read packaged static assets (the CSS/JS shipped under ``static/``).

One reader for both the renderer (layout.css, switchboard.js) and the demo
(its island adapters), so package data is read one way, memoized once.
"""

from functools import cache
from importlib.resources import files


@cache
def read_static(name: str) -> str:
    """Read a packaged asset under ``static/`` as text (read once per name)."""
    return (files("switchboard_ui") / "static" / name).read_text(encoding="utf-8")
