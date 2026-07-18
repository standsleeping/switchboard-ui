"""A showcase page draws each vertical seam on a full-height cell, never island content.

`switchboard-theme`'s `test_seams.py` proves single-ownership for the
`three_column` preset's region hooks. The showcase also hand-rolls layouts
directly on `Frame` (the theme builder's nav | controls | preview), whose seams
are the page's own chrome CSS and fall outside that guard. This is the parallel
guard for those pages.

A vertical column seam (a `border-inline-*`) must be drawn by a box the layout
stretches to the column's full height. A flex child of a row stretches by default;
content nested inside an `.sb-island` does not (the island is `display: block`, so
its block children size to their content). A seam placed on island content stops
where the content stops, leaving the lower part of the column unbordered. The
guard bans exactly that: no element carrying a vertical seam may sit inside an
island. The accent-channel reservation (a `transparent` inline-start border on a
nav row) is not a seam and is excluded by its color.
"""

import re
from collections.abc import Callable
from html.parser import HTMLParser

from showcase.build import (
    _BUILDER_CSS,
    _GALLERY_CSS,
    build_showcase,
    build_theme_builder,
)
from switchboard_ui import Document, render_document

# Logical and physical vertical-edge borders: the properties that draw a column
# seam between two side-by-side cells.
_VERTICAL_SEAM_PROPERTIES = frozenset(
    {
        "border-inline",
        "border-inline-start",
        "border-inline-end",
        "border-left",
        "border-right",
    }
)

# Elements with no end tag: never pushed onto the ancestry stack, so an island's
# scope unwinds correctly past them.
_VOID_TAGS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)


def _rules(css: str) -> list[tuple[str, str]]:
    """``(selector-list, body)`` for each rule block, comments stripped."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    return re.findall(r"([^{}]+)\{([^{}]*)\}", css)


def _subject_classes(selector: str) -> set[str]:
    """Class names in the rightmost compound selector (the rule's subject)."""
    last = re.split(r"\s*[>+~]\s*|\s+", selector.strip())[-1]
    return set(re.findall(r"\.([_a-zA-Z][\w-]*)", last))


def _draws_a_visible_vertical_seam(body: str) -> bool:
    """Whether a rule body sets a visible (non-transparent) vertical-edge border."""
    for decl in body.split(";"):
        name, sep, value = decl.partition(":")
        if not sep:
            continue
        if name.strip().lower() not in _VERTICAL_SEAM_PROPERTIES:
            continue
        value = value.strip().lower()
        if value in {"none", "0", "0px"} or "transparent" in value:
            continue
        return True
    return False


def _seam_classes(css: str) -> set[str]:
    """Classes whose rule draws a visible vertical seam."""
    classes: set[str] = set()
    for selectors, body in _rules(css):
        if not _draws_a_visible_vertical_seam(body):
            continue
        for selector in selectors.split(","):
            classes |= _subject_classes(selector)
    return classes


class _IslandDescendants(HTMLParser):
    """Collects the classes of every element nested inside an ``.sb-island``."""

    def __init__(self) -> None:
        super().__init__()
        self._stack: list[bool] = []  # per open element: is it inside an island?
        self.classes_inside_island: set[str] = set()

    @staticmethod
    def _classes(attrs: list[tuple[str, str | None]]) -> set[str]:
        for key, value in attrs:
            if key == "class":
                return set((value or "").split())
        return set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = self._classes(attrs)
        inside_island = bool(self._stack and self._stack[-1])
        if inside_island:
            self.classes_inside_island |= classes
        if tag in _VOID_TAGS:
            return
        self._stack.append(inside_island or "sb-island" in classes)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._stack and self._stack[-1]:
            self.classes_inside_island |= self._classes(attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag not in _VOID_TAGS and self._stack:
            self._stack.pop()


def _classes_inside_islands(html: str) -> set[str]:
    """Every class that appears on an element nested inside an ``.sb-island``."""
    parser = _IslandDescendants()
    parser.feed(html)
    return parser.classes_inside_island


# Each hand-rolled showcase page paired with the chrome CSS that draws its seams.
# Component CSS is excluded on purpose: a component's internal borders live inside
# its island legitimately and are not region seams.
_PAGES: tuple[tuple[str, Callable[[], Document], str], ...] = (
    ("theme builder", build_theme_builder, _BUILDER_CSS),
    ("gallery", build_showcase, _GALLERY_CSS),
)


def test_showcase_pages_draw_vertical_seams_on_full_height_cells_not_island_content() -> (
    None
):
    """No page-chrome vertical seam is bound to a class that renders inside an island.

    A seam on island content truncates at the content's height; this catches the
    theme builder's nav rail bordering its own <nav> (217px) instead of the
    full-height controls cell.
    """
    for name, build, css in _PAGES:
        seam_classes = _seam_classes(css)
        inside_island = _classes_inside_islands(render_document(build()))
        offenders = seam_classes & inside_island
        assert not offenders, (
            f"{name}: vertical seam(s) {sorted(offenders)} sit on island content, "
            "which does not stretch to the cell, so the seam truncates at the "
            "content's height; draw the seam on the full-height column cell instead"
        )
