# switchboard-ui

Render server-side HTML pages that host arbitrarily complex, self-contained interactive **islands**, wired together by a declarative event bus. Built with pure Python and zero runtime dependencies. The output is a string, so any backend can serve it.

Beyond the mechanism, it ships an optional theme and a small set of interactive components with every visual value exposed as a `--sb-*` token: switchboard is a toolkit for building any design system, not an opinionated design system of its own.

## Installation

```bash
uv sync --all-groups
```

## Usage

The `workbench` preset places islands into a nine-region viewport-locked layout and returns a `Document` you render to HTML. Its sibling `document_site` builds the flowing shape a reader reads.

```python
from switchboard_ui import Island, render_document, workbench

page = workbench(
    {
        "body-l": (Island(name="nav"),),
        "body-c": (Island(name="app", props={"start": 0}, publishes=("count:changed",)),),
        "body-r": (Island(name="inspector", subscribes=("count:changed",)),),
    },
    title="My app",
)

html = render_document(page)  # a complete, self-contained <!doctype html> string
```

Each `Island` is a mount point a browser-side adapter fills; islands talk to each other over the event bus via the topics they declare (`publishes` / `subscribes`).

The presets show the layout primitives: a `Frame` is a recursive flex stack, a `Document` wraps one as a page, and `render_document` renders any layout you build by hand. See [the workbench preset](docs/reference/workbench.md), [the document-site preset](docs/reference/document-site.md), and [page model](docs/reference/page-model.md).

## Documentation

Full documentation lives in [`docs/`](docs/index.md):

**Tutorials**

- [Getting started](docs/tutorials/getting-started.md)

**How-to guides**

- [Serve rendered HTML](docs/how-to/serve-rendered-html.md)
- [Write an island adapter](docs/how-to/write-an-island-adapter.md)
- [Render the demo and docs](docs/how-to/render-demo-and-docs.md)

**Reference**

- [Page model](docs/reference/page-model.md)
- [Components](docs/reference/components.md)
- [Rendering](docs/reference/rendering.md)
- [The document-site preset](docs/reference/document-site.md)
- [The workbench preset](docs/reference/workbench.md)
- [Theme tokens](docs/reference/tokens.md)
- [The browser runtime](docs/reference/browser-runtime.md)
- [The wiring analyzer](docs/reference/analyzer.md)
- [The CLI](docs/reference/cli.md)
- [Glossary](docs/reference/glossary.md)

**Explanation**

- [Architecture](docs/explanation/architecture.md)
- [Backend independence](docs/explanation/backend-independence.md)
- [Layout](docs/explanation/layout.md)
- [Ownership](docs/explanation/ownership.md)
- [Seams](docs/explanation/seams.md)

## Examples

Runnable examples live in [`examples/`](examples/README.md):

- [Vanilla DOM](examples/vanilla/README.md).
- [Web Components](examples/web-components/README.md).
- [React](examples/react/README.md).

## Development

```bash
just check          # lint, format check, type check, tests (what CI runs)
just format         # apply formatting
just typecheck-ty   # supplementary type check with ty
```
