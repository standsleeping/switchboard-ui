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
from switchboard_ui.components import (
    NavItem,
    NavSection,
    code_block,
    code_block_styles,
    nav,
    nav_scripts,
    nav_styles,
    prose,
    prose_styles,
)


def _paragraphs(count: int, marker: str = "para") -> Island:
    """A block of prose long enough to make the page scroll."""
    body = "".join(
        f'<p id="{marker}-{i}" style="line-height:1.6">'
        f"Paragraph {i}. " + ("Body text. " * 14) + "</p>"
        for i in range(count)
    )
    return Island(name="article", initial=body)


def font_bytes() -> bytes:
    """The packaged typeface, for a fixture to serve at whatever speed it likes."""
    from switchboard_theme import api as themes

    return themes.font_bytes()


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


def themed_document_page(*, paragraphs: int, nav_items: int) -> str:
    """A flowing document carrying the theme head, the way a shipped page does.

    The structural sheet can reserve an element scroller's gutter, but the
    viewport's own gutter can only be declared from the root element, and that
    declaration is the theme's. A case about page-bar geometry therefore needs
    the theme head present, or it exercises a configuration no shipped page has.
    """
    from switchboard_theme import api as themes

    page = document_site(
        {
            "head-c": (Island(name="brand", initial="<b>Fixture</b>"),),
            "body-l": (_nav_island(0, nav_items, ""),),
            "body-c": (_paragraphs(paragraphs),),
            "foot-c": (Island(name="status", initial="footer"),),
        },
        title="Themed",
    )
    return render_document(page, extra_head=themes.head("default") + _head())


def anchor_page(*, filler: int = 30) -> str:
    """A themed document whose prose carries an in-page link and its target.

    The theme gives prose headings a scroll margin, so an anchor jump must land
    the heading below the scroll owner's edge rather than flush against it. The
    target sits between two runs of filler: the run before it makes the jump a
    real scroll, and the run after it gives the page enough range below the
    target for the jump to actually reach the margin position.
    """
    from switchboard_theme import api as themes

    def _filler(count: int, marker: str) -> str:
        return "".join(
            f'<p id="{marker}-{i}">Filler {i}. ' + ("Body text. " * 14) + "</p>"
            for i in range(count)
        )

    body = (
        '<p><a href="#landing">Jump to the landing section</a></p>'
        + _filler(filler, "before")
        + '<h2 id="landing">Landing</h2>'
        + _filler(filler // 2, "after")
    )
    page = document_site({"body-c": (prose(html=body),)}, title="Anchors")
    return render_document(
        page, extra_head=themes.head("default") + f"<style>{prose_styles()}</style>"
    )


def nested_nav_page() -> str:
    """A document whose rail nests three levels deep, six rows in all.

    Small on purpose: every row has a name a keyboard case can list in full, so
    an assertion about traversal order reads as the order itself.
    """
    rail = nav(
        sections=(
            NavSection(
                heading="Pages",
                items=(
                    NavItem(
                        label="Top 0",
                        href="/t0",
                        children=(
                            NavItem(
                                label="Mid 0",
                                href="/m0",
                                children=(
                                    NavItem(label="Leaf 0", href="/l0"),
                                    NavItem(label="Leaf 1", href="/l1"),
                                ),
                            ),
                            NavItem(label="Mid 1", href="/m1"),
                        ),
                    ),
                    NavItem(label="Top 1", href="/t1", current=True),
                ),
            ),
        ),
        label="Fixture nav",
        scroll_key="",
    )
    page = document_site(
        {"body-l": (rail,), "body-c": (_paragraphs(5),)},
        title="Nested",
    )
    return render_document(page, extra_head=_head(), extra_scripts=nav_scripts())


def wide_code_page() -> str:
    """A document holding a code block far wider than any viewport under test.

    The block's contract is that long lines scroll inside it and never push the
    page; a single 240-term expression makes the line wider than a 1920px
    viewport, so the contract is exercised rather than assumed at every width.
    Carries the theme head because the two halves of the contract are split
    across the layers: structure owns the block's overflow, the theme owns the
    `white-space: pre` that makes a long line wide at all.
    """
    from switchboard_theme import api as themes

    wide = "value = " + " + ".join(f"column_{i}" for i in range(240))
    block = code_block(code=wide, label="A deliberately wide line", copy=False)
    page = document_site(
        {"body-c": (block, _paragraphs(6))},
        title="Wide code",
    )
    return render_document(
        page,
        extra_head=themes.head("default")
        + _head()
        + f"<style>{code_block_styles()}</style>",
    )


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


def font_page(*, font_src: str, paragraphs: int = 12) -> str:
    """A flowing document whose text is set in the packaged face.

    Uses the theme's own ``font_head``, so the case exercises the shipped
    ``@font-face`` — its preload hint and its ``font-display`` value — rather
    than a copy that could drift away from it.
    """
    from switchboard_theme import api as themes

    # A non-wrapping ruler. Paragraph height is far too coarse to detect a swap:
    # the packaged face and the fallback differ by a fraction of a percent in
    # advance width, which rarely changes a line count and so rarely changes a
    # height. An unwrapped run of text turns that fraction into pixels.
    ruler = Island(
        name="ruler",
        initial=(
            '<span id="font-ruler" style="white-space:pre">'
            "The quick brown fox jumps over the lazy dog 0123456789"
            "</span>"
        ),
    )
    page = document_site(
        {"body-c": (ruler, _paragraphs(paragraphs, marker="font"))},
        title="Font",
    )
    return render_document(
        page, extra_head=themes.head("default") + themes.font_head(font_src)
    )
