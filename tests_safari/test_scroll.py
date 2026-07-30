"""Real-Safari regression tests for scroll ownership and rail continuity.

The same contracts the Playwright suite proves in its three bundled engines,
re-proven against the engine Safari actually ships. The back/forward case is
the one that is genuinely different here rather than merely re-run: Safari's
cache restores a stored document's element scroll itself, and the adapter's
obligation on that path is to leave the restoration alone.
"""

from collections.abc import Callable

from selenium.webdriver import Safari
from selenium.webdriver.common.by import By
from tests_browser.conftest import Routes, Site
from tests_browser.pages import (
    anchor_page,
    document_page,
    site_routes,
    workbench_page,
)

from .conftest import wait_until

Serve = Callable[[Routes], Site]


def test_a_sticky_rail_holds_while_the_article_scrolls_past(
    safari: Safari, site: Serve
) -> None:
    """The rail pins at the top; the article keeps moving."""
    server = site({"/": document_page()})
    safari.get(server.url("/"))
    measure = (
        "return {nav: document.querySelector('.sb-body-l')"
        ".getBoundingClientRect().top,"
        " art: document.querySelector('.sb-body-c').getBoundingClientRect().top}"
    )
    before = safari.execute_script(measure)
    safari.execute_script("window.scrollTo(0, 900)")
    after = safari.execute_script(measure)
    assert round(before["art"] - after["art"]) == 900
    assert 0 <= round(before["nav"] - after["nav"]) < 900


def test_the_foot_rail_ends_the_document_on_long_and_short_pages(
    safari: Safari, site: Serve
) -> None:
    """The foot sits at the document's end, which on a short page is the fold.

    Two pages, one claim: the document ends where the foot does. A long page
    scrolled to its bottom shows the foot with nothing below it; a page shorter
    than the viewport shows the foot at the viewport's bottom edge rather than
    partway up.
    """
    server = site(
        {
            "/long": document_page(),
            "/short": document_page(paragraphs=1, nav_items=3),
        }
    )
    safari.get(server.url("/long"))
    safari.execute_script("window.scrollTo(0, document.documentElement.scrollHeight)")
    gap = safari.execute_script(
        "const r = document.querySelector('.sb-foot-row').getBoundingClientRect();"
        "return document.documentElement.scrollHeight - (window.scrollY + r.bottom)"
    )
    assert abs(gap) <= 1, f"{gap}px of nothing below the foot at the bottom"

    safari.get(server.url("/short"))
    short = safari.execute_script(
        "return {scrolls: document.documentElement.scrollHeight"
        " > document.documentElement.clientHeight,"
        " gap: window.innerHeight - document.querySelector('.sb-foot-row')"
        ".getBoundingClientRect().bottom}"
    )
    assert not short["scrolls"], "precondition: the short page must fit the viewport"
    assert abs(short["gap"]) <= 1, f"the foot floated {short['gap']}px above the fold"


def test_the_rail_offset_survives_a_real_cross_page_navigation(
    safari: Safari, site: Serve
) -> None:
    """A scrolled rail is where the reader left it on the next page."""
    server = site(site_routes())
    safari.get(server.url("/page-0"))
    safari.execute_script(
        "const r = document.querySelector('.sb-body-l');"
        "r.scrollTop = 445; r.dispatchEvent(new Event('scroll'))"
    )
    wait_until(safari, "sessionStorage.getItem('sb-nav-scroll:fixture-nav') === '445'")

    # A row already on screen at this offset: the driver scrolls a target into
    # view before clicking, so a row above the fold would move the rail and the
    # case would measure its own side effect.
    safari.find_element(By.CSS_SELECTOR, "a[href='/page-20']").click()
    wait_until(safari, "location.pathname === '/page-20'")
    wait_until(safari, "document.querySelector('.sb-body-l').scrollTop === 445")


def test_a_back_navigation_restores_the_rail(safari: Safari, site: Serve) -> None:
    """Going back puts the rail where the reader left it, on either path.

    Safari decides whether this history navigation is served from its
    back/forward cache or re-fetched, and the two paths restore differently:
    a cached document keeps its live DOM, whose element scroll the browser
    itself restores with the adapter standing down; a re-fetched one is a
    fresh document the adapter restores from storage. The reader-visible
    claim is the same either way, and which path ran is Safari's business,
    not the assertion's.
    """
    server = site(site_routes())
    safari.get(server.url("/page-0"))
    safari.execute_script(
        "const r = document.querySelector('.sb-body-l');"
        "r.scrollTop = 300; r.dispatchEvent(new Event('scroll'))"
    )
    wait_until(safari, "sessionStorage.getItem('sb-nav-scroll:fixture-nav') === '300'")
    safari.find_element(By.CSS_SELECTOR, "a[href='/page-14']").click()
    wait_until(safari, "location.pathname === '/page-14'")

    safari.back()
    wait_until(safari, "location.pathname === '/page-0'")
    wait_until(safari, "document.querySelector('.sb-body-l').scrollTop === 300")
    # Restored, not restored-and-re-saved-and-restored: the stored value is
    # still the one the reader left behind.
    assert (
        safari.execute_script(
            "return sessionStorage.getItem('sb-nav-scroll:fixture-nav')"
        )
        == "300"
    )


def test_a_direct_load_reveals_a_current_item_below_the_fold(
    safari: Safari, site: Serve
) -> None:
    """A first visit scrolls the rail just enough to show where the reader is."""
    server = site(site_routes())
    safari.get(server.url("/page-38"))
    wait_until(
        safari,
        "!document.querySelector('.sb-body-l').hasAttribute('data-sb-restoring')",
    )
    revealed = safari.execute_script(
        "const rail = document.querySelector('.sb-body-l');"
        "const cur = rail.querySelector('[aria-current=page]');"
        "const i = cur.getBoundingClientRect(), v = rail.getBoundingClientRect();"
        "return {top: rail.scrollTop,"
        " visible: i.top >= v.top - 1 && i.bottom <= v.bottom + 1}"
    )
    assert revealed["visible"], f"current item not revealed: {revealed}"
    assert revealed["top"] > 0, "the rail never moved, so nothing was revealed"


def test_an_anchor_jump_lands_the_heading_below_the_edge_by_its_margin(
    safari: Safari, site: Serve
) -> None:
    """The heading clears the edge by its declared scroll margin, not zero."""
    server = site({"/": anchor_page()})
    safari.get(server.url("/"))
    margin = safari.execute_script(
        "return parseFloat(getComputedStyle(document.getElementById('landing'))"
        ".scrollMarginBlockStart)"
    )
    assert margin > 0, "precondition: the theme must give the heading a scroll margin"

    safari.find_element(By.CSS_SELECTOR, "a[href='#landing']").click()
    top = safari.execute_script(
        "return document.getElementById('landing').getBoundingClientRect().top"
    )
    assert abs(top - margin) <= 1, (
        f"the heading landed {top}px from the edge; its scroll margin is {margin}px"
    )


def test_a_workbench_stays_viewport_sized_and_delegates_its_scroll(
    safari: Safari, site: Serve
) -> None:
    """The page never scrolls; the body cells do, and nothing leaks past the root."""
    server = site({"/": workbench_page()})
    safari.get(server.url("/"))
    assert not safari.execute_script(
        "return document.documentElement.scrollHeight"
        " > document.documentElement.clientHeight"
    )
    safari.execute_script("document.querySelector('.sb-body-c').scrollTop = 300")
    assert (
        safari.execute_script("return document.querySelector('.sb-body-c').scrollTop")
        == 300
    )
    assert safari.execute_script("return window.scrollY") == 0
