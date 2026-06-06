# switchboard-ui

Render server-side HTML pages that host arbitrarily complex, self-contained interactive **islands**, wired together by a declarative event bus. Pure Python, zero runtime dependencies; the output is a string, so any backend (or none) can serve it.

## Installation

```bash
uv sync --all-groups
```

## Usage

`Shell` is one ready-made layout: place islands into its nine regions and render to HTML.

```python
from switchboard_ui import Island, Shell, render_shell

shell = Shell(
    title="My app",
    regions={
        "body-l": (Island(name="nav"),),
        "body-c": (Island(name="app", props={"start": 0}, publishes=("count:changed",)),),
        "body-r": (Island(name="inspector", subscribes=("count:changed",)),),
    },
)

html = render_shell(shell)  # a complete, self-contained <!doctype html> string
```

Each `Island` is a mount point a browser-side adapter fills; islands talk to each other over the event bus via the topics they declare (`publishes` / `subscribes`).

`Shell` is a preset over the lower-level `Frame`; `render_frame` renders an arbitrary `Frame`, so other layouts are possible. See [the shell layout](docs/reference/shell-layout.md) and [page model](docs/reference/page-model.md).

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
- [The shell layout](docs/reference/shell-layout.md)
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
