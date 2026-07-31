"""Real-browser regression tests for classic-scrollbar geometry.

Overlay scrollbars reserve nothing, so every case here first measures the
platform's own bar and skips when it has no width: under overlay bars these
assertions pass without exercising anything, and a skip records that honestly.
Because overlay is the default on every current desktop, these cases launch
their engines with the classic-bar switch each engine offers (see the module's
``page`` fixture); wherever the switch takes — or the user has set classic
bars themselves — the same measurements are the ones that can fail.

Two levels are tested separately because they are owned separately. An element
scroller's gutter is the structural sheet's (`.sb-overflow-auto` reserves it),
and every engine applies it. The viewport's gutter can only be declared from
the root element and is the theme's; engines differ on whether they apply the
root's declaration to the viewport at all, so the case that depends on it
probes for that first and skips where the declaration is inert.
"""

from collections.abc import Callable, Iterator

import pytest
from playwright.sync_api import Page, Playwright

from .conftest import Routes, Site
from .pages import themed_document_page, workbench_page

Serve = Callable[[Routes], Site]


@pytest.fixture
def page(playwright: Playwright, browser_name: str) -> Iterator[Page]:
    """A page in an engine launched with its classic-scrollbar switch thrown.

    Overlay bars are the default on every current desktop, including the CI
    runners, so a platform whose bars are classic cannot be waited for. Two
    engines offer a switch — Chromium a feature flag, Firefox a preference —
    and throwing it here scopes classic bars to exactly these cases. WebKit
    offers none, and macOS imposes the system setting on every engine, so the
    probe below still makes the final call and skips where nothing is
    reserved.
    """
    launcher = getattr(playwright, browser_name)
    options: dict[str, object] = {}
    if browser_name == "chromium":
        options["args"] = ["--disable-features=OverlayScrollbar"]
    if browser_name == "firefox":
        options["firefox_user_prefs"] = {"widget.gtk.overlay-scrolling.enabled": False}
    browser = launcher.launch(**options)
    try:
        yield browser.new_page()
    finally:
        browser.close()


_BAR_PROBE = (
    "(() => {const p = document.createElement('div');"
    " p.style.cssText ="
    "  'position:absolute;visibility:hidden;width:100px;height:100px;overflow:scroll';"
    " document.body.appendChild(p);"
    " const w = p.offsetWidth - p.clientWidth; p.remove(); return w})()"
)


def _classic_bar_width_or_skip(page: Page) -> int:
    """The platform bar's width, skipping the case where bars are overlay."""
    width = page.evaluate(_BAR_PROBE)
    if width == 0:
        pytest.skip("overlay scrollbars: nothing is reserved and nothing can shift")
    return int(width)


def test_a_cell_scroller_keeps_its_content_width_as_its_bar_comes_and_goes(
    page: Page, site: Serve
) -> None:
    """The reserved gutter, not the bar, owns the width it occupies.

    Measured on the content's own laid-out box rather than on the scroller's
    CSSOM properties: what must not move is what the reader sees. The cell
    starts overflowing (bar present), is emptied until its bar disappears, and
    the surviving paragraph's rectangle must not have changed.
    """
    server = site({"/": workbench_page()})
    page.goto(server.url("/"))
    _classic_bar_width_or_skip(page)

    assert page.evaluate(
        "(() => {const c = document.querySelector('.sb-body-c');"
        " return c.scrollHeight > c.clientHeight})()"
    ), "precondition: the cell must start with scroll range"
    before = page.evaluate(
        "(() => {const r = document.getElementById('para-0').getBoundingClientRect();"
        " return [r.left, r.width]})()"
    )

    page.evaluate(
        "document.querySelectorAll('.sb-body-c p').forEach("
        "  (el, i) => { if (i > 0) el.style.display = 'none' })"
    )
    assert not page.evaluate(
        "(() => {const c = document.querySelector('.sb-body-c');"
        " return c.scrollHeight > c.clientHeight})()"
    ), "precondition: emptying the cell must make its bar disappear"
    after = page.evaluate(
        "(() => {const r = document.getElementById('para-0').getBoundingClientRect();"
        " return [r.left, r.width]})()"
    )
    assert before == after, (
        f"the cell's content moved when its bar left: {before} -> {after}"
    )


def test_the_rail_and_the_article_edge_hold_when_the_page_bar_appears(
    page: Page, site: Serve
) -> None:
    """A page bar appearing moves neither the rail nor the article's start edge.

    This half holds in every engine regardless of viewport gutter support: the
    rail's basis is fixed, so the bar's width is taken from the article's end,
    never from the shared edge the reader aligns both columns by.
    """
    server = site(
        {
            "/short": themed_document_page(paragraphs=1, nav_items=3),
            "/long": themed_document_page(paragraphs=60, nav_items=60),
        }
    )
    measure = (
        "(() => {const m = el => {const r = el.getBoundingClientRect();"
        "  return [r.left, r.width]};"
        " return {nav: m(document.querySelector('.sb-body-l')),"
        "  articleLeft: document.querySelector('.sb-body-c')"
        "   .getBoundingClientRect().left}})()"
    )

    page.goto(server.url("/short"))
    _classic_bar_width_or_skip(page)
    assert not page.evaluate(
        "document.documentElement.scrollHeight > document.documentElement.clientHeight"
    ), "precondition: the short page must fit the viewport"
    short = page.evaluate(measure)

    page.goto(server.url("/long"))
    assert page.evaluate(
        "document.documentElement.scrollHeight > document.documentElement.clientHeight"
    ), "precondition: the long page must scroll"
    long = page.evaluate(measure)

    assert short == long, f"the page bar moved a column edge: {short} -> {long}"


def test_the_article_width_holds_where_the_viewport_reserves_its_gutter(
    page: Page, site: Serve
) -> None:
    """Where the root's declared gutter reaches the viewport, nothing reflows.

    The declaration is the theme's `scrollbar-gutter: stable` on the root
    element, which is the only place a viewport gutter can be declared from.
    Engines that do not apply it to the viewport are skipped by measurement
    rather than by name: on those, the bar's width comes out of the article
    instead, which is the documented fallback, not a defect this suite owns.
    """
    server = site(
        {
            "/short": themed_document_page(paragraphs=1, nav_items=3),
            "/long": themed_document_page(paragraphs=60, nav_items=60),
        }
    )
    page.goto(server.url("/short"))
    _classic_bar_width_or_skip(page)
    reserved = page.evaluate("innerWidth - document.documentElement.clientWidth")
    if reserved == 0:
        pytest.skip(
            "this engine does not apply the root's scrollbar-gutter to the viewport"
        )

    width = "document.querySelector('.sb-body-c').getBoundingClientRect().width"
    short = page.evaluate(width)
    page.goto(server.url("/long"))
    long = page.evaluate(width)
    assert short == long, f"the page bar reflowed the article: {short} -> {long}"
