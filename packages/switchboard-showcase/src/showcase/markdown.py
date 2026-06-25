"""A dependency-free markdown *subset* renderer that emits switchboard structure.

This is not a markdown engine. It renders exactly the constructs the project's
own ``docs/`` use and raises :class:`MarkdownError` on anything it does not, so it
never grows into a general-purpose parser by accident. The docs are its spec: when
a doc needs a construct the renderer lacks, the renderer gains it as a deliberate
edit (the same anti-erosion discipline the token registry uses for categories).

The pipeline is two stages, parse then render, so structure is decided before any
HTML is emitted:

1. :func:`_blocks` tokenizes the source into a list of typed :class:`Block`
   values (heading, fenced code, list, paragraph). Fenced code is opaque — no
   line inside a fence is ever interpreted as markdown.
2. :func:`render_markdown` walks the blocks and emits switchboard markup: a fenced
   code block becomes a real ``code_block`` island (so its copy action mounts), and
   a run of prose blocks coalesces into one content island carrying anchored
   headings, paragraphs, and lists. Inline spans (bold, code, link) render through
   :func:`_render_inline`.

The result is a :class:`RenderedDoc`: the page title (the first H1), the H2/H3
headings for an on-this-page table of contents, and the ordered content islands a
host places into a layout region.
"""

import posixpath
import re
from collections.abc import Callable
from dataclasses import dataclass

from switchboard_ui import Island
from switchboard_ui.components import Cell, code_block, table
from switchboard_ui.html import element, escape_attr, escape_text

# A link rewriter maps a markdown href to the href the rendered site should use
# (e.g. an internal ``../foo.md`` to its in-site route). The identity is the
# default, so the renderer is usable without one.
LinkRewriter = Callable[[str], str]


class MarkdownError(ValueError):
    """A construct the subset does not cover, raised at the render boundary.

    Carries the 1-based source line so an unsupported construct fails where it is
    written, the way the component factories fail at their authoring boundary.
    """


# --- the block grammar -------------------------------------------------------

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_FENCE = re.compile(r"^```(\w*)\s*$")
_UNORDERED = re.compile(r"^[-*]\s+(.*)$")
_ORDERED = re.compile(r"^\d+\.\s+(.*)$")
# A GFM delimiter-row cell: dashes with optional alignment colons (``:--``, ``--:``).
_DELIM_CELL = re.compile(r"^:?-+:?$")


@dataclass(frozen=True)
class Heading:
    """One heading: its level, plain text (the TOC label), and anchor slug."""

    level: int
    text: str
    slug: str


@dataclass(frozen=True)
class CodeBlock:
    """A fenced code block: its info-string language (``""`` if none) and source."""

    language: str
    code: str


@dataclass(frozen=True)
class ListBlock:
    """A list: ``ordered`` picks the marker; ``items`` are the raw item texts."""

    ordered: bool
    items: tuple[str, ...]


@dataclass(frozen=True)
class TableBlock:
    """A table: a header row over body rows, cells holding raw inline source."""

    header: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class Paragraph:
    """A paragraph: soft-wrapped source lines joined into one inline run."""

    text: str


Block = Heading | CodeBlock | ListBlock | TableBlock | Paragraph


def _blocks(source: str) -> list[Block]:
    """Tokenize ``source`` into typed blocks, fences opaque, unsupported loud.

    Line-driven rather than blank-line-split, because a fenced code block may
    contain blank lines and its body must never be classified as markdown.
    """
    lines = source.splitlines()
    blocks: list[Block] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        fence = _FENCE.match(line)
        if fence is not None:
            i, block = _take_fence(lines, i, fence.group(1))
            blocks.append(block)
        elif not line.strip():
            i += 1
        elif (heading := _HEADING.match(line)) is not None:
            level = len(heading.group(1))
            blocks.append(Heading(level=level, text=heading.group(2).strip(), slug=""))
            i += 1
        elif _UNORDERED.match(line) or _ORDERED.match(line):
            i, block = _take_list(lines, i)
            blocks.append(block)
        elif line.lstrip().startswith("|"):
            i, block = _take_table(lines, i)
            blocks.append(block)
        elif line.lstrip().startswith(">"):
            raise MarkdownError(f"blockquote is not in the subset (line {i + 1})")
        else:
            i, block = _take_paragraph(lines, i)
            blocks.append(block)
    return blocks


def _take_fence(lines: list[str], start: int, language: str) -> tuple[int, CodeBlock]:
    """Consume a fenced block from its opening fence to its closing ```` ``` ````."""
    body: list[str] = []
    i = start + 1
    while i < len(lines) and not _FENCE.match(lines[i]):
        body.append(lines[i])
        i += 1
    if i >= len(lines):
        raise MarkdownError(f"unterminated code fence (line {start + 1})")
    return i + 1, CodeBlock(language=language, code="\n".join(body))


def _take_list(lines: list[str], start: int) -> tuple[int, ListBlock]:
    """Consume consecutive marker lines of one kind into a single list block.

    The first item's marker fixes the list kind; a marker of the other kind ends
    the list and begins a new block, so an ordered and an unordered list never
    merge.
    """
    ordered = _ORDERED.match(lines[start]) is not None
    pattern = _ORDERED if ordered else _UNORDERED
    items: list[str] = []
    i = start
    while i < len(lines) and (match := pattern.match(lines[i])) is not None:
        items.append(match.group(1).strip())
        i += 1
    return i, ListBlock(ordered=ordered, items=tuple(items))


def _split_row(line: str) -> tuple[str, ...]:
    """Split a ``| a | b |`` row into stripped cells (the outer pipes dropped)."""
    return tuple(cell.strip() for cell in line.strip().strip("|").split("|"))


def _take_table(lines: list[str], start: int) -> tuple[int, TableBlock]:
    """Consume a GFM table: a header row, a delimiter row, then body rows.

    The delimiter row (``| --- | --- |``) is required, as in GFM, so a stray
    pipe-prefixed line is not silently read as a one-row table; a header with no
    delimiter fails loudly. Body rows are padded or truncated to the header's
    column count, so a ragged row never reaches the ``table`` factory's rectangular
    check.
    """
    header = _split_row(lines[start])
    width = len(header)
    if start + 1 >= len(lines) or not all(
        _DELIM_CELL.match(cell) for cell in _split_row(lines[start + 1])
    ):
        raise MarkdownError(f"table is missing its delimiter row (line {start + 1})")
    rows: list[tuple[str, ...]] = []
    i = start + 2
    while i < len(lines) and lines[i].lstrip().startswith("|"):
        cells = _split_row(lines[i])
        padded = tuple((cells + ("",) * width)[:width])
        rows.append(padded)
        i += 1
    return i, TableBlock(header=header, rows=tuple(rows))


def _take_paragraph(lines: list[str], start: int) -> tuple[int, Paragraph]:
    """Consume soft-wrapped lines up to a blank line or the next block start."""
    body: list[str] = []
    i = start
    while i < len(lines):
        line = lines[i]
        if not line.strip() or _is_block_start(line):
            break
        body.append(line.strip())
        i += 1
    return i, Paragraph(text=" ".join(body))


def _is_block_start(line: str) -> bool:
    """Whether ``line`` opens a non-paragraph block (so a paragraph run stops)."""
    return bool(
        _HEADING.match(line)
        or _FENCE.match(line)
        or _UNORDERED.match(line)
        or _ORDERED.match(line)
        or line.lstrip().startswith(("|", ">"))
    )


# --- inline rendering --------------------------------------------------------
#
# Asterisk emphasis only: the docs write **bold** with asterisks, and underscore
# emphasis would mis-fire on snake_case identifiers that appear in prose. A code
# span is matched first and its body is escaped, never re-parsed, so markup inside
# backticks stays literal.
_INLINE = re.compile(
    r"(?P<code>`[^`]+`)"
    r"|(?P<strong>\*\*[^*]+\*\*)"
    r"|(?P<em>\*[^*]+\*)"
    r"|(?P<link>\[[^\]]+\]\([^)]+\))"
)
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _render_inline(text: str, rewrite: LinkRewriter) -> str:
    """Render inline markdown to HTML, escaping every literal run exactly once."""
    out: list[str] = []
    pos = 0
    for match in _INLINE.finditer(text):
        out.append(escape_text(text[pos : match.start()]))
        out.append(_render_inline_token(match, rewrite))
        pos = match.end()
    out.append(escape_text(text[pos:]))
    return "".join(out)


def _render_inline_token(match: re.Match[str], rewrite: LinkRewriter) -> str:
    """Render one matched inline span by its kind."""
    token = match.group()
    match match.lastgroup:
        case "code":
            return element("code", {"class": "sb-doc-code"}, [escape_text(token[1:-1])])
        case "strong":
            return element("strong", {}, [_render_inline(token[2:-2], rewrite)])
        case "em":
            return element("em", {}, [_render_inline(token[1:-1], rewrite)])
        case "link":
            link = _LINK.match(token)
            assert link is not None  # the alternation matched the same shape
            label, href = link.group(1), link.group(2)
            return (
                f'<a class="sb-doc-link" href="{escape_attr(rewrite(href))}">'
                f"{_render_inline(label, rewrite)}</a>"
            )
        case _:  # pragma: no cover — the alternation has no other groups
            raise MarkdownError(f"unhandled inline token {token!r}")


def _plain(text: str) -> str:
    """Reduce inline markdown to plain text: drop the markers, keep a link's label.

    The plain form names a heading in the TOC, the page title, and the slug, where
    a code chip or a link would be noise (a ``## `Island``` heading lists as
    ``Island``, not as `` `Island` `` with literal backticks).
    """
    out: list[str] = []
    pos = 0
    for match in _INLINE.finditer(text):
        out.append(text[pos : match.start()])
        token = match.group()
        match match.lastgroup:
            case "code":
                out.append(token[1:-1])
            case "strong":
                out.append(_plain(token[2:-2]))
            case "em":
                out.append(_plain(token[1:-1]))
            case "link":
                link = _LINK.match(token)
                assert link is not None
                out.append(_plain(link.group(1)))
        pos = match.end()
    out.append(text[pos:])
    return "".join(out)


# --- rendering blocks to switchboard markup ----------------------------------


def _slugger() -> Callable[[str], str]:
    """A slug maker that disambiguates repeats (``intro``, ``intro-2``, ...)."""
    seen: dict[str, int] = {}

    def slug(text: str) -> str:
        base = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "section"
        count = seen.get(base, 0)
        seen[base] = count + 1
        return base if count == 0 else f"{base}-{count + 1}"

    return slug


def _render_heading(block: Heading, slug: str, rewrite: LinkRewriter) -> str:
    """An anchored heading: a real ``<h{level}>`` whose id is the TOC target."""
    return element(
        f"h{block.level}",
        {"id": slug, "class": f"sb-doc-h sb-doc-h{block.level}"},
        [_render_inline(block.text, rewrite)],
    )


def _render_list(block: ListBlock, rewrite: LinkRewriter) -> str:
    """A list as a flex column of items (no ``<ul>``/``<ol>`` UA margin to fight).

    Each item carries its own marker (a number for an ordered list, a bullet for
    an unordered one) in an inert span, so the column reads as a list without the
    list element's default inset.
    """
    items: list[str] = []
    for index, text in enumerate(block.items, start=1):
        marker = f"{index}." if block.ordered else "•"
        items.append(
            element(
                "div",
                {"class": "sb-doc-item", "role": "listitem"},
                [
                    element(
                        "span",
                        {"class": "sb-doc-marker", "aria-hidden": "true"},
                        [marker],
                    ),
                    element(
                        "span",
                        {"class": "sb-doc-item-body"},
                        [_render_inline(text, rewrite)],
                    ),
                ],
            )
        )
    return element("div", {"class": "sb-doc-list", "role": "list"}, items)


def _render_table(block: TableBlock, section: str, rewrite: LinkRewriter) -> Island:
    """A table through the ``table`` component: plain headers, inline-rendered cells.

    The header cells stay plain text (the component escapes them); body cells carry
    inline markup (links, code), so each is a ``Cell`` of already-rendered HTML. The
    accessible name is the section the table sits under, falling back to ``Table``.
    """
    rows = [[Cell(_render_inline(cell, rewrite)) for cell in row] for row in block.rows]
    return table(columns=block.header, rows=rows, label=section or "Table")


@dataclass(frozen=True)
class RenderedDoc:
    """A rendered doc: its title, its TOC headings, and its content islands.

    ``content`` is the ordered island sequence a host drops into a region — prose
    runs as static islands, each fenced code block as a ``code_block`` island so
    its copy action mounts.
    """

    title: str
    headings: tuple[Heading, ...]
    content: tuple[Island, ...]


def render_markdown(
    source: str, *, rewrite: LinkRewriter = lambda href: href
) -> RenderedDoc:
    """Render a markdown-subset ``source`` into switchboard content.

    Coalesces consecutive prose blocks into one content island and flushes it
    before each ``code_block`` island, so the document renders as prose runs
    interleaved with interactive code blocks, in source order.
    """
    blocks = _blocks(source)
    slug = _slugger()
    headings: list[Heading] = []
    content: list[Island] = []
    prose: list[str] = []
    title = ""
    section = ""  # the most recent heading, the accessible name for a table

    def flush() -> None:
        if prose:
            content.append(
                Island(name="doc-prose", class_="sb-doc", initial="".join(prose))
            )
            prose.clear()

    for block in blocks:
        match block:
            case CodeBlock(language=language, code=code):
                flush()
                content.append(
                    code_block(
                        code=code,
                        label=f"{language or 'code'} sample",
                        language=language or None,
                    )
                )
            case Heading() as heading:
                plain = _plain(heading.text)
                anchor = slug(plain)
                section = plain  # the accessible name for any table under this heading
                if heading.level == 1 and not title:
                    title = plain
                elif heading.level in (2, 3):
                    headings.append(Heading(heading.level, plain, anchor))
                prose.append(_render_heading(heading, anchor, rewrite))
            case ListBlock() as list_block:
                prose.append(_render_list(list_block, rewrite))
            case TableBlock() as table_block:
                flush()
                content.append(_render_table(table_block, section, rewrite))
            case Paragraph(text=text):
                prose.append(
                    element("p", {"class": "sb-doc-p"}, [_render_inline(text, rewrite)])
                )
    flush()
    return RenderedDoc(title=title, headings=tuple(headings), content=tuple(content))


# --- internal-link rewriting -------------------------------------------------


def internal_link_rewriter(current_relpath: str) -> LinkRewriter:
    """A rewriter mapping a doc-relative ``.md`` link to its in-site ``/docs`` route.

    ``current_relpath`` is the current doc's path under ``docs/`` (e.g.
    ``tutorials/getting-started.md``); a relative link is resolved against its
    directory, the ``.md`` suffix dropped, and ``index`` mapped to the ``/docs``
    root. External URLs, in-page anchors, and absolute paths pass through.
    """
    base = posixpath.dirname(current_relpath)

    def rewrite(href: str) -> str:
        if "://" in href or href.startswith(("#", "/", "mailto:")):
            return href
        path, _, fragment = href.partition("#")
        if not path.endswith(".md"):
            return href
        route = posixpath.normpath(posixpath.join(base, path))[:-3]
        base_route = "/docs" if route == "index" else f"/docs/{route}"
        return f"{base_route}#{fragment}" if fragment else base_route

    return rewrite
