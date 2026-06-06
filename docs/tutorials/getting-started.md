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

## 2. Render an empty page

The simplest page comes from the `three_column` preset, which places islands into a nine-region layout and returns a `Document`. Rendering it produces a complete HTML document as a string.

```python
from switchboard_ui import render_document, three_column

html = render_document(three_column(title="My first page"))
print(html)
```

The output begins with `<!doctype html>` and contains the three-column structure. The cells are empty for now, and an empty cell collapses until an island fills it.

## 3. Place an island

An `Island` is a descriptor: a plain data value naming the adapter that will fill it. Put one in the center column.

```python
from switchboard_ui import Island, render_document, three_column

page = three_column(
    {"body-c": (Island(name="counter", props={"start": 0}),)},
    title="My first page",
)
html = render_document(page)
```

`name` is the adapter key the browser will look up.

`props` is JSON-serializable data handed to the adapter when it mounts.

The renderer turns this island into a `<div data-island="counter" data-props='{"start":0}'>`. Nothing interactive happens yet, because no adapter named `counter` has been registered.

## 4. Declare the wiring

The counter will announce a message; a readout will listen for it. You declare those topics on the descriptors, as data.

```python
page = three_column(
    {
        "body-c": (Island(name="counter", props={"start": 0}, publishes=("count:changed",)),),
        "body-r": (Island(name="readout", subscribes=("count:changed",)),),
    },
    title="My first page",
)
```

`publishes` lists the topics this island broadcasts onto the bus.

`subscribes` lists the topics this island listens for.

Because the wiring is declared as data, the connection from `counter` to `readout` is visible in the rendered HTML without running anything.

## 5. Write the two adapters

An adapter is browser code that registers under a name and receives the element, the props, and the bus. It returns a teardown function.

```javascript
window.switchboard.register("counter", function (el, props, bus) {
  var n = props.start || 0;
  var btn = document.createElement("button");
  function paint() { btn.textContent = "count: " + n; }
  paint();
  btn.addEventListener("click", function () {
    n += 1;
    paint();
    bus.publish("count:changed", n);
  });
  el.appendChild(btn);
  return function teardown() { btn.remove(); };
});

window.switchboard.register("readout", function (el, props, bus) {
  var out = document.createElement("div");
  out.textContent = "waiting for a click...";
  el.appendChild(out);
  var off = bus.subscribe("count:changed", function (n) {
    out.textContent = "latest count: " + n;
  });
  return function teardown() { off(); out.remove(); };
});
```

## 6. Ship the adapters with the page

Pass the adapter source to the renderer so it is included in the document.

```python
counter_js = "...the counter adapter from step 5..."
readout_js = "...the readout adapter from step 5..."

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
