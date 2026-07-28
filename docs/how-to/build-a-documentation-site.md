# How to build a static documentation site

This guide builds a multi-page documentation site: a flowing shell, a nav generated from the filesystem, in-page anchors, and rendered output you can serve from anywhere. It is what this site itself does.

## 1. Choose the shape

Documentation is read, so use [`document_site`](../reference/document-site.md). The page scrolls, the rails stick.

```python
from switchboard_ui import Island, document_site, render_document

page = document_site(
    {
        "head-c": (Island(name="brand", initial="<b>My project</b>"),),
        "body-l": (site_nav,),
        "body-c": (*article,),
        "body-r": (on_this_page,),
        "foot-c": (Island(name="status", initial="docs"),),
    },
    title="Reference · My project",
)
html = render_document(page)
```

## 2. Generate the nav from the filesystem

Walk the source tree so a new page appears in the nav the moment it lands.

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Entry:
    """One page: its nav label, its route, and its path under the docs root."""
    label: str
    route: str
    relpath: str

def title_of(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("-", " ").capitalize()

def entries_in(directory: Path) -> list[Entry]:
    found = [
        Entry(title_of(p), f"/docs/{directory.name}/{p.stem}", f"{directory.name}/{p.name}")
        for p in sorted(directory.glob("*.md"))
    ]
    found.sort(key=lambda e: e.label)
    return found
```

### Nest by meaning, not by directory

[`NavItem.children`](../reference/components.md) nests to any depth. Resist deriving that nesting from the directory layout: a tree whose shape is the filesystem makes every file move a re-nesting, and directories rarely express the relationships a reader cares about.

Declare the hierarchy the content already asserts, keyed by path, and leave everything else flat:

```python
PARENT = {
    "reference/document-site.md": "reference/page-model.md",
    "reference/workbench.md": "reference/page-model.md",
}
```

Then fold a flat list into a tree, building children exactly the way parents are built so depth costs nothing extra:

```python
from switchboard_ui.components import NavItem, NavSection, nav

def nest(entries: list[Entry], current: str) -> tuple[NavItem, ...]:
    known = {e.relpath for e in entries}

    def build(entry):
        return NavItem(
            label=entry.label,
            href=entry.route,
            current=entry.relpath == current,
            children=tuple(
                build(c) for c in entries if PARENT.get(c.relpath) == entry.relpath
            ),
        )

    return tuple(build(e) for e in entries if PARENT.get(e.relpath) not in known)
```

An entry whose declared parent is missing stays top-level rather than disappearing, so a mistyped key degrades to a flat row instead of dropping a page out of the nav.

One section per category, and the pieces compose:

```python
sections = [
    NavSection(heading=heading, items=nest(entries_in(Path("docs") / name), current))
    for name, heading in (("tutorials", "Tutorials"), ("reference", "Reference"))
]
```

Exactly one item may be `current`; more raises. Ancestors of the current item get `data-current-ancestor` computed server-side, so the path to the current page is marked with no script and no reflow.

## 3. Keep the rail's place across pages

The nav is the same on every page, so give it a `scroll_key`:

```python
site_nav = nav(
    sections=tuple(sections),
    label="Documentation",
    scroll_key="docs-primary-nav",
)
```

Register the adapter alongside your others:

```python
from switchboard_ui.components import nav_scripts

html = render_document(page, extra_scripts=nav_scripts())
```

That is the whole of it. A reader who scrolls the rail and clicks a link finds the rail where they left it, and a reader arriving on a deep link finds the current page revealed. See [Scroll ownership and navigation state](../explanation/scroll-ownership.md).

If you serve under a strict Content-Security-Policy, note that this emits a small inline script; without `'unsafe-inline'` or a nonce it is blocked, and the rail simply starts at the top as it would have anyway.

## 4. Keep anchors native

Headings with `id` attributes are all an in-page table of contents needs. No scroll-management script; the browser follows the fragment.

Give anchor targets a `scroll-margin-block-start` in your content chrome so a heading does not land flush against the top of its scroll owner:

```css
.sb-body-c [id] {
  scroll-margin-block-start: 1rem;
}
```

## 5. Render every route to a file

`render_document` returns a string, so writing a static site is a loop:

```python
from pathlib import Path

out = Path("dist")
for relpath in every_doc():
    html = render_document(build_page(relpath))
    target = out / relpath.replace(".md", ".html")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")
```

For linked (rather than inlined) assets, render with `runtime="linked"` and an `asset_base`, then copy the package's static files to that path. See [Serve rendered HTML](serve-rendered-html.md).

## 6. Check what you built

Two checks catch most of what goes wrong, and both are cheap enough to run on every build.

Every internal link should resolve to a file that exists. A cross-reference to a page you renamed is invisible until a reader clicks it.

Every page should render without a fallback notice, if your renderer has a restricted subset like this one's.

## See also

- [The document-site preset](../reference/document-site.md)
- [Scroll ownership and navigation state](../explanation/scroll-ownership.md)
- [Components](../reference/components.md) — `nav`, `toc`, `breadcrumb`, `code_block`
- [Browser support](../reference/browser-support.md)
