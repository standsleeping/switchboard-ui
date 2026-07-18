# How to write an island adapter

An adapter is the browser-side implementation of an island. This guide shows how to write one, register it, and connect it to the page.

## The four parts of a component

An adapter is one of four parts that ship together to make a component. The full recipe:

1. **Factory.** A Python function returning an `Island` descriptor (in `components.py` for the bundled set). It server-renders the component's initial markup into `Island.initial`, so the component is present and correctly sized at first paint before any JavaScript runs, and it validates its inputs at the authoring boundary (raising `ValueError` on bad input). See the [page model reference](../reference/page-model.md).
2. **Adapter.** The browser-side `mount(element, props, bus) => teardown` that the rest of this guide covers. It enhances the server-rendered markup in place; it never rebuilds or resizes it.
3. **Structural CSS.** A per-component stylesheet (`static/<name>.css`) owning geometry only: token-free, `.sb-*` selectors only, the same contract as `layout.css`, with the test suite guarding every component sheet to that contract. See [Ownership](../explanation/ownership.md) and [Layout](../explanation/layout.md).
4. **Paint.** The component's appearance, added to the theme as `--sb-*` tokens and rules. Geometry stays stable across interactive state: reserve any state geometry (for example a transparent accent-width border) on the base rule and only recolor it in the state rule, so a `:hover` or `:focus` never reflows the box.

The split is by ownership: the factory owns markup, the adapter owns behavior, the structural CSS owns geometry, the theme owns paint. The host opts each part in, adapters through `extra_scripts` and structural CSS through `extra_head`. The rest of this guide covers part 2, the adapter.

## The mount contract

Every adapter is a function with this shape:

```javascript
function mount(element, props, bus) {
  // build UI inside element, wire up behavior
  return function teardown() {
    // release listeners and remove nodes
  };
}
```

`element` is the island's mount-point `<div>`, already sized by its region.

`props` is the parsed `data-props` object the Python descriptor carried.

`bus` is the event bus, with `publish(topic, detail)` and `subscribe(topic, handler)`.

The return value is a `teardown` function, or nothing if the island never needs cleanup.

## Register the adapter by name

Register against the runtime's global. The name must match the `name` on the Python `Island` descriptor.

```javascript
window.switchboard.register("clock", function (el, props, bus) {
  var out = document.createElement("time");
  el.appendChild(out);
  var id = setInterval(function () {
    out.textContent = new Date().toLocaleTimeString();
  }, 1000);
  return function teardown() {
    clearInterval(id);
    out.remove();
  };
});
```

Registration is order-independent. If the mount point is already in the DOM when you register, the runtime mounts it immediately; if you register first, it mounts as the element appears. See the [Browser runtime reference](../reference/browser-runtime.md) for the mount loop.

## Publish and subscribe

Islands coordinate by topic, never by direct reference.

```javascript
// a publisher
bus.publish("filter:changed", { query: "open" });

// a subscriber, in a different island
var off = bus.subscribe("filter:changed", function (detail) {
  render(detail.query);
});
// call off() in teardown to unsubscribe
```

A topic is just a string. The convention used by the bundled demo is `subject:event`, for example `count:changed`.

## Declare the wiring on the descriptor

For the connection to be visible to static analysis, declare each topic on the Python `Island`, not only in the adapter.

```python
Island(name="filter", publishes=("filter:changed",))
Island(name="results", subscribes=("filter:changed",))
```

These become `data-pub` and `data-sub` attributes on the mount points. The runtime does not require them to deliver messages; they are the declared, inspectable record of the wiring, and [the wiring analyzer](../reference/analyzer.md) recovers the pub/sub graph from them. Keep them in agreement with what the adapter actually publishes and subscribes to; a topic the analyzer reports as dangling is the first place to check for drift.

## Provide server-rendered initial content

An island can carry HTML that is present at first paint, before its adapter runs. Pass it as `initial`.

```python
Island(name="results", initial="<p>Loading results...</p>", subscribes=("filter:changed",))
```

`initial` is treated as trusted raw HTML and is placed inside the mount point. The adapter typically replaces it once it mounts.

## Ship the adapter

Pass the adapter source to the renderer through `extra_scripts`, or serve it as its own file and reference it from `extra_head`.

```python
html = render_document(page, extra_scripts=(clock_adapter_js,))
```

The bundled demo ships its two adapters as real files under `static/` and reads them with the package's asset reader; see `demo.py` for that pattern.

## Adapters need not be vanilla

The mount contract is the only requirement. A Web Component or a React component can satisfy `mount(element, props, bus) => teardown` just as a vanilla-DOM function does. The page, the descriptor, and the Python renderer never know which kind an island is. The vanilla form above is the one the package ships.
