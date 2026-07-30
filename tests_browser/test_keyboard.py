"""Real-browser regression tests for keyboard traversal of the rail.

Driven with trusted keyboard input rather than programmatic focus: the
contracts here are about what the keys themselves do — the order Tab visits
rows in, what the rail does to keep the visited row on screen, what Enter
means on a row, and what any keypress means to restoration. Programmatic
focus reaches the same elements without exercising any of that, which is why
the fast suite's reachability case is not a substitute for these.
"""

from collections.abc import Callable

from playwright.sync_api import Page

from .conftest import Routes, Site
from .pages import document_page, nested_nav_page, site_routes, workbench_page

Serve = Callable[[Routes], Site]


def _tab_key(browser_name: str) -> str:
    """The key that walks links in this engine.

    WebKit keeps links out of the default Tab order, exactly as shipping Safari
    does; Option+Tab is how a Safari reader walks them. The other engines put
    links in the Tab order directly.
    """
    return "Alt+Tab" if browser_name == "webkit" else "Tab"


_FOCUSED_ROW = (
    "(() => {const a = document.activeElement;"
    " return a && a.classList && a.classList.contains('sb-nav-item')"
    "  ? a.textContent.trim() : null})()"
)


def test_tab_visits_every_nav_row_in_document_order_at_every_depth(
    page: Page, site: Serve, browser_name: str
) -> None:
    """The Tab key walks the rail top to bottom, descending through nesting.

    The expected order is read from the document rather than restated, so the
    assertion is that traversal matches structure, whatever the structure is.
    The leaf labels double as the precondition: a grandchild row only exists in
    the document if nesting rendered it.
    """
    server = site({"/": nested_nav_page()})
    page.goto(server.url("/"))
    expected = page.evaluate(
        "[...document.querySelectorAll('.sb-nav-item')].map(a => a.textContent.trim())"
    )
    assert expected == ["Top 0", "Mid 0", "Leaf 0", "Leaf 1", "Mid 1", "Top 1"]

    visited = []
    for _ in range(len(expected) + 4):
        page.keyboard.press(_tab_key(browser_name))
        label = page.evaluate(_FOCUSED_ROW)
        if label is not None:
            visited.append(label)
        if len(visited) == len(expected):
            break
    assert visited == expected


def test_tabbing_through_a_scrolled_rail_keeps_every_focused_row_visible(
    page: Page, site: Serve, browser_name: str
) -> None:
    """Focus scrolls the rail as it walks; no row is skipped or left off screen.

    The rail overflows on purpose, so most rows start below its fold. Reaching
    them by Tab alone means the rail must scroll under focus, and every row the
    key lands on must be at least half inside the rail's visible box at that
    moment. Half, not whole: engines' focus-scroll policies differ on targets
    that are already peeking into view (one may leave a few pixels clipped),
    and the contract is that focus is never on a row the reader cannot see,
    not that every engine reveals every row completely.
    """
    server = site({"/": document_page(nav_items=40, current=0)})
    page.goto(server.url("/"))
    assert page.evaluate(
        "(() => {const r = document.querySelector('.sb-body-l');"
        " return r.scrollHeight > r.clientHeight})()"
    ), "precondition: the rail must overflow"

    states = []
    presses = 0
    # A press that leaves the label unchanged is focus parked in browser
    # chrome, which `document.activeElement` keeps reporting as the last row;
    # only a *changed* row is a traversal step. The press budget bounds the
    # loop if focus ever truly sticks, and the order assertion still fails on
    # any skipped or wrapped row.
    while len(states) < 40 and presses < 80:
        page.keyboard.press(_tab_key(browser_name))
        presses += 1
        state = page.evaluate(
            "(async () => {"
            " await new Promise(r => requestAnimationFrame(() => setTimeout(r, 0)));"
            " const a = document.activeElement;"
            " if (!a || !a.classList || !a.classList.contains('sb-nav-item'))"
            "   return null;"
            " const v = document.querySelector('.sb-body-l').getBoundingClientRect();"
            " const i = a.getBoundingClientRect();"
            " const shown = Math.min(i.bottom, v.bottom) - Math.max(i.top, v.top);"
            " return {label: a.textContent.trim(),"
            "  visible: shown >= (i.bottom - i.top) / 2}})()"
        )
        if state is None:
            continue
        if states and states[-1]["label"] == state["label"]:
            continue
        states.append(state)
    assert [s["label"] for s in states] == [f"Page {i}" for i in range(40)]
    hidden = [s["label"] for s in states if not s["visible"]]
    assert not hidden, f"focus landed outside the rail's visible box on: {hidden}"


def test_enter_on_a_focused_row_navigates_and_the_rail_position_survives(
    page: Page, site: Serve
) -> None:
    """Activating a row with Enter is a native navigation, continuity included.

    Focusing the row is staging; the keypress is the behaviour under test. The
    focused row is one that is already on screen at the stored offset, so
    focusing it moves nothing and the case measures the navigation, not its own
    setup.
    """
    server = site(site_routes())
    page.goto(server.url("/page-0"))
    page.evaluate(
        "const r = document.querySelector('.sb-body-l');"
        "r.scrollTop = 445; r.dispatchEvent(new Event('scroll'))"
    )
    page.wait_for_function(
        "() => sessionStorage.getItem('sb-nav-scroll:fixture-nav') === '445'"
    )
    page.evaluate("document.querySelector(\"a[href='/page-20']\").focus()")
    assert page.evaluate("document.querySelector('.sb-body-l').scrollTop") == 445, (
        "precondition: focusing an on-screen row must not move the rail"
    )

    page.keyboard.press("Enter")
    page.wait_for_url("**/page-20")
    page.wait_for_function(
        "() => document.querySelector('.sb-body-l').scrollTop === 445",
        timeout=3000,
    )


def test_tabbing_a_workbench_keeps_focus_inside_the_visible_cell(
    page: Page, site: Serve, browser_name: str
) -> None:
    """Focus never lands on a row the reader cannot see.

    The workbench's nav cell is a viewport-locked scroller, so its rows below
    the fold are reachable only if focus scrolls the cell. Every row Tab lands
    on must be at least half visible within the cell and the viewport at that
    moment; the half is the same engine allowance the rail case explains.
    """
    server = site({"/": workbench_page()})
    page.goto(server.url("/"))

    seen = 0
    for _ in range(60):
        page.keyboard.press(_tab_key(browser_name))
        state = page.evaluate(
            "(async () => {"
            " await new Promise(r => requestAnimationFrame(() => setTimeout(r, 0)));"
            " const a = document.activeElement;"
            " if (!a || !a.classList || !a.classList.contains('sb-nav-item'))"
            "   return null;"
            " const cell = a.closest('.sb-body-l').getBoundingClientRect();"
            " const i = a.getBoundingClientRect();"
            " const shown = Math.min(i.bottom, cell.bottom, innerHeight)"
            "  - Math.max(i.top, cell.top, 0);"
            " return shown >= (i.bottom - i.top) / 2})()"
        )
        if state is None:
            if seen:
                break
            continue
        assert state, f"row {seen} took focus while outside the visible cell"
        seen += 1
    assert seen == 40, f"only {seen} of 40 rows were reachable by Tab"


def test_a_reader_pressing_keys_during_load_is_not_dragged_back(
    page: Page, slow_site: Serve
) -> None:
    """A trusted keypress during load stands restoration down, like a wheel.

    The keyboard twin of the wheel takeover case: the adapter treats any of
    wheel, touch, or key input as the reader taking over, and this one arrives
    through the real keyboard rather than a constructed event.
    """
    server = slow_site(site_routes())
    page.goto(server.url("/page-0"))
    page.evaluate(
        "const r = document.querySelector('.sb-body-l');"
        "r.scrollTop = 445; r.dispatchEvent(new Event('scroll'))"
    )
    page.wait_for_function(
        "() => sessionStorage.getItem('sb-nav-scroll:fixture-nav') === '445'"
    )

    page.goto(server.url("/page-20"), wait_until="commit")
    page.wait_for_function(
        "() => {const r = document.querySelector('.sb-body-l');"
        " return r && r.scrollHeight - r.clientHeight > 100}"
    )
    page.keyboard.press("ArrowDown")
    page.evaluate("document.querySelector('.sb-body-l').scrollTop = 60")
    page.wait_for_load_state("load")

    assert page.evaluate("document.querySelector('.sb-body-l').scrollTop") == 60, (
        "restoration overrode a reader who pressed a key during load"
    )
