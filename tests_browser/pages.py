"""Fixture pages built from the real package, not from hand-written HTML.

Every page here goes through the same ``document_site`` / ``workbench`` /
``nav`` the dogfood surfaces use, so a browser case exercises the shipped
assembly rather than a copy of it that can drift away from it silently.
"""

from switchboard_ui import (
    Island,
    document_site,
    render_document,
    workbench,
)
from switchboard_ui.components import NavItem, NavSection, nav, nav_scripts, nav_styles


def _paragraphs(count: int, marker: str = "para") -> Island:
    """A block of prose long enough to make the page scroll."""
    body = "".join(
        f'<p id="{marker}-{i}" style="line-height:1.6">'
        f"Paragraph {i}. " + ("Body text. " * 14) + "</p>"
        for i in range(count)
    )
    return Island(name="article", initial=body)


def _nav_island(current: int, count: int, scroll_key: str) -> Island:
    """A rail long enough to scroll, with one item marked current."""
    return nav(
        sections=(
            NavSection(
                heading="Pages",
                items=tuple(
                    NavItem(
                        label=f"Page {i}",
                        href=f"/page-{i}",
                        current=i == current,
                    )
                    for i in range(count)
                ),
            ),
        ),
        label="Fixture nav",
        scroll_key=scroll_key,
    )


def _head() -> str:
    return (
        "<style>"
        "body{font:16px/1.4 system-ui}"
        ".sb-body-l{background:#eee}"
        ".sb-nav-item{display:block;padding:8px}"
        "</style>" + f"<style>{nav_styles()}</style>"
    )


def document_page(
    *,
    current: int = 18,
    nav_items: int = 40,
    paragraphs: int = 40,
    scroll_key: str = "fixture-nav",
) -> str:
    """A flowing document site: page-scrolling article beside a sticky nav rail."""
    page = document_site(
        {
            "head-c": (Island(name="brand", initial="<b>Fixture</b>"),),
            "body-l": (_nav_island(current, nav_items, scroll_key),),
            "body-c": (_paragraphs(paragraphs),),
            "foot-c": (Island(name="status", initial="footer"),),
        },
        title=f"Page {current}",
    )
    return render_document(page, extra_head=_head(), extra_scripts=nav_scripts())


def workbench_page(*, paragraphs: int = 40) -> str:
    """A viewport-locked workbench: the body cells scroll, the page does not."""
    page = workbench(
        {
            "head-c": (Island(name="brand", initial="<b>Workbench</b>"),),
            "body-l": (_nav_island(0, 40, ""),),
            "body-c": (_paragraphs(paragraphs),),
            "foot-c": (Island(name="status", initial="footer"),),
        },
        title="Workbench",
    )
    return render_document(page, extra_head=_head())


def clipped_page() -> str:
    """A viewport root whose content is trapped behind a clipped frame.

    The tree is valid node by node; only the combination is the defect, which is
    what makes it a diagnostic rather than a type error.
    """
    from switchboard_ui.model import Document, Frame, Slot

    body = Frame(
        direction="column",
        overflow="clip",
        children=(
            Slot(
                Frame(
                    direction="column",
                    overflow="clip",
                    children=(_paragraphs(30, marker="trapped"),),
                    class_="sb-trapped",
                )
            ),
        ),
    )
    return render_document(
        Document(body=body, root="viewport", title="Clipped"),
        extra_head=_head(),
    )


def site_routes(*, pages: int = 40, nav_items: int = 40) -> dict[str, str]:
    """A multi-page site sharing one nav, for cross-navigation cases.

    Every nav target is served, so a case can click a link that is *already*
    visible at the scroll offset under test. That matters more than it sounds:
    the driver scrolls an element into view before clicking it, so clicking a
    row near the top of a scrolled rail moves the rail to zero first and the
    case then measures its own side effect rather than the product's behaviour.
    """
    return {
        f"/page-{i}": document_page(current=i, nav_items=nav_items)
        for i in range(pages)
    } | {"/": document_page(current=0, nav_items=nav_items)}
