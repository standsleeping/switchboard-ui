# switchboard-ui

Render server-side HTML shells that host arbitrarily complex, self-contained interactive **islands**, wired together by a declarative event bus. Pure Python, zero runtime dependencies; the output is a string, so any backend (or none) can serve it.

## Features

- Python 3.14+
- Standard src-layout package structure
- Strict typing (mypy with `follow_imports = "error"`), `py.typed` shipped
- Linting and formatting with Ruff
- Testing with pytest at 100% coverage
- uv for dependency management and builds
- `just` task runner mirrored by CI

## Installation

```bash
uv sync --all-groups
```

## Usage

Place islands into the nine regions of the three-column shell and render to HTML:

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

Each `Island` is a mount point a browser-side adapter fills; islands talk to each
other over the event bus via the topics they declare (`publishes` / `subscribes`).

## Documentation

Full documentation lives in [`docs/`](docs/index.md), organized by the [Diátaxis](https://diataxis.fr/) framework:

- **Tutorials:** [Getting started](docs/tutorials/getting-started.md).
- **How-to guides:** [serve rendered HTML](docs/how-to/serve-rendered-html.md), [write an island adapter](docs/how-to/write-an-island-adapter.md), [render the demo and docs](docs/how-to/render-demo-and-docs.md).
- **Reference:** [page model](docs/reference/page-model.md), [rendering](docs/reference/rendering.md), [the shell layout](docs/reference/shell-layout.md), [the browser runtime](docs/reference/browser-runtime.md), [the CLI](docs/reference/cli.md), [glossary](docs/reference/glossary.md).
- **Explanation:** [architecture](docs/explanation/architecture.md), [backend independence](docs/explanation/backend-independence.md), [layout](docs/explanation/layout.md), [design decisions](docs/explanation/design-decisions.md).

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
