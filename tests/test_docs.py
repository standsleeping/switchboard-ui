"""The docs host renders the project's own docs through switchboard's own shell."""

from pathlib import Path

import pytest

from showcase import docs
from showcase.docs import DOCS_ROOT, build_doc, docs_scripts, docs_styles
from showcase.server import _docs_relpath
from switchboard_ui import render_document
from tests.htmlprobe import find


def test_build_doc_fills_the_three_columns_with_nav_breadcrumb_content_and_toc() -> (
    None
):
    """A rendered doc carries the nav, a breadcrumb over content, and an on-this-page TOC."""
    html = render_document(build_doc("tutorials/getting-started.md"))
    assert find(html, "div", **{"data-island": "nav"})
    assert find(html, "div", **{"data-island": "toc"})
    assert find(html, "div", **{"data-island": "breadcrumb"})
    assert find(
        html, "div", **{"data-island": "code-block"}
    )  # real, mountable code blocks
    assert find(html, "nav", **{"class": "sb-breadcrumb", "aria-label": "Breadcrumb"})


def test_nav_marks_the_current_doc() -> None:
    """Exactly the current doc's nav link carries aria-current, pointing at its route."""
    html = render_document(build_doc("tutorials/getting-started.md"))
    current = find(html, "a", **{"class": "sb-nav-item", "aria-current": "page"})
    assert [a["href"] for a in current] == ["/docs/tutorials/getting-started"]


def test_docs_page_carries_the_surface_switch_marking_docs() -> None:
    """The docs page shows the Gallery · Docs · Builder switch with Docs active."""
    html = render_document(build_doc("index.md"))
    active = find(html, "a", **{"class": "sb-switch-link", "aria-current": "page"})
    assert [a["href"] for a in active] == ["/docs"]


def test_every_doc_in_the_tree_renders_without_a_notice() -> None:
    """The whole Diátaxis tree renders through switchboard; no doc hits the boundary."""
    paths = sorted(DOCS_ROOT.rglob("*.md"))
    assert len(paths) >= 15
    for path in paths:
        relpath = str(path.relative_to(DOCS_ROOT))
        html = render_document(build_doc(relpath))
        assert "Not yet rendered" not in html, f"{relpath} hit the subset boundary"


def test_a_table_doc_renders_real_tables_with_working_cell_links() -> None:
    """index.md (entirely tables of links) renders real tables, links intact."""
    html = render_document(build_doc("index.md"))
    assert find(html, "table", **{"class": "sb-table-grid"})
    assert find(html, "a", href="/docs/tutorials/getting-started")  # a cell link works


def test_unsupported_construct_renders_a_notice_keeping_the_shell(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A construct outside the subset renders a navigable notice, not a 500."""
    (tmp_path / "note.md").write_text("# Note\n\n> a blockquote\n", encoding="utf-8")
    monkeypatch.setattr(docs, "DOCS_ROOT", tmp_path)
    html = render_document(docs.build_doc("note.md"))
    assert "Not yet rendered" in html
    assert "blockquote is not in the subset" in html
    assert find(html, "div", **{"data-island": "nav"})  # shell survives the notice


def test_docs_styles_carry_the_prose_chrome_and_table_css() -> None:
    """The docs paint their own prose, nav, TOC, and load the table component's CSS."""
    css = docs_styles()
    assert ".sb-body-c" in css  # the center column owns both column seams
    assert ".sb-doc-p" in css and ".sb-doc-code" in css  # prose styles
    assert ".sb-nav" in css and ".sb-toc" in css  # the shared nav/toc components' CSS
    assert ".sb-table-grid" in css  # the table component's structural CSS is loaded


def test_docs_scripts_include_the_code_block_copy_adapter() -> None:
    """The only behavior the docs need is the code block's copy action."""
    assert any("code-block" in script for script in docs_scripts())


def test_docs_route_resolves_index_and_nested_pages() -> None:
    """``/docs`` is the index; a nested URL maps to its doc path under ``docs/``."""
    assert _docs_relpath("/docs") == "index.md"
    assert (
        _docs_relpath("/docs/tutorials/getting-started")
        == "tutorials/getting-started.md"
    )


def test_docs_route_rejects_traversal_and_missing_pages() -> None:
    """An out-of-tree or non-existent URL resolves to None so the server can 404 it."""
    assert _docs_relpath("/docs/../server") is None
    assert _docs_relpath("/docs/tutorials/does-not-exist") is None
