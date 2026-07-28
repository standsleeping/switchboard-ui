# Glossary

| Term | Meaning |
|---|---|
| Island | A self-contained interactive mini-app mounted into one region of the page. |
| Descriptor | The declarative `Island` value: name, props, published and subscribed topics, and initial HTML. |
| Mount contract | `mount(element, props, bus)` returning `teardown`, the interface every adapter satisfies. |
| Adapter | The browser-side implementation of an island, registered by name. |
| Bus | The topic-keyed publish/subscribe channel islands coordinate through. |
| Topic | A string key on the bus, by convention `subject:event` (for example `count:changed`). |
| Wiring | The declared pub/sub graph of a page: islands, per-topic edges, and dangling topics, recovered from rendered HTML by the analyzer (`switchboard_ui.analyze`). |
| Frame | A recursive layout node: a one-dimensional flex stack (`row` or `column`, the `Direction`) of islands or nested frames. The general layout primitive. |
| Slot | A sized position in a frame: a child plus a fixed (`flex: 0 0 basis`) or flexible (`flex: 1 1 0`) main-axis size. |
| Document | A full page: a root layout frame plus a title; renders to a complete HTML document. |
| Preset | A function that assembles islands into a `Frame` and returns a `Document`; `document_site` and `workbench` are the bundled ones. |
| Region | One of the nine placement names both presets accept (`head`/`body`/`foot` by `l`/`c`/`r`). |
| Root mode | Whether a `Document`'s root flows with the page or is locked to the viewport; a required field, never inferred. |
| Document site | The flowing page shape: the page is the primary scroll owner and side rails are sticky. Built by `document_site`. |
| Workbench | The viewport-locked page shape: the page never scrolls and named regions own their scroll. Built by `workbench`. |
| Overflow policy | A `Frame`'s declared answer for content that exceeds it: `visible`, `clip`, or `auto`. Every frame carries exactly one. |
| Scroll owner | The frame that scrolls its own overflow, i.e. one declaring `overflow="auto"`. In the flowing shape the page itself is the primary one. |
| Reset layer | The narrow set of user-agent defaults a structural sheet may clear (a body margin, a list's marker and indent), permitted at exactly the values that neutralize them. |
| Envelope | The generated `<body class="sb-document">`, named by the package so it can be reset without styling a host element. |
| Ownership | The rule that every spatial or visual decision has exactly one owning layer, so a theme is replaceable and a visual bug traces to one layer. See [Ownership](../explanation/ownership.md). |
| Seam | The border line between two tiled regions; drawn exactly once, by a single owner. See [Seams](../explanation/seams.md). |
| Geometry contract | The `--sb-fit-*` obligations: a themed component *requires* (intrinsic geometry projected from its causes), structure *grants* (a slot floored at the requirement). See [Ownership](../explanation/ownership.md). |
| Registry | The runtime's name-to-adapter map; dispatch is an explicit registry, not inheritance. |
| Inline / linked | The two modes for delivering the CSS and runtime (embedded in the document, or referenced by URL). |
| Hydration | Filling a server-rendered page with interactive islands after load, into boxes that already hold their final geometry. |
