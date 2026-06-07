# Reference: the browser runtime

The runtime is `switchboard_ui/static/switchboard.js`: hand-written vanilla JavaScript with no dependencies and no build step. It scans the page for mount points and brings islands to life. It exposes one global, `window.switchboard`.

## `window.switchboard`

```javascript
window.switchboard = { bus: bus, register: register, boot: boot };
```

### `bus`

The topic-keyed publish/subscribe channel. It is the only shared-state layer.

```javascript
bus.publish(topic, detail)        // broadcast detail to every subscriber of topic
var off = bus.subscribe(topic, handler)   // handler(detail, topic); returns an unsubscribe function
off()                             // stop receiving
```

A topic is any string. `publish` to a topic with no subscribers is a no-op. The subscriber set is copied before dispatch, so a handler that subscribes or unsubscribes mid-dispatch cannot corrupt the in-flight delivery.

### `register`

```javascript
window.switchboard.register(name, mount)
```

Registers an adapter under `name`. `mount` is `mount(element, props, bus)` returning an optional `teardown`. Registering also mounts any matching mount points already in the DOM, so registration order does not matter.

### `boot`

```javascript
window.switchboard.boot()
```

Scans the document and mounts every registered island. It runs automatically: on `DOMContentLoaded` if the document is still loading, otherwise immediately. Call it manually only after injecting new mount points into the DOM.

### `debug`

```javascript
window.switchboard.debug()        // toggle the overlay
window.switchboard.debug(true)    // force on
window.switchboard.debug(false)   // force off
```

A dev-only diagnostic that injects an outline overlay over the frame tree: an `outline` on every frame and island (outline, not border, so it adds no size to the boxes it measures), plus an override that un-collapses empty cells so every region shows. Because the package ships zero visual style, this is how you see the structure without DevTools. It returns the resulting on/off state, and turning it off removes the injected `<style>`, leaving no trace.

Loading the page with `?debug` in the URL enables the overlay automatically, so the structure is visible in development without knowing the console call. A shipped URL will not carry the parameter, so production stays clean.

`debug` lives in a sibling module, `switchboard_ui/static/switchboard-debug.js`, which is standalone (it touches only the DOM and `window.switchboard`, never the bus or registry) and augments the global the runtime creates. `render_document` emits it right after the runtime in both delivery modes, so it is always present and dormant until called.

## The mount contract

```javascript
function mount(element, props, bus) {
  return function teardown() { /* cleanup */ };
}
```

`element` is the mount-point `<div>`, already sized by its region.

`props` is the parsed `data-props` object (an empty object if absent).

`bus` is the channel above.

The return value, if a function, is stored on the element as `__sbTeardown`.

## How an element is mounted

The runtime reads the descriptor attributes the Python renderer emitted:

`data-island` selects the adapter by name.

`data-props` is parsed as JSON into the `props` argument.

`data-pub` and `data-sub` are the declared topics. The runtime does not consume them to deliver messages; they are the static-analysis surface, recoverable from the HTML without executing anything.

An element is mounted at most once (tracked in a `WeakSet`). If no adapter is registered for its name yet, it is skipped and mounted by a later `register` call. An island with no adapter (such as pure server-rendered content) simply never mounts and keeps its `initial` HTML.

## Writing adapters

See [Write an island adapter](../how-to/write-an-island-adapter.md) for the practical guide.
