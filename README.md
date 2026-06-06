# switchboard-ui

Render server-side HTML pages that host arbitrarily complex, self-contained interactive **islands**, wired together by a declarative event bus. Pure Python, zero runtime dependencies; the output is a string, so any backend (or none) can serve it.

## Installation

```bash
uv sync --all-groups
```

## Usage

`three_column` is a preset that places islands into a nine-region layout and returns a `Document` you render to HTML.

```python
from switchboard_ui import Island, render_document, three_column

page = three_column(
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

`three_column` is just a preset over the layout primitive: a `Frame` is a recursive flex stack, a `Document` wraps one as a page, and `render_document` renders any layout you build by hand. See [the three-column preset](docs/reference/three-column.md) and [page model](docs/reference/page-model.md).

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
- [Rendering](docs/reference/rendering.md)
- [The three-column preset](docs/reference/three-column.md)
- [The browser runtime](docs/reference/browser-runtime.md)
- [The CLI](docs/reference/cli.md)
- [Glossary](docs/reference/glossary.md)

**Explanation**

- [Architecture](docs/explanation/architecture.md)
- [Backend independence](docs/explanation/backend-independence.md)
- [Layout](docs/explanation/layout.md)
- [Design decisions](docs/explanation/design-decisions.md)

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
