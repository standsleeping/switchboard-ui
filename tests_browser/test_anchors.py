"""Real-browser regression tests for in-page anchor jumps.

Two facts about the same jump: it lands the heading below the scroll owner's
edge by the margin the theme declares, and under reduced motion it lands in
one step. The second is asserted behaviourally even though the layers never
declare smooth scrolling (the fast suites prove that absence), because the
claim the reader cares about is the composed page's, not each sheet's.
"""

from collections.abc import Callable

from playwright.sync_api import Page

from .conftest import Routes, Site
from .pages import anchor_page

Serve = Callable[[Routes], Site]


def test_an_anchor_jump_lands_the_heading_below_the_edge_by_its_margin(
    page: Page, site: Serve
) -> None:
    """The heading clears the edge by its declared scroll margin, not zero."""
    server = site({"/": anchor_page()})
    page.goto(server.url("/"))
    margin = page.evaluate(
        "parseFloat(getComputedStyle(document.getElementById('landing'))"
        ".scrollMarginBlockStart)"
    )
    assert margin > 0, "precondition: the theme must give the heading a scroll margin"

    page.click("a[href='#landing']")
    top = page.evaluate(
        "document.getElementById('landing').getBoundingClientRect().top"
    )
    assert abs(top - margin) <= 1, (
        f"the heading landed {top}px from the edge; its scroll margin is {margin}px"
    )


def test_a_reduced_motion_anchor_jump_is_instant(page: Page, site: Serve) -> None:
    """Under reduced motion the jump paints at most a start and an end.

    Sampled every painted frame: an animated jump leaves intermediate scroll
    positions behind, an instant one leaves none. The sheets add no smooth
    scrolling anywhere, so the reduction needs nothing to disable; this proves
    that absence survives composition.
    """
    server = site({"/": anchor_page()})
    page.emulate_media(reduced_motion="reduce")
    page.goto(server.url("/"))
    assert page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches"), (
        "precondition: the page must see the reduced-motion preference"
    )
    page.evaluate(
        "window.__pos = [];"
        "(function sample() {"
        "  requestAnimationFrame(() => {"
        "    window.__pos.push(Math.round(window.scrollY)); sample()});"
        "})()"
    )

    page.click("a[href='#landing']")
    page.wait_for_function("() => window.scrollY > 0")
    page.wait_for_timeout(200)

    samples = page.evaluate("window.__pos")
    start, end = samples[0], samples[-1]
    assert end > start, "precondition: the jump must have scrolled"
    # Instant means every painted frame sits at the start or at the landing;
    # a tween would leave frames strictly between them. A 1px tolerance
    # absorbs fractional scroll positions rounding differently across frames.
    between = [p for p in samples if abs(p - start) > 1 and abs(p - end) > 1]
    assert not between, f"the jump painted intermediate positions: {between}"
