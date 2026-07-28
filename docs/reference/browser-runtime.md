# The browser runtime

The runtime is `switchboard_ui/static/switchboard.js`: hand-written vanilla JavaScript with no dependencies and no build step. It scans the page for mount points and brings islands to life. It exposes one global, `window.switchboard`.

## `window.switchboard`

```javascript
window.switchboard = { bus: bus, register: register, boot: boot, unmount: unmount };
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

### `unmount`

```javascript
window.switchboard.unmount(root)
```

Unmounts every mounted island at or under `root` (the whole document if omitted). Each island's teardown runs — releasing its bus subscriptions and DOM listeners so a swapped-out island can never fire again — and the element is forgotten, so a later `boot` would mount it afresh. The inverse of `boot`, for a host that replaces a server-rendered island in place: `unmount(node)`, swap the HTML, `boot()`.

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

An element is mounted at most once (tracked in a `WeakSet`). If no adapter is registered for its name yet, it is skipped and mounted by a later `register` call. An island with no adapter (such as pure server-rendered content) never mounts and keeps its `initial` HTML.

## Writing adapters

See [Write an island adapter](../how-to/write-an-island-adapter.md) for the practical guide.

## Rail scroll persistence

A nav built with a `scroll_key` keeps its scroll position across native page loads. The boundary it addresses is the platform's: a forward navigation builds a new document, so an element scroll container starts at zero. The browser restores what it owns — the page's own position, and the whole DOM on a back/forward-cache traversal — but an element's scroll offset in a freshly built document is the application's to carry.

The work is split across two scripts, because only one half has a deadline.

**Placement** ships inline, immediately *before* the nav markup, and runs as the parser reaches it. It has to precede the paint of a complete rail: anything later paints the rail at the top and then corrects it, which the reader sees as a jump. Before the nav rather than after, because a document arrives in chunks and the parser can finish the nav, yield, and let the browser paint before reaching the next byte.

It does one of two things. With a stored offset it restores that offset exactly, re-applying each frame as the rail gains scroll range, since a rail still filling in cannot yet reach the target. With no stored offset — a deep link, a search result, a shared URL — it scrolls by the smallest amount that brings the current item into view, and leaves an already-visible item alone.

Either way it stands down the moment the reader takes over, on a wheel, touch, or key gesture, or on any scroll it did not cause itself.

**Saving** is an ordinary adapter (`nav_scripts()`), mounted with everything else. It writes the position on scroll (throttled to one write per frame), on link activation, and on `pagehide`. It holds off while placement is still in flight, which the two coordinate through a `data-sb-restoring` marker on the scroll owner: leaving a page mid-placement would otherwise persist a position the reader never chose over the one being restored.

Storage is `sessionStorage` under `sb-nav-scroll:<key>`, so the position is per-tab navigation continuity rather than a durable preference; two tabs scroll their rails independently and closing the tab forgets. Every access is guarded, since storage throws in a private or blocked context. A back/forward-cache traversal is left alone entirely: it reuses the live DOM, whose element scroll the browser has already restored.

Two boundaries worth knowing. The inline script needs `'unsafe-inline'` or a nonce under a strict Content-Security-Policy; the package emits no nonce, so a host with such a policy silently loses the enhancement and the rail simply starts at zero. And nothing is persisted for a nav without a `scroll_key` — the adapter mounts, finds no key, and returns.
