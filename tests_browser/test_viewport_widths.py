"""Real-browser regression tests for the horizontal contract across widths.

One claim at every width from tablet to wide desktop: the page never scrolls
sideways. Content that is genuinely wider than the viewport — a long code
line — scrolls inside its own box instead of pushing the page. Below tablet
width is out of scope by design; a narrow drawer is separate work.
"""

from collections.abc import Callable

import pytest
from playwright.sync_api import Page

from .conftest import Routes, Site
from .pages import document_page, wide_code_page, workbench_page

Serve = Callable[[Routes], Site]

WIDTHS = (768, 1024, 1470, 1920)


@pytest.mark.parametrize("width", WIDTHS)
def test_no_surface_scrolls_the_page_sideways(
    page: Page, site: Serve, width: int
) -> None:
    """Neither shape leaks horizontally at any width."""
    server = site(
        {
            "/doc": document_page(),
            "/bench": workbench_page(),
            "/code": wide_code_page(),
        }
    )
    page.set_viewport_size({"width": width, "height": 720})
    for path in ("/doc", "/bench", "/code"):
        page.goto(server.url(path))
        leak = page.evaluate(
            "document.documentElement.scrollWidth"
            " - document.documentElement.clientWidth"
        )
        assert leak <= 0, f"{path} leaks {leak}px sideways at {width}px"


@pytest.mark.parametrize("width", WIDTHS)
def test_a_wide_code_block_scrolls_within_itself(
    page: Page, site: Serve, width: int
) -> None:
    """The long line scrolls inside the block; the page does not move for it."""
    server = site({"/": wide_code_page()})
    page.set_viewport_size({"width": width, "height": 720})
    page.goto(server.url("/"))
    state = page.evaluate(
        "(() => {const pre = document.querySelector('.sb-code-pre');"
        " return {scrolls: pre.scrollWidth > pre.clientWidth,"
        "  leak: document.documentElement.scrollWidth"
        "   - document.documentElement.clientWidth}})()"
    )
    assert state["scrolls"], "precondition: the line must be wider than the block"
    assert state["leak"] <= 0, f"the wide line leaked {state['leak']}px into the page"
