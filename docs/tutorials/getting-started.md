# Getting started

This tutorial builds a small interactive page from scratch. By the end you will have rendered an HTML document in which a button in one region updates a readout in another, with no build step and no framework.

## What you will build

A page with two interactive pieces. One is a counter button. The other is a readout that displays the latest count. They live in different parts of the page and never reference each other directly; they communicate by announcing and listening for a named message.

A few terms used throughout:

An **island** is a self-contained interactive mini-application that owns one box on the page.

A **region** is one of the nine named boxes the page is divided into.

The **bus** is a single channel islands use to broadcast and receive named messages.

An **adapter** is the browser-side code that brings an island to life: a function that you register under a name.

## 1. Install

```bash
uv sync --all-groups
```

## 2. Render a page

A page is a `Document`: a layout, and a statement about how that layout meets the viewport. Build one by hand first, so nothing is hidden.

```python
from switchboard_ui import Document, Frame, render_document

page = Document(
    body=Frame(direction="column"),
    root="flow",
    title="My first page",
)
html = render_document(page)
print(html)
```

The output begins with `<!doctype html>` and contains one empty flex stack.

`root="flow"` is the browser's normal document: the root is content-sized and the *page* scrolls, which is what an article does and what find-in-page, fragment anchors, and the back button all expect. The alternative is `root="viewport"`, which locks the root to the screen so the page never scrolls and each region scrolls on its own — an application shell rather than a document.

There is no default. The two are different kinds of page rather than one page with a setting, so every document says which it is.

## 3. Reach for a preset

Hand-built frames are the primitive; a preset is a ready-made arrangement of them, chosen by what the page *is*. `document_site` builds the flowing shape for an article or documentation. `workbench` builds the viewport-locked shape for a tool or dashboard, and names `root="viewport"` itself.

This tutorial builds a small interactive counter, so it uses `workbench`.

```python
from switchboard_ui import render_document, workbench

html = render_document(workbench(title="My first page"))
print(html)
```

Both presets place islands into the same nine-region layout. The cells are empty for now, and an empty cell collapses until an island fills it.

## 4. Place an island

An `Island` is a descriptor: a plain data value naming the adapter that will fill it. Put one in the center column.

```python
from switchboard_ui import Island, render_document, workbench

page = workbench(
    {
        "body-c": (
            Island(
                name="counter",
                props={"start": 0},
                initial='<button class="demo-btn">count: 0</button>',
            ),
        ),
    },
    title="My first page",
)
html = render_document(page)
```

`name` is the adapter key the browser will look up.

`props` is JSON-serializable data handed to the adapter when it mounts.

`initial` is server-rendered HTML placed inside the mount point. The button is already on the page at first paint, correctly sized, before any JavaScript runs; the adapter you write later will bring it to life rather than build it.

The renderer turns this island into a `<div data-island="counter" data-props='{"start":0}'>` holding the button. Nothing interactive happens yet, because no adapter named `counter` has been registered.

## 5. Declare the wiring

The counter will announce a message; a readout will listen for it. You declare those topics on the descriptors, as data.

```python
page = workbench(
    {
        "body-c": (
            Island(
                name="counter",
                props={"start": 0},
                publishes=("count:changed",),
                initial='<button class="demo-btn">count: 0</button>',
            ),
        ),
        "body-r": (
            Island(
                name="readout",
                subscribes=("count:changed",),
                initial='<div class="demo-readout">waiting for a click...</div>',
            ),
        ),
    },
    title="My first page",
)
```

`publishes` lists the topics this island broadcasts onto the bus.

`subscribes` lists the topics this island listens for.

Because the wiring is declared as data, the connection from `counter` to `readout` is visible in the rendered HTML without running anything.

## 6. Write the two adapters

An adapter is browser code that registers under a name and receives the element, the props, and the bus. It returns a teardown function.

The markup already arrived with the page (the `initial` HTML from step 4), so each adapter finds its element and enhances it in place. An adapter wires behavior; it never builds or resizes the markup.

```javascript
window.switchboard.register("counter", function (el, props, bus) {
  var n = props.start || 0;
  var btn = el.querySelector(".demo-btn");
  function onClick() {
    n += 1;
    btn.textContent = "count: " + n;
    bus.publish("count:changed", n);
  }
  btn.addEventListener("click", onClick);
  return function teardown() { btn.removeEventListener("click", onClick); };
});

window.switchboard.register("readout", function (el, props, bus) {
  var out = el.querySelector(".demo-readout");
  var off = bus.subscribe("count:changed", function (n) {
    out.textContent = "latest count: " + n;
  });
  return function teardown() { off(); };
});
```

## 7. Ship the adapters with the page

Pass the adapter source to the renderer so it is included in the document.

```python
counter_js = "...the counter adapter from step 6..."
readout_js = "...the readout adapter from step 6..."

html = render_document(page, extra_scripts=(counter_js, readout_js))
```

Write the result to a file and open it.

```python
from pathlib import Path
Path("page.html").write_text(html)
```

Click the button. The count rises, and the readout in the other column updates in step. The two islands never call each other; the counter publishes `count:changed`, the readout subscribes to it, and the bus connects them.

## A shortcut: the bundled demo

The package ships exactly this example. Render it with one command:

```bash
uv run switchboard-ui --runtime inline > demo.html
open demo.html
```

See [Render the demo and docs](../how-to/render-demo-and-docs.md) for what that command does.

## Next steps

- Understand the design: [Architecture](../explanation/architecture.md).
- Build your own islands: [Write an island adapter](../how-to/write-an-island-adapter.md).
- Look up the API: [Page model](../reference/page-model.md) and [Rendering](../reference/rendering.md).
