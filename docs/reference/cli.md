# Reference: the CLI

The package installs a console script, `switchboard-ui`, defined in `switchboard_ui.cli`. It renders the bundled demo page to standard output. It is the application layer: the one place that configures logging, done at runtime inside `main`.

## Usage

```bash
switchboard-ui [--runtime {inline,linked}] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
```

Under uv:

```bash
uv run switchboard-ui --runtime inline > demo.html
```

The module entry point is equivalent:

```bash
uv run python -m switchboard_ui --runtime inline > demo.html
```

## Options

| Flag | Choices | Default | Effect |
|---|---|---|---|
| `--runtime` | `inline`, `linked` | `inline` | Embed the CSS/JS (`inline`) or reference them (`linked`). |
| `--log-level` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` | `WARNING` | Root logger level. Logs go to standard error, so they never mix with the HTML on standard output. |

## Output

The command prints a complete HTML document to standard output and exits `0`. Redirect it to a file to save the page. The HTML is the only thing on standard output; diagnostics go to standard error.

```bash
switchboard-ui > demo.html        # HTML to the file, logs to the terminal
```

## What it renders

The demo page (`switchboard_ui.demo.build_demo`, a `Document`) with its two vanilla adapters (`switchboard_ui.demo.demo_scripts`). See [Render the demo and docs](../how-to/render-demo-and-docs.md) for building static HTML directly, without the CLI.
