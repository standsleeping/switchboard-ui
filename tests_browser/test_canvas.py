"""Real-browser regression test for the canvas behind the page.

Overscroll — rubber-banding past the document's edges — exposes the browser's
canvas, which is painted by the root element's background or by nothing. The
gesture itself cannot be synthesized, but the colour it would expose can be
measured: the root's resolved background must be opaque and must follow the
colour scheme, or dark-mode overscroll flashes the user agent's pale canvas.
"""

from collections.abc import Callable

from playwright.sync_api import Page

from .conftest import Routes, Site
from .pages import themed_document_page

Serve = Callable[[Routes], Site]


def test_the_root_paints_the_canvas_in_both_schemes(page: Page, site: Serve) -> None:
    """The canvas colour is the theme's surface in light and in dark."""
    server = site({"/": themed_document_page(paragraphs=1, nav_items=3)})
    resolved: dict[str, str] = {}
    for scheme in ("light", "dark"):
        page.emulate_media(color_scheme=scheme)
        page.goto(server.url("/"))
        colour = page.evaluate(
            "getComputedStyle(document.documentElement).backgroundColor"
        )
        assert colour not in ("rgba(0, 0, 0, 0)", "transparent"), (
            f"the root paints nothing in {scheme}; overscroll would expose the"
            " user agent's canvas"
        )
        resolved[scheme] = colour
    assert resolved["light"] != resolved["dark"], (
        "the canvas ignores the colour scheme; dark overscroll would flash light"
    )
