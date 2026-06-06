# How to serve rendered HTML

`render_shell` returns a `str` and imports no web-framework type, so integration is a one-liner at the edge of your application. This guide covers the common targets.

## Serve from a backend

The rendered string drops into any framework's HTML response.

```python
# Starlette / FastAPI
from starlette.responses import HTMLResponse
return HTMLResponse(render_shell(shell))

# Flask
return render_shell(shell)

# Django
from django.http import HttpResponse
return HttpResponse(render_shell(shell))
```

## Write a static file

With no server at all, write the document to disk.

```python
from pathlib import Path
Path("index.html").write_text(render_shell(shell))
```

## Print from a CLI

```python
print(render_shell(shell))
```

## Choose inline or linked delivery

The CSS and the JavaScript runtime reach the page in one of two modes, selected by the `runtime` argument.

**Inline** (the default) embeds both the stylesheet and the runtime in the document. The result is a single self-contained file that runs with no host.

```python
html = render_shell(shell, runtime="inline")
```

**Linked** references the two assets by URL, for a host to serve and cache.

```python
html = render_shell(shell, runtime="linked", asset_base="/static/")
```

This emits `<link rel="stylesheet" href="/static/shell.css">` and `<script src="/static/switchboard.js">`. Your server must serve those two files at `asset_base`.

Use inline for generated files, emails, and anything opened directly. Use linked when a host serves many pages and should cache the assets across them, or when a strict Content-Security-Policy forbids inline `<style>` and `<script>`.

## Serve the assets in linked mode

The two files ship as package data under `switchboard_ui/static/`. Locate them with the standard library, then serve that directory.

```python
from importlib.resources import files
static_dir = files("switchboard_ui") / "static"  # holds shell.css and switchboard.js
```

Mount it directly (Starlette / FastAPI):

```python
from importlib.resources import files
from starlette.staticfiles import StaticFiles

app.mount(
    "/static",
    StaticFiles(directory=str(files("switchboard_ui") / "static")),
    name="switchboard-static",
)
```

Or copy the files into your own asset pipeline at build time:

```python
import shutil
from importlib.resources import files
shutil.copytree(files("switchboard_ui") / "static", "build/static", dirs_exist_ok=True)
```

Note on packaging: `files() / "..."` yields a real filesystem path for a normally-installed package, which is the common case. If the package is ever loaded from a zip, wrap reads in `importlib.resources.as_file()` to materialize a temporary path. Reading the bytes is always zip-safe; handing a directory path to a static-file server is not.

## Inject extra head markup and scripts

Two further arguments let you extend the document without touching the package.

`extra_head` is raw HTML inserted into `<head>` (meta tags, a favicon, your own stylesheet link).

`extra_scripts` is a sequence of script bodies inserted before `</body>`, used to register island adapters.

```python
html = render_shell(
    shell,
    extra_head='<link rel="icon" href="/favicon.ico">',
    extra_scripts=(counter_adapter_js, readout_adapter_js),
)
```

See the [Rendering reference](../reference/rendering.md) for the full signature.
