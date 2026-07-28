"""Real-browser regression tests for scroll ownership and rail continuity.

The original defect these guard: a left rail scrolled to 445, a real link click,
and the next page's rail starting at 0 with the current item 419px below the
fold. Nothing in a rendered-HTML assertion can see that, because it is a fact
about a second document's first painted frame.
"""

from collections.abc import Callable

from playwright.sync_api import Page

from .conftest import Routes, Site
from .pages import clipped_page, document_page, site_routes, workbench_page

Serve = Callable[[Routes], Site]


def test_a_flow_document_scrolls_at_the_page_level(page: Page, site: Serve) -> None:
    """A document taller than the viewport scrolls as a page; the root is not fixed."""
    server = site({"/": document_page()})
    page.goto(server.url("/"))
    assert page.evaluate(
        "document.documentElement.scrollHeight > document.documentElement.clientHeight"
    )
    assert (
        page.evaluate("getComputedStyle(document.querySelector('.sb-root')).position")
        == "static"
    )
    page.evaluate("window.scrollTo(0, 400)")
    assert page.evaluate("window.scrollY") == 400


def test_a_workbench_stays_viewport_sized_and_delegates_its_scroll(
    page: Page, site: Serve
) -> None:
    """The page never scrolls; the body cells do, and nothing leaks past the root."""
    server = site({"/": workbench_page()})
    page.goto(server.url("/"))
    assert not page.evaluate(
        "document.documentElement.scrollHeight > document.documentElement.clientHeight"
    )
    assert page.evaluate(
        "(() => {const c = document.querySelector('.sb-body-c');"
        " return c.scrollHeight > c.clientHeight})()"
    )
    page.evaluate("document.querySelector('.sb-body-c').scrollTop = 300")
    assert page.evaluate("document.querySelector('.sb-body-c').scrollTop") == 300
    assert page.evaluate("window.scrollY") == 0


def test_a_sticky_rail_holds_while_the_article_scrolls_past(
    page: Page, site: Serve
) -> None:
    """The rail pins at the top; the article keeps moving."""
    server = site({"/": document_page()})
    page.goto(server.url("/"))
    before = page.evaluate(
        "({nav: document.querySelector('.sb-body-l').getBoundingClientRect().top,"
        "  art: document.querySelector('.sb-body-c').getBoundingClientRect().top})"
    )
    page.evaluate("window.scrollTo(0, 900)")
    after = page.evaluate(
        "({nav: document.querySelector('.sb-body-l').getBoundingClientRect().top,"
        "  art: document.querySelector('.sb-body-c').getBoundingClientRect().top})"
    )
    assert round(before["art"] - after["art"]) == 900
    # The rail travelled only as far as its own start edge, then pinned.
    assert 0 <= round(before["nav"] - after["nav"]) < 900


def test_the_rail_offset_survives_a_real_cross_page_navigation(
    page: Page, slow_site: Serve
) -> None:
    """The reproduced 445-to-0 reset: gone, and gone before the first frame.

    Served in delayed chunks on purpose. In one flush the parser reaches the end
    of the body in the same task that began the document, so *any* end-of-body
    script would beat the first paint and this test would pass against a design
    that fails on a real connection.
    """
    server = slow_site(site_routes())
    page.goto(server.url("/page-0"))
    page.evaluate("document.querySelector('.sb-body-l').scrollTop = 445")
    page.evaluate(
        "document.querySelector('.sb-body-l').dispatchEvent(new Event('scroll'))"
    )
    page.wait_for_function(
        "() => sessionStorage.getItem('sb-nav-scroll:fixture-nav') === '445'"
    )

    # A row already on screen at this offset: the driver scrolls a target into
    # view before clicking, so a row above the fold would move the rail and the
    # case would measure its own side effect.
    page.click("a[href='/page-20']")
    page.wait_for_url("**/page-20")
    assert page.evaluate("document.querySelector('.sb-body-l').scrollTop") == 445


def test_the_complete_rail_is_never_painted_at_zero(
    page: Page, slow_site: Serve
) -> None:
    """No frame ever shows the finished rail at the top when it should be scrolled.

    Sampled from inside the document, every animation frame, because the claim is
    about what a reader could see rather than about the value that eventually
    settles. Reading ``scrollTop`` after ``goto`` returns would pass against a
    design that paints zero and then corrects.

    The rail is deliberately only checked once it is *complete*. Under chunked
    delivery the browser paints a partly-parsed rail, and a rail holding four of
    its forty rows has no 445 to be at — there is nothing yet to restore to. The
    defect being guarded is the visible correction: a fully built rail painted at
    the top and then snapped down. So every frame whose rail has reached its
    final height must already be at the restored offset.
    """
    routes = site_routes()
    # Sampled *after* each frame paints: a task scheduled from inside the frame
    # callback runs post-paint, so it reads the values the reader actually saw.
    # Reading inside the frame callback instead would race the restoration's own
    # callback and report pre-correction values that were never displayed.
    probe = (
        "<script>window.__painted = [];"
        "(function sample() {"
        "  requestAnimationFrame(() => {"
        "    setTimeout(() => {"
        "      const r = document.querySelector('.sb-body-l');"
        "      if (r) window.__painted.push("
        "        [r.scrollHeight, r.scrollTop, r.clientHeight]);"
        "    }, 0);"
        "    sample();"
        "  });"
        "})();</script>"
    )
    routes["/page-20"] = routes["/page-20"].replace("<body", probe + "<body", 1)
    server = slow_site(routes)

    page.goto(server.url("/page-0"))
    page.evaluate("document.querySelector('.sb-body-l').scrollTop = 445")
    page.evaluate(
        "document.querySelector('.sb-body-l').dispatchEvent(new Event('scroll'))"
    )
    page.wait_for_function(
        "() => sessionStorage.getItem('sb-nav-scroll:fixture-nav') === '445'"
    )

    page.click("a[href='/page-20']")
    page.wait_for_url("**/page-20")
    page.wait_for_load_state("load")

    final_height = page.evaluate("document.querySelector('.sb-body-l').scrollHeight")
    painted = page.evaluate("window.__painted")
    complete = [top for height, top, _ in painted if height == final_height]
    assert complete, "no frame observed with the rail at its final height"
    assert set(complete) == {445}, (
        f"the finished rail was painted at {sorted(set(complete))} before "
        "settling; restoration must precede the first complete paint"
    )
    # While the rail is still filling, every frame is scrolled as far as the
    # range that exists allows. A rail shorter than the viewport has no range at
    # all, so zero is the only possible answer there and is not a defect.
    short = [
        (height, top, client)
        for height, top, client in painted
        if height > client and top != min(445, height - client)
    ]
    assert not short, f"a partly-built rail wasted the range it had: {short}"


def test_a_direct_load_reveals_a_current_item_below_the_fold(
    page: Page, site: Serve
) -> None:
    """A first visit scrolls the rail just enough to show where the reader is.

    A deep link, a search result, or a shared URL arrives with no stored offset,
    so the rail opens at the top. On a long rail the page actually being read can
    sit far below the fold, and a nav that does not show your position is worse
    than no nav: it silently asserts you are somewhere near the beginning.
    """
    server = site(site_routes())
    page.goto(server.url("/page-38"))
    page.wait_for_load_state("load")
    # Placement finishes in a frame callback, so it can land after `load`. The
    # rail advertises that it is in flight, which is a fact about the code rather
    # than a guess about the machine, so wait on that and then assert the result.
    page.wait_for_function(
        "() => !document.querySelector('.sb-body-l').hasAttribute('data-sb-restoring')"
    )
    revealed = page.evaluate(
        "(() => {const rail = document.querySelector('.sb-body-l');"
        " const cur = rail.querySelector('[aria-current=page]');"
        " const i = cur.getBoundingClientRect(), v = rail.getBoundingClientRect();"
        " return {top: rail.scrollTop, label: cur.textContent.trim(),"
        "  visible: i.top >= v.top - 1 && i.bottom <= v.bottom + 1}})()"
    )
    assert revealed["visible"], f"current item not revealed: {revealed}"
    assert revealed["top"] > 0, "the rail never moved, so nothing was revealed"


def test_revealing_scrolls_by_the_smallest_amount_that_works(
    page: Page, site: Serve
) -> None:
    """The current item lands against the nearest edge, not centred.

    Minimal on purpose. Scrolling further than necessary moves rows the reader
    has no reason to expect to move, and on a first visit they have no mental
    model of the rail yet to absorb the surprise.
    """
    server = site(site_routes())
    page.goto(server.url("/page-38"))
    page.wait_for_load_state("load")
    # Placement finishes in a frame callback, so it can land after `load`. The
    # rail advertises that it is in flight, which is a fact about the code rather
    # than a guess about the machine, so wait on that and then assert the result.
    page.wait_for_function(
        "() => !document.querySelector('.sb-body-l').hasAttribute('data-sb-restoring')"
    )
    flush = page.evaluate(
        "(() => {const rail = document.querySelector('.sb-body-l');"
        " const cur = rail.querySelector('[aria-current=page]');"
        " const i = cur.getBoundingClientRect(), v = rail.getBoundingClientRect();"
        " return Math.round(i.bottom - v.bottom)})()"
    )
    # Scrolled down to reach it, so it sits against the trailing edge.
    assert abs(flush) <= 1, f"item is {flush}px from the near edge, not flush"


def test_a_direct_load_leaves_an_already_visible_current_item_alone(
    page: Page, site: Serve
) -> None:
    """Nothing moves when the current item is already on screen.

    Revealing is a repair for a rail that hides your position, not a habit. A
    rail that already shows it should open exactly as authored.
    """
    server = site(site_routes())
    page.goto(server.url("/page-0"))
    page.wait_for_load_state("load")
    # Placement finishes in a frame callback, so it can land after `load`. The
    # rail advertises that it is in flight, which is a fact about the code rather
    # than a guess about the machine, so wait on that and then assert the result.
    page.wait_for_function(
        "() => !document.querySelector('.sb-body-l').hasAttribute('data-sb-restoring')"
    )
    assert page.evaluate("document.querySelector('.sb-body-l').scrollTop") == 0


def test_a_stored_offset_takes_precedence_over_revealing(
    page: Page, site: Serve
) -> None:
    """Continuing a visit beats introducing one.

    Once the reader has a position in the rail it is theirs, even if it does not
    show the current page. Overriding it to reveal would undo the continuity the
    stored offset exists to provide.
    """
    server = site(site_routes())
    page.goto(server.url("/page-0"))
    page.evaluate("document.querySelector('.sb-body-l').scrollTop = 120")
    page.evaluate(
        "document.querySelector('.sb-body-l').dispatchEvent(new Event('scroll'))"
    )
    page.wait_for_function(
        "() => sessionStorage.getItem('sb-nav-scroll:fixture-nav') === '120'"
    )
    page.click("a[href='/page-4']")
    page.wait_for_url("**/page-4")
    page.wait_for_function(
        "() => document.querySelector('.sb-body-l').scrollTop === 120",
        timeout=3000,
    )


def test_a_corrupt_stored_offset_is_ignored(page: Page, site: Serve) -> None:
    """A non-finite or negative value must move the rail by nothing at all."""
    server = site(site_routes())
    page.goto(server.url("/page-0"))
    for bad in ("NaN", "Infinity", "-40", "garbage"):
        page.evaluate(f"sessionStorage.setItem('sb-nav-scroll:fixture-nav', {bad!r})")
        page.goto(server.url("/page-1"))
        assert page.evaluate("document.querySelector('.sb-body-l').scrollTop") == 0


def test_a_back_navigation_restores_the_rail_exactly_once(
    page: Page, site: Serve
) -> None:
    """Going back re-fetches the page and puts the rail where the reader left it.

    Which path this exercises is worth stating: the fixture sends
    ``Cache-Control: no-store``, which disables the back/forward cache, so this
    is the *re-fetched* history navigation — a fresh document, and therefore the
    path that needs restoring at all. The bfcache path is deliberately untouched
    by the adapter, since it reuses the live DOM whose element scroll the browser
    has already restored; that it never listens for ``pageshow`` is asserted in
    the unit tests, where it is a property of the source rather than of a run.
    """
    server = site(site_routes())
    page.goto(server.url("/page-0"))
    page.evaluate("document.querySelector('.sb-body-l').scrollTop = 300")
    page.evaluate(
        "document.querySelector('.sb-body-l').dispatchEvent(new Event('scroll'))"
    )
    page.wait_for_function(
        "() => sessionStorage.getItem('sb-nav-scroll:fixture-nav') === '300'"
    )
    page.click("a[href='/page-14']")
    page.wait_for_url("**/page-14")

    page.go_back()
    page.wait_for_url("**/page-0")
    page.wait_for_load_state("load")
    # Waited for rather than sampled at a fixed frame. Restoration runs in a
    # frame callback and re-applies as the rail gains range, so which frame it
    # lands on depends on how the document arrived; pinning a frame count tests
    # the machine's load, not the code. That it lands before any *visible* wrong
    # frame is the separate claim of the first-paint case above, which samples
    # every painted frame; this one asserts only that going back restores.
    page.wait_for_function(
        "() => document.querySelector('.sb-body-l').scrollTop === 300",
        timeout=3000,
    )
    # Restored, not restored-and-re-saved-and-restored: the stored value is
    # still the one the reader left behind.
    assert page.evaluate("sessionStorage.getItem('sb-nav-scroll:fixture-nav')") == "300"


def test_short_and_long_pages_keep_the_same_column_geometry(
    page: Page, site: Serve
) -> None:
    """A scrollbar appearing must not move the column it appears in.

    Under overlay scrollbars the bar reserves nothing and this holds trivially;
    under classic scrollbars the reserved gutter is what makes it hold. The
    assertion is the same either way, which is the point of reserving.
    """
    server = site(
        {
            "/short": document_page(paragraphs=1, nav_items=3),
            "/long": document_page(paragraphs=60, nav_items=60),
        }
    )
    page.goto(server.url("/short"))
    short = page.evaluate("document.querySelector('.sb-body-l').clientWidth")
    page.goto(server.url("/long"))
    long = page.evaluate("document.querySelector('.sb-body-l').clientWidth")
    assert short == long


def test_marking_the_current_item_moves_no_row(page: Page, site: Serve) -> None:
    """State repaints; it does not reshape. Measured on the real face.

    This is the browser half of the static state-geometry guard: the guard proves
    no state rule *declares* a geometry property, and this proves the paint it
    does declare — including the bold current row — changes no rectangle.
    """
    server = site({"/": document_page()})
    page.goto(server.url("/"))
    measure = (
        "[...document.querySelectorAll('.sb-nav-item')]"
        ".map(a => {const r = a.getBoundingClientRect();"
        " return [Math.round(r.x), Math.round(r.y), Math.round(r.width),"
        " Math.round(r.height)]})"
    )
    before = page.evaluate(measure)
    page.evaluate(
        "document.querySelectorAll('.sb-nav-item').forEach("
        "  a => a.setAttribute('aria-current', 'false'))"
    )
    after = page.evaluate(measure)
    assert before == after


def test_a_three_level_nav_is_keyboard_reachable_at_every_depth(
    page: Page, site: Serve
) -> None:
    """Every row can be focused, and focus never lands outside the visible rail."""
    server = site({"/": document_page(nav_items=12)})
    page.goto(server.url("/"))
    count = page.evaluate("document.querySelectorAll('.sb-nav-item').length")
    reached = page.evaluate(
        "(() => {const rail = document.querySelector('.sb-body-l');"
        " let seen = 0;"
        " for (const a of document.querySelectorAll('.sb-nav-item')) {"
        "   a.focus();"
        "   if (document.activeElement === a) seen++;"
        " }"
        " return seen})()"
    )
    assert reached == count


def test_a_clipped_viewport_root_traps_content_the_diagnostic_reports(
    page: Page, site: Serve
) -> None:
    """The defect the whole-tree diagnostic exists for, shown to be real.

    Content past the fold inside a fully clipped chain is unreachable: nothing
    scrolls, and `clip` creates no scroll container for the user agent to move
    even when a descendant is focused.
    """
    server = site({"/": clipped_page()})
    page.goto(server.url("/"))
    assert not page.evaluate(
        "document.documentElement.scrollHeight > document.documentElement.clientHeight"
    )
    trapped = page.evaluate(
        "(() => {const el = document.querySelector('.sb-trapped');"
        " return el.scrollHeight > el.clientHeight && el.scrollTop === 0})()"
    )
    assert trapped
    # Programmatic scrolling cannot rescue it either: a clip box is not a
    # scroll container, so the write is a no-op rather than a hidden scroll.
    page.evaluate("document.querySelector('.sb-trapped').scrollTop = 500")
    assert page.evaluate("document.querySelector('.sb-trapped').scrollTop") == 0


def test_leaving_mid_restore_does_not_overwrite_the_stored_offset(
    page: Page, site: Serve
) -> None:
    """A navigation during restoration must not persist the un-restored position.

    The failure this guards is a two-step one, which is what makes it hard to
    attribute: leaving page B before its rail finishes restoring saves B's rail
    at zero over a perfectly good stored offset, and the reader loses their place
    on the navigation *after* the one they just made. The saving half therefore
    stands down while the restoring half is still working, which the two
    coordinate through a marker on the scroll owner.
    """
    server = site(site_routes())
    page.goto(server.url("/page-0"))
    page.evaluate("document.querySelector('.sb-body-l').scrollTop = 300")
    page.evaluate(
        "document.querySelector('.sb-body-l').dispatchEvent(new Event('scroll'))"
    )
    page.wait_for_function(
        "() => sessionStorage.getItem('sb-nav-scroll:fixture-nav') === '300'"
    )

    # Two hops in a row, each begun as soon as the URL changes, so the second
    # leaves while restoration is plausibly still in flight.
    page.click("a[href='/page-14']")
    page.wait_for_url("**/page-14")
    page.go_back()
    page.wait_for_url("**/page-0")

    assert (
        page.evaluate("sessionStorage.getItem('sb-nav-scroll:fixture-nav')") == "300"
    ), "a mid-restore navigation overwrote the reader's stored offset"


def test_a_reader_scrolling_during_load_is_not_dragged_back(
    page: Page, slow_site: Serve
) -> None:
    """Restoration stands down the moment the reader takes over.

    A reader who scrolls while the page is still arriving has said where they
    want to be. Continuing to re-apply a stored offset would drag them back,
    which is the same class of defect as the reset the feature exists to fix.

    The takeover is staged deterministically rather than with a timed gesture:
    waited until the rail has real scroll range (so a scroll means something),
    then a wheel event and a chosen position, then the rest of the document. A
    wall-clock gesture would sometimes land before the rail had any range, where
    scrolling is a no-op and the test would pass without exercising anything.
    """
    server = slow_site(site_routes())
    page.goto(server.url("/page-0"))
    page.evaluate("document.querySelector('.sb-body-l').scrollTop = 445")
    page.evaluate(
        "document.querySelector('.sb-body-l').dispatchEvent(new Event('scroll'))"
    )
    page.wait_for_function(
        "() => sessionStorage.getItem('sb-nav-scroll:fixture-nav') === '445'"
    )

    page.goto(server.url("/page-20"), wait_until="commit")
    page.wait_for_function(
        "() => {const r = document.querySelector('.sb-body-l');"
        " return r && r.scrollHeight - r.clientHeight > 100}"
    )
    page.evaluate("window.dispatchEvent(new WheelEvent('wheel'))")
    page.evaluate("document.querySelector('.sb-body-l').scrollTop = 60")
    page.wait_for_load_state("load")

    assert page.evaluate("document.querySelector('.sb-body-l').scrollTop") == 60, (
        "restoration overrode a reader who scrolled during load"
    )
