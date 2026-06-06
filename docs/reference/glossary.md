# Reference: glossary

| Term | Meaning |
|---|---|
| Island | A self-contained interactive mini-app mounted into one region of the page. |
| Descriptor | The declarative `Island` value: name, props, published and subscribed topics, and initial HTML. |
| Mount contract | `mount(element, props, bus)` returning `teardown`, the interface every adapter satisfies. |
| Adapter | The browser-side implementation of an island, registered by name. |
| Bus | The topic-keyed publish/subscribe channel islands coordinate through. |
| Topic | A string key on the bus, by convention `subject:event` (for example `count:changed`). |
| Frame | A recursive layout node: a one-dimensional flex stack (`row` or `column`, the `Direction`) of islands or nested frames. The general layout primitive. |
| Slot | A sized position in a frame: a child plus a fixed (`flex: 0 0 basis`) or flexible (`flex: 1 1 0`) main-axis size. |
| Shell | An example preset of `Frame`: the nine-region three-column page layout. |
| Document | A full page: a root layout frame plus a title; renders to a complete HTML document. |
| Region | One of the nine named cells of the shell (`head`/`body`/`foot` by `l`/`c`/`r`). |
| Chrome | The outer ring of regions (the top and bottom rails and the side rails) that frames the scrolling center. |
| Registry | The runtime's name-to-adapter map; dispatch is an explicit registry, not inheritance. |
| Inline / linked | The two modes for delivering the CSS and runtime (embedded in the document, or referenced by URL). |
| Hydration | Filling a server-rendered page with interactive islands after load, into boxes that already hold their final geometry. |
