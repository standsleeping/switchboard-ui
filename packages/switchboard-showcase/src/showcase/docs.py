"""Render the project's own ``docs/`` through switchboard-ui itself.

The documentation site is built with the library it documents: each doc's
markdown is rendered by the in-repo subset renderer (:mod:`showcase.markdown`)
into switchboard structure, then placed into the same ``three_column`` preset the
gallery uses, its columns used for what they mean:

- **Nav (body-l)** — the Diátaxis tree (Tutorials / How-to / Reference /
  Explanation), the current page marked. The gallery's nav pattern reused.
- **Content (body-c)** — a ``breadcrumb`` of the doc's path over the rendered doc.
- **On-this-page (body-r)** — the doc's H2/H3 headings as anchor links, the
  structural twin of the gallery inspector.

A doc whose markdown uses a construct outside the renderer's subset does not 500
the dev server; the renderer raises loudly, the host catches it, and the page
renders a notice naming the construct, so the tree stays navigable while the
subset boundary stays visible. The whole doc tree renders today (headings,
prose, code, lists, and tables cover it); the notice remains the surface for any
construct a future doc introduces before the renderer gains it.
"""

from dataclasses import dataclass
from pathlib import Path

from showcase.chrome import surface_switch, surface_switch_styles
from showcase.markdown import (
    Heading,
    MarkdownError,
    RenderedDoc,
    internal_link_rewriter,
    render_markdown,
)
from switchboard_ui import Document, Island
from switchboard_ui.components import (
    breadcrumb,
    breadcrumb_styles,
    code_block_scripts,
    code_block_styles,
    table_styles,
)
from switchboard_ui.html import element, escape_text
from switchboard_ui.model import Region
from switchboard_ui.presets import three_column

REPO_ROOT = Path(__file__).resolve().parents[4]
DOCS_ROOT = REPO_ROOT / "docs"

# The Diátaxis categories, in the order index.md introduces them. A directory name
# maps to the display label the nav and breadcrumb show.
_CATEGORIES: tuple[tuple[str, str], ...] = (
    ("tutorials", "Tutorials"),
    ("how-to", "How-to"),
    ("reference", "Reference"),
    ("explanation", "Explanation"),
)


def _doc_route(relpath: str) -> str:
    """The in-site route for a doc path under ``docs/`` (``index.md`` is the root)."""
    if relpath == "index.md":
        return "/docs"
    return f"/docs/{relpath[:-3]}"


def _doc_title(path: Path) -> str:
    """A doc's first ``# `` heading, the nav label (humanized stem as a fallback)."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("-", " ").capitalize()


@dataclass(frozen=True)
class _Entry:
    """One doc in the nav: its label, in-site route, and path-under-docs."""

    label: str
    route: str
    relpath: str


def _tree() -> list[tuple[str, list[_Entry]]]:
    """The Diátaxis nav tree: each category label paired with its doc entries.

    Built from the filesystem so a new ``.md`` appears in the nav the moment it
    lands; entries within a category are ordered by their title.
    """
    groups: list[tuple[str, list[_Entry]]] = []
    for directory, label in _CATEGORIES:
        entries: list[_Entry] = []
        category_dir = DOCS_ROOT / directory
        for path in sorted(category_dir.glob("*.md")):
            relpath = f"{directory}/{path.name}"
            entries.append(_Entry(_doc_title(path), _doc_route(relpath), relpath))
        entries.sort(key=lambda entry: entry.label)
        if entries:
            groups.append((label, entries))
    return groups


def _category_of(relpath: str) -> tuple[str, str] | None:
    """The ``(directory, label)`` a doc belongs to (``None`` for the index)."""
    directory = relpath.split("/", 1)[0]
    for name, label in _CATEGORIES:
        if name == directory:
            return name, label
    return None


def _nav(current: str) -> Island:
    """The nav column: an Overview link over the Diátaxis groups, current marked.

    A static island (no adapter): the links navigate natively to ``/docs`` routes.
    """
    items: list[str] = [
        element(
            "a",
            {
                "class": "sb-docs-nav-item",
                "href": "/docs",
                "aria-current": "page" if current == "index.md" else "false",
            },
            [escape_text("Overview")],
        )
    ]
    for label, entries in _tree():
        items.append(
            element("div", {"class": "sb-docs-nav-group"}, [escape_text(label)])
        )
        for entry in entries:
            items.append(
                element(
                    "a",
                    {
                        "class": "sb-docs-nav-item",
                        "href": entry.route,
                        "aria-current": "page" if entry.relpath == current else "false",
                    },
                    [escape_text(entry.label)],
                )
            )
    nav = element("nav", {"class": "sb-docs-nav", "aria-label": "Documentation"}, items)
    return Island(name="docs-nav", initial=nav)


def _toc(headings: tuple[Heading, ...]) -> Island:
    """The on-this-page column: the doc's H2/H3 headings as anchor links.

    A static island: each link is an in-page anchor to the heading's id. H3s are
    grouped into a sublist that owns the nesting indent structurally, so the links
    themselves keep a square inset rather than an asymmetric left padding.
    """

    def link(heading: Heading) -> str:
        return element(
            "a",
            {
                "class": f"sb-docs-toc-link sb-docs-toc-l{heading.level}",
                "href": f"#{heading.slug}",
            },
            [escape_text(heading.text)],
        )

    rows: list[str] = []
    sublist: list[str] = []

    def flush_sublist() -> None:
        if sublist:
            rows.append(element("div", {"class": "sb-docs-toc-sublist"}, list(sublist)))
            sublist.clear()

    for heading in headings:
        if heading.level >= 3:
            sublist.append(link(heading))
        else:
            flush_sublist()
            rows.append(link(heading))
    flush_sublist()

    children = [
        element("div", {"class": "sb-docs-toc-label"}, [escape_text("On this page")]),
        element("div", {"class": "sb-docs-toc-links"}, rows),
    ]
    toc = element(
        "nav", {"class": "sb-docs-toc", "aria-label": "On this page"}, children
    )
    return Island(name="docs-toc", initial=toc)


def _breadcrumb(relpath: str, title: str) -> Island:
    """The doc's path crumb: Docs / Category / Page, the category linking to its first doc."""
    trail: list[tuple[str, str]] = [("Docs", "/docs")]
    category = _category_of(relpath)
    if category is not None:
        _, label = category
        for group_label, entries in _tree():
            if group_label == label and entries:
                trail.append((label, entries[0].route))
                break
    return breadcrumb(trail=tuple(trail), current=title)


def _shell(
    *,
    relpath: str,
    title: str,
    headings: tuple[Heading, ...],
    content: tuple[Island, ...],
) -> Document:
    """Assemble the docs three-column shell around a doc's rendered content."""
    body_c = (_breadcrumb(relpath, title), *content)
    regions: dict[Region, tuple[Island, ...]] = {
        "head-c": (surface_switch("docs"),),
        "body-l": (_nav(relpath),),
        "body-c": body_c,
        "body-r": (_toc(headings),),
        "foot-c": (Island(name="status", initial="documentation"),),
    }
    return three_column(
        regions, title=f"{title} · switchboard-ui docs", right_width="16rem"
    )


def _notice(relpath: str, message: str) -> Island:
    """A flat callout naming the construct that keeps a doc out of the subset."""
    return Island(
        name="docs-notice",
        class_="sb-docs-notice",
        initial=element(
            "div",
            {"class": "sb-docs-notice-body"},
            [
                element(
                    "div",
                    {"class": "sb-docs-notice-title"},
                    [escape_text("Not yet rendered")],
                ),
                element(
                    "p",
                    {"class": "sb-doc-p"},
                    [
                        escape_text(
                            f"{relpath} uses a construct outside the renderer's subset: "
                            f"{message}. The renderer covers what the docs use and gains a "
                            "construct only when one is added deliberately."
                        )
                    ],
                ),
            ],
        ),
    )


def build_doc(relpath: str) -> Document:
    """Render the doc at ``relpath`` (under ``docs/``) into the docs shell.

    On a construct outside the subset the renderer raises ``MarkdownError``; the
    host catches it and renders a notice in the content column, so the nav and the
    rest of the shell stay intact and the unsupported doc is still reachable.
    """
    path = DOCS_ROOT / relpath
    source = path.read_text(encoding="utf-8")
    fallback_title = path.stem.replace("-", " ").capitalize()
    try:
        rendered: RenderedDoc = render_markdown(
            source, rewrite=internal_link_rewriter(relpath)
        )
    except MarkdownError as exc:
        return _shell(
            relpath=relpath,
            title=fallback_title,
            headings=(),
            content=(_notice(relpath, str(exc)),),
        )
    return _shell(
        relpath=relpath,
        title=rendered.title or fallback_title,
        headings=rendered.headings,
        content=rendered.content,
    )


def docs_scripts() -> tuple[str, ...]:
    """The adapters the docs register: the code block's copy action (nav is static)."""
    return code_block_scripts()


# The docs' own page chrome (host CSS, not the core's structure or the theme's
# paint): the content prose styles, the nav, the on-this-page TOC, and the header.
# It reads the theme's --sb-* tokens because the theme is loaded. The centre column
# owns both inline seams (single owner; the side columns draw neither). Content
# children share one reading measure so prose and code align to one column edge.
_DOC_MEASURE = "60rem"

_DOCS_CSS = f"""
.sb-body-c {{
  border-inline-start: var(--sb-border-width-thin) solid var(--sb-color-border);
  border-inline-end: var(--sb-border-width-thin) solid var(--sb-color-border);
  gap: var(--sb-space-lg);
  padding: var(--sb-space-xl);
}}
.sb-body-c > .sb-island {{
  inline-size: 100%;
  max-inline-size: {_DOC_MEASURE};
}}
.sb-doc {{
  display: flex;
  flex-direction: column;
  gap: var(--sb-space-md);
}}
.sb-doc-h {{
  font-family: var(--sb-font-family);
  font-weight: var(--sb-font-weight-bold);
  line-height: 1.2;
}}
.sb-doc-h1 {{ font-size: var(--sb-font-size-lg); }}
.sb-doc-h2 {{ font-size: var(--sb-font-size-base); }}
.sb-doc-h3 {{
  font-size: var(--sb-font-size-base);
  font-weight: var(--sb-font-weight-medium);
}}
.sb-doc-p {{
  font-family: var(--sb-font-family-prose);
  line-height: var(--sb-font-line-height);
  color: var(--sb-color-fg);
}}
.sb-doc-code {{
  font-family: var(--sb-font-family);
  font-size: var(--sb-font-size-sm);
  background: var(--sb-color-bg-raised);
  padding: var(--sb-space-2xs);
}}
.sb-doc-link {{
  color: var(--sb-color-accent);
  text-decoration: underline;
}}
.sb-doc-link:focus-visible {{
  outline: var(--sb-border-width-accent) solid var(--sb-color-accent);
  outline-offset: 2px;
}}
.sb-doc-list {{
  display: flex;
  flex-direction: column;
  gap: var(--sb-space-sm);
}}
.sb-doc-item {{
  display: flex;
  gap: var(--sb-space-sm);
  font-family: var(--sb-font-family-prose);
  line-height: var(--sb-font-line-height);
}}
.sb-doc-marker {{
  flex: 0 0 auto;
  min-inline-size: var(--sb-space-md);
  color: var(--sb-color-muted);
}}
.sb-docs-nav {{
  display: flex;
  flex-direction: column;
  gap: var(--sb-space-2xs);
  padding: var(--sb-space-md);
}}
.sb-docs-nav-group {{
  color: var(--sb-color-muted);
  font-weight: var(--sb-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--sb-font-tracking-wide);
  font-size: var(--sb-font-size-sm);
}}
.sb-docs-nav-item {{
  color: var(--sb-color-fg);
  text-decoration: none;
  border-inline-start: var(--sb-border-width-accent) solid transparent;
  padding: var(--sb-space-xs);
}}
.sb-docs-nav-item:hover {{
  color: var(--sb-color-accent);
}}
.sb-docs-nav-item[aria-current="page"] {{
  color: var(--sb-color-accent);
  border-inline-start-color: var(--sb-color-accent);
}}
.sb-docs-nav-item:focus-visible {{
  outline: var(--sb-border-width-accent) solid var(--sb-color-accent);
  outline-offset: -2px;
}}
.sb-docs-toc {{
  display: flex;
  flex-direction: column;
  gap: var(--sb-space-sm);
  padding: var(--sb-space-md);
}}
.sb-docs-toc-label {{
  color: var(--sb-color-muted);
  font-weight: var(--sb-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--sb-font-tracking-wide);
  font-size: var(--sb-font-size-sm);
  padding: var(--sb-space-2xs);
}}
.sb-docs-toc-links {{
  display: flex;
  flex-direction: column;
  gap: var(--sb-space-2xs);
}}
.sb-docs-toc-sublist {{
  display: flex;
  flex-direction: column;
  gap: var(--sb-space-2xs);
  padding-inline-start: var(--sb-space-md);
}}
.sb-docs-toc-link {{
  color: var(--sb-color-muted);
  text-decoration: none;
  font-size: var(--sb-font-size-sm);
  padding: var(--sb-space-2xs);
}}
.sb-docs-toc-link:hover {{
  color: var(--sb-color-accent);
}}
.sb-docs-notice {{
  border: var(--sb-border-width-thin) solid var(--sb-color-border);
}}
.sb-docs-notice-body {{
  display: flex;
  flex-direction: column;
  gap: var(--sb-space-sm);
  padding: var(--sb-space-lg);
}}
.sb-docs-notice-title {{
  font-weight: var(--sb-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--sb-font-tracking-wide);
  color: var(--sb-color-muted);
}}
"""


def docs_styles() -> str:
    """The components' structural CSS plus the docs' page chrome, for ``extra_head``."""
    sheets = "\n".join((code_block_styles(), breadcrumb_styles(), table_styles()))
    return f"<style>{sheets}</style><style>{_DOCS_CSS}</style>{surface_switch_styles()}"
