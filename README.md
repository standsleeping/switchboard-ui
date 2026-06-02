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

## Development

```bash
just check          # lint, format check, type check, tests (what CI runs)
just format         # apply formatting
just typecheck-ty   # supplementary type check with ty
```
