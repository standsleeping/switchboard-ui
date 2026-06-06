# How to render the demo and docs

The package ships a command-line frontend that renders the bundled demo page to standard output. Because rendering needs no host, the package can produce its own static HTML and host the result anywhere.

## Render the demo

```bash
uv run switchboard-ui --runtime inline > demo.html
open demo.html
```

This renders a self-contained page with four islands. The `counter` button publishes `count:changed`; the `readout` in another region subscribes and updates live. The `brand` and `status` islands are pure server-rendered content with no adapter.

## Choose the delivery mode

```bash
uv run switchboard-ui --runtime inline > demo.html   # assets embedded, opens as a file
uv run switchboard-ui --runtime linked > demo.html   # assets referenced, needs a host
```

Inline is the default. For linked, serve the page next to the packaged assets; see [Serve rendered HTML](serve-rendered-html.md#serve-the-assets-in-linked-mode).

## Equivalent invocations

```bash
uv run python -m switchboard_ui --runtime inline > demo.html   # module entry shim
uv run switchboard-ui > demo.html                              # inline is the default
```

## Build static HTML without the CLI

The CLI is a thin wrapper over the public API. Anything it does, you can do in a few lines, which is the same path you would use to render your own pages or a documentation site.

```python
from pathlib import Path
from switchboard_ui.demo import build_demo, demo_scripts
from switchboard_ui.render import render_document

html = render_document(build_demo(), runtime="inline", extra_scripts=demo_scripts())
Path("demo.html").write_text(html)
```

`build_demo()` returns the demo `Document`.

`demo_scripts()` returns the two vanilla adapter sources.

To render a documentation site or storybook the same way, build your own pages (by hand or from a preset) and write each rendered string to its own file. The package renders its own output, so a guide, a component gallery, and a sandbox are all just documents rendered to static HTML.

See the [CLI reference](../reference/cli.md) for every flag.
