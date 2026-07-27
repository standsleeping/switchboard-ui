# Rendering

The renderer is defined in `switchboard_ui.render`. It turns a `Document` into a complete HTML document string. It imports no web-framework type, so the output is independent of any backend.

## `render_document`

```python
def render_document(
    document: Document,
    *,
    runtime: RuntimeMode = "inline",
    asset_base: str = "",
    extra_head: str = "",
    extra_scripts: Sequence[str] = (),
) -> str
```

Renders a [`Document`](page-model.md#document) (a root layout frame plus a title) to a complete `<!doctype html>` page. The body frame becomes the viewport-locked page root. The document always includes a UTF-8 charset, a responsive viewport, and the escaped title.

| Parameter | Type | Default | Effect |
|---|---|---|---|
| `document` | `Document` | required | The page to render. |
| `runtime` | `RuntimeMode` | `"inline"` | How the CSS and JS reach the page (see below). |
| `asset_base` | `str` | `""` | URL prefix for the linked assets. Only used when `runtime="linked"`. |
| `extra_head` | `str` | `""` | Raw HTML inserted into `<head>`. |
| `extra_scripts` | `Sequence[str]` | `()` | Script bodies inserted before `</body>`, each wrapped in its own `<script>`. |

Build the `Document` by hand, or from [`document_site`](document-site.md) or [`workbench`](workbench.md).

```python
render_document(
    Document(body=Frame("row", (Island(name="nav"), Island(name="main"))))
)
```

## `RuntimeMode`

```python
RuntimeMode = Literal["inline", "linked"]
```

`"inline"` embeds the stylesheet in a `<style>` and the runtime (plus the debug overlay) in `<script>` elements, producing a self-contained document.

`"linked"` emits `<link rel="stylesheet" href="{asset_base}layout.css">`, `<script src="{asset_base}switchboard.js">`, and `<script src="{asset_base}switchboard-debug.js">`, which a host must serve at `asset_base`.

See [Serve rendered HTML](../how-to/serve-rendered-html.md) for choosing between them and serving the linked assets.

## `render_island`

```python
def render_island(island: Island) -> str
```

Renders one island as its mount-point `<div>`. Used internally by the renderer; exposed for rendering a single island in isolation (for tests or partial responses).

The `<div>` carries `class="sb-island"`, `data-island`, and the `data-props` / `data-pub` / `data-sub` attributes for any non-empty fields. Empty fields are omitted entirely. The island's `initial` HTML is placed inside.

```python
render_island(Island(name="counter", props={"start": 0}, publishes=("count:changed",)))
# <div class="sb-island" data-island="counter" data-props='{"start":0}' data-pub="count:changed"></div>
```

`data-props` is serialized with sorted keys and compact separators, so the output is stable across runs.

## `render_frame`

```python
def render_frame(frame: Frame) -> str
```

Renders a [`Frame`](page-model.md#frame) and its children recursively as nested flex `<div>`s. A frame becomes `<div class="sb-frame sb-frame-{direction}">`; each child is rendered in order (an island as its mount point, a nested frame recursively). A child wrapped in a [`Slot`](page-model.md#slot) carries a `flex` style for fixed or flexible sizing; a bare child is content-sized.

```python
render_frame(Frame(direction="row", children=(Island(name="a"), Island(name="b"))))
# <div class="sb-frame sb-frame-row"><div class="sb-island" data-island="a"></div><div class="sb-island" data-island="b"></div></div>
```

The [`document_site`](document-site.md) and [`workbench`](workbench.md) presets are two arrangements of frames built this way; you can build any other by hand.

## Escaping

The renderer escapes the title as character data and `asset_base` as an attribute value. Island `props` are JSON-encoded. Island `initial` content and `extra_head` / `extra_scripts` are treated as trusted raw HTML and are not escaped; the caller is responsible for their safety.
