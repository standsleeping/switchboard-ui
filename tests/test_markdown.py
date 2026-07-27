"""The markdown subset renderer covers what the docs use and fails loudly otherwise."""

import pytest

from showcase.markdown import (
    MarkdownError,
    internal_link_rewriter,
    render_markdown,
)
from tests.htmlprobe import find


def _body(source: str) -> str:
    """The concatenated initial HTML of a rendered doc's content islands."""
    return "".join(island.initial for island in render_markdown(source).content)


def test_first_h1_becomes_the_title() -> None:
    """The document title is the first level-1 heading's text."""
    assert render_markdown("# The page\n\nBody.").title == "The page"


def test_h2_and_h3_populate_the_toc_but_h1_does_not() -> None:
    """The on-this-page TOC is the H2/H3 headings; the H1 is the title, not a TOC entry."""
    rendered = render_markdown("# Title\n\n## Alpha\n\n### Beta\n\n## Gamma")
    assert [(h.level, h.text) for h in rendered.headings] == [
        (2, "Alpha"),
        (3, "Beta"),
        (2, "Gamma"),
    ]


def test_headings_carry_anchors_matching_their_toc_slugs() -> None:
    """Each heading renders an id equal to the slug the TOC links to."""
    rendered = render_markdown("# Title\n\n## What you build")
    heading = rendered.headings[0]
    assert heading.slug == "what-you-build"
    body = "".join(island.initial for island in rendered.content)
    assert find(body, "h2", id="what-you-build")


def test_repeated_heading_text_gets_a_disambiguated_slug() -> None:
    """Two headings with the same text get distinct ids, so anchors stay unique."""
    rendered = render_markdown("# T\n\n## Notes\n\n## Notes")
    assert [h.slug for h in rendered.headings] == ["notes", "notes-2"]


def test_toc_label_and_title_reduce_inline_markdown_to_plain_text() -> None:
    """A heading with inline code lists plainly in the TOC and title; the chip stays in content."""
    rendered = render_markdown("# `Island` model\n\n## The `Frame`")
    assert rendered.title == "Island model"  # title is plain, no backticks
    assert rendered.headings[0].text == "The Frame"  # TOC label is plain
    assert rendered.headings[0].slug == "the-frame"
    body = "".join(island.initial for island in rendered.content)
    assert '<code class="sb-doc-code">Frame</code>' in body  # content keeps the chip


def test_paragraph_inline_renders_bold_code_and_links() -> None:
    """Inline bold, code, and links each render to their semantic element."""
    body = _body("A **bold** word, `code`, and a [site](https://x.test).")
    assert "<strong>bold</strong>" in body
    assert '<code class="sb-doc-code">code</code>' in body
    assert find(body, "a", **{"class": "sb-doc-link", "href": "https://x.test"})


def test_code_span_protects_markup_from_inline_parsing() -> None:
    """Markup inside a code span is literal text, not re-parsed as markdown."""
    body = _body("Use `a**b**c` literally.")
    assert "<strong>" not in body
    assert '<code class="sb-doc-code">a**b**c</code>' in body


def test_emphasis_is_asterisks_only_so_snake_case_is_left_alone() -> None:
    """A single asterisk pair italicizes; underscores in identifiers do not."""
    body = _body("Set *this* but never extra_scripts_value.")
    assert "<em>this</em>" in body
    assert "<em>" in body and body.count("<em>") == 1
    assert "extra_scripts_value" in body


def test_literal_html_in_prose_is_escaped() -> None:
    """Stray angle brackets in prose are escaped, not emitted as live markup."""
    body = _body("Pass <script> to nobody.")
    assert "&lt;script&gt;" in body
    assert "<script>" not in body


def test_fenced_code_becomes_a_code_block_island_with_its_language() -> None:
    """A fence renders a real code-block island (so its copy action can mount)."""
    rendered = render_markdown("# T\n\n```python\nx = 1\n```")
    code = [island for island in rendered.content if island.name == "code-block"]
    assert len(code) == 1
    assert "python" in code[0].initial
    assert "x = 1" in code[0].initial


def test_fenced_code_body_is_opaque() -> None:
    """A line inside a fence is never interpreted as a heading or a table."""
    rendered = render_markdown(
        "# T\n\n```bash\n# not a heading\n| not | a table |\n```"
    )
    # The '#' line did not become a heading and the '|' line did not raise a table
    # error; both survive as escaped text inside the one code-block island.
    assert rendered.headings == ()
    code = next(island for island in rendered.content if island.name == "code-block")
    assert "# not a heading" in code.initial
    assert "| not | a table |" in code.initial


def test_lists_render_as_flex_columns_not_native_lists() -> None:
    """Ordered and unordered lists render as item columns, carrying no <ul>/<ol>."""
    body = _body("- one\n- two\n\n1. first\n2. second")
    assert find(body, "div", **{"class": "sb-doc-list", "role": "list"})
    assert body.count('class="sb-doc-item"') == 4
    assert "<ul" not in body and "<ol" not in body


def test_internal_md_link_is_rewritten_to_an_in_site_route() -> None:
    """A relative ``.md`` link resolves against the current doc to a ``/docs`` route."""
    rewrite = internal_link_rewriter("tutorials/getting-started.md")
    source = "See [arch](../explanation/architecture.md) and [home](../index.md)."
    body = "".join(
        island.initial for island in render_markdown(source, rewrite=rewrite).content
    )
    assert find(body, "a", href="/docs/explanation/architecture")
    assert find(body, "a", href="/docs")  # index.md maps to the docs root


def test_external_and_anchor_links_pass_through_rewriting() -> None:
    """Absolute URLs and in-page anchors are not rewritten."""
    rewrite = internal_link_rewriter("reference/cli.md")
    assert rewrite("https://x.test/a") == "https://x.test/a"
    assert rewrite("#section") == "#section"
    assert rewrite("/docs/other") == "/docs/other"


def test_internal_md_link_keeps_its_anchor_fragment() -> None:
    """A ``.md#anchor`` link rewrites the path to a route and preserves the fragment."""
    rewrite = internal_link_rewriter("reference/workbench.md")
    assert (
        rewrite("rendering.md#render_document")
        == "/docs/reference/rendering#render_document"
    )


def test_table_renders_through_the_table_component() -> None:
    """A GFM table becomes a `table` island: header → columns, body → rows."""
    rendered = render_markdown(
        "# T\n\n| Name | Role |\n| --- | --- |\n| accent | interactive |"
    )
    tables = [island for island in rendered.content if island.name == "table"]
    assert len(tables) == 1
    html = tables[0].initial
    assert len(find(html, "th", scope="col")) == 2
    assert "accent" in html and "interactive" in html


def test_table_cells_render_inline_links_and_code_not_escaped_source() -> None:
    """Inline markup in a body cell renders to elements, not literal markdown."""
    rewrite = internal_link_rewriter("index.md")
    source = "# T\n\n| Doc | Note |\n| --- | --- |\n| [G](getting.md) | `code` |"
    html = "".join(
        island.initial for island in render_markdown(source, rewrite=rewrite).content
    )
    assert find(html, "a", **{"class": "sb-doc-link", "href": "/docs/getting"})
    assert '<code class="sb-doc-code">code</code>' in html
    assert "[G]" not in html  # the raw link source did not leak into the cell


def test_table_pads_a_short_body_row_to_the_column_count() -> None:
    """A body row with fewer cells than the header is padded, not rejected."""
    rendered = render_markdown("# T\n\n| A | B | C |\n| - | - | - |\n| x |")
    html = next(island.initial for island in rendered.content if island.name == "table")
    assert len(find(html, "td")) == 3  # one filled cell plus two padded empties


def test_table_without_a_delimiter_row_is_rejected() -> None:
    """A pipe line not followed by a delimiter is not silently read as a table."""
    with pytest.raises(MarkdownError, match="missing its delimiter row"):
        render_markdown("# T\n\n| a | b |\nnot a delimiter row")


def test_blockquote_is_rejected() -> None:
    """A blockquote is outside the subset and fails loudly."""
    with pytest.raises(MarkdownError, match="blockquote is not in the subset"):
        render_markdown("# T\n\n> quoted")


def test_unterminated_fence_is_rejected() -> None:
    """A code fence with no closing fence fails loudly rather than swallowing the rest."""
    with pytest.raises(MarkdownError, match="unterminated code fence"):
        render_markdown("# T\n\n```python\nx = 1")


def test_thematic_break_is_rejected() -> None:
    """A `---` rule is outside the subset; it must not degrade to a paragraph."""
    with pytest.raises(MarkdownError, match="thematic break is not in the subset"):
        render_markdown("# T\n\n---")


def test_thematic_break_ends_a_paragraph_and_still_fails() -> None:
    """A rule directly under prose is seen and rejected, never swallowed by the paragraph."""
    with pytest.raises(MarkdownError, match="thematic break"):
        render_markdown("# T\n\nsome prose\n---\nmore prose")


def test_nested_list_item_is_rejected() -> None:
    """An indented list marker (a nested list) fails loudly instead of becoming prose."""
    with pytest.raises(MarkdownError, match="nested list item is not in the subset"):
        render_markdown("# T\n\n- top\n  - nested")


def test_fence_with_a_non_word_info_string_is_rejected() -> None:
    """A fence line the grammar cannot read must not leak its body as paragraphs."""
    with pytest.raises(MarkdownError, match="unsupported code fence"):
        render_markdown("# T\n\n```c++\nint x;\n```")


def test_indented_fence_is_rejected() -> None:
    """An indented fence is outside the subset and fails loudly."""
    with pytest.raises(MarkdownError, match="unsupported code fence"):
        render_markdown("# T\n\n  ```python\nx = 1\n```")


def test_image_is_rejected() -> None:
    """An image fails loudly wherever it appears; it must not render as `!` plus a link."""
    with pytest.raises(MarkdownError, match="image is not in the subset"):
        render_markdown("# T\n\nsee ![alt text](img.png) here")


def test_image_in_a_list_item_is_rejected() -> None:
    """The image check covers every inline run, not just paragraphs."""
    with pytest.raises(MarkdownError, match="image is not in the subset"):
        render_markdown("# T\n\n- an item with ![icon](i.png)")
