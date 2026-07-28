"""Real-browser regression tests for the packaged font's loading policy.

Font replacement is the symptom class that most easily impersonates a layout
defect: text is painted in a fallback, the real face arrives, and everything
reflows. A filmstrip of that looks exactly like a scroll or scrollbar bug, which
is why the two are guarded separately rather than argued about together.

The policy under test is ``font-display: optional``, whose whole claim is that it
*never* swaps after paint: a face that misses its short block period sits out that
page load entirely and is used from cache on the next one. Over localhost the face
always arrives inside the block period, so the interesting path — missing it —
only exists if the fixture stalls the font deliberately. That is what
:class:`~tests_browser.conftest.Asset`'s ``delay`` is for.
"""

from collections.abc import Callable

from playwright.sync_api import Page

from .conftest import Asset, Site
from .pages import font_bytes, font_page

Serve = Callable[..., Site]

FONT_URL = "/fonts/recursive.woff2"

# Sampled after each frame paints, then compared: a swap changes the measured
# advance width at some point after the first paint. Reading only at the end
# would prove the final state and nothing about how it got there.
_PROBE = """(() => new Promise(resolve => {
  const shifts = [];
  new PerformanceObserver(list => {
    for (const e of list.getEntries()) if (!e.hadRecentInput) shifts.push(e.value);
  }).observe({type: 'layout-shift', buffered: true});

  const widths = [];
  const measure = () => {
    const r = document.getElementById('font-ruler');
    // Sub-pixel: the face and the fallback differ by roughly a third of a
    // percent, so rounding to whole pixels would hide the very swap this looks
    // for. Two decimals is far finer than any real metric difference.
    if (r) widths.push(+r.getBoundingClientRect().width.toFixed(2));
  };
  (function sample() {
    requestAnimationFrame(() => { setTimeout(measure, 0); sample(); });
  })();

  const finish = () => setTimeout(() => resolve({
    cls: +shifts.reduce((a, b) => a + b, 0).toFixed(5),
    widths: [...new Set(widths)],
    usingPackaged: document.fonts.check('16px Recursive'),
  }), 1200);
  if (document.readyState === 'complete') finish();
  else addEventListener('load', finish);
}))()"""


def _serve(site: Serve, delay: float) -> Site:
    return site(
        {"/": font_page(font_src=FONT_URL)},
        {FONT_URL: Asset(font_bytes(), "font/woff2", delay=delay)},
    )


def test_a_late_face_never_replaces_painted_text(page: Page, site: Serve) -> None:
    """A face that misses its block period does not reflow the page.

    This is the path ``optional`` exists for and the one localhost cannot
    produce on its own. The font is stalled well past the block period, so the
    page paints in the fallback; the face must then sit out this load rather
    than swapping in and reflowing text the reader is already reading.
    """
    server = _serve(site, delay=1.0)
    page.goto(server.url("/"), wait_until="commit")
    result = page.evaluate(_PROBE)

    assert result["cls"] == 0, f"late face caused layout shift: {result}"
    assert len(result["widths"]) == 1, (
        f"text was re-set after first paint: widths {result['widths']}"
    )
    # The ruler is what makes this test capable of failing. Measured against the
    # same fixture with `font-display: swap`, the width goes 487.67 -> 486; with
    # `optional` it holds. Coarser signals do not discriminate: the two faces
    # differ by about a third of a percent in advance width, which is too little
    # to change a paragraph's line count, so paragraph height and cumulative
    # layout shift both read zero under `swap` as well.


def test_a_prompt_face_is_used_and_still_does_not_shift(
    page: Page, site: Serve
) -> None:
    """Arriving inside the block period, the face is used, and nothing moves.

    The other half of the policy: `optional` is not "never use the font". When
    the face is there in time it is used for the first paint, so there is
    nothing to replace.
    """
    server = _serve(site, delay=0.0)
    page.goto(server.url("/"), wait_until="commit")
    result = page.evaluate(_PROBE)

    assert result["usingPackaged"], "a prompt face was not used"
    assert result["cls"] == 0, f"prompt face caused layout shift: {result}"
    assert len(result["widths"]) == 1


def test_a_warm_cache_load_does_not_shift(page: Page, site: Serve) -> None:
    """The second visit uses the cached face without disturbing the first paint.

    The cold/warm pair is the case that makes font replacement look like a
    navigation bug: one page renders in the fallback, the next in the face, and
    the difference reads as the *navigation* having moved something. Neither
    load may shift on its own, which is what is asserted here; that the two
    differ slightly in metrics is a property of the two faces, measured
    separately, not a layout defect.
    """
    server = _serve(site, delay=1.0)
    page.goto(server.url("/"), wait_until="commit")
    page.evaluate(_PROBE)  # first visit; the face lands in the cache

    page.goto(server.url("/"), wait_until="commit")
    warm = page.evaluate(_PROBE)

    assert warm["cls"] == 0, f"warm load caused layout shift: {warm}"
    assert len(warm["widths"]) == 1


def test_the_face_is_preloaded_from_the_url_the_face_rule_names(
    page: Page, site: Serve
) -> None:
    """One fetch, started at head-parse rather than at first use.

    The preload exists to start the download before the ``@font-face`` is first
    matched against an element. It carries ``crossorigin`` because a font is
    always fetched in anonymous CORS mode; without it the preload and the real
    request are two separate fetches, which is worse than no preload at all.
    """
    server = _serve(site, delay=0.0)
    requests: list[str] = []
    page.on(
        "request",
        lambda r: requests.append(r.url) if r.resource_type == "font" else None,
    )
    page.goto(server.url("/"))
    page.wait_for_load_state("load")

    assert requests, "the face was never fetched"
    assert len(requests) == 1, f"the face was fetched {len(requests)} times: {requests}"
