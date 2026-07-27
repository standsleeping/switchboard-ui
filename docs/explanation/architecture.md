# Architecture

switchboard-ui exists to put interactive behavior on a server-rendered page without a framework, a build step, or a runtime dependency. This page explains the shape that goal produced.

## Islands and an event bus

A page is static server-rendered HTML. Inside it, certain `<div>` elements are mount points for islands: self-contained mini-applications, each owning its own DOM, lifecycle, and state. This is the islands architecture. The page is mostly static, with interactivity confined to known, independent spots rather than spread across one monolithic application.

Islands are not isolated. They coordinate through an event bus: a single, topic-keyed publish/subscribe channel. An island announces a change by publishing to a topic; other islands react by subscribing to it. The bus is the shared-state layer, and an event-driven channel matches how the browser already works.

Two pieces make islands pluggable without committing to a single technology.

**The mount contract.** Every island adapter is a function `mount(element, props, bus)` that returns a `teardown` function. That one signature is the stable seam. A vanilla-DOM island, a Web Component, and a React component can all satisfy it, and the page and the Python renderer never need to know which kind an island is. The package ships the vanilla adapter; other adapters are later additions that register against the same contract, with no change to the core.

**The registry.** Adapters register by name. The runtime scans the page for mount points, looks each one up by name, and calls its adapter. Dispatch is an explicit registry, not an inheritance hierarchy.

## The spine: one descriptor, three consumers

The central idea is that an island is declarative data, not code. An `Island` value names its adapter, carries the props handed to it, and declares the event topics it publishes and subscribes to. Nothing about an island is expressed as behavior at the Python layer; it is all data.

That single descriptor has three independent consumers.

1. **Python emits it.** The renderer serializes each `Island` into a mount-point `<div>` carrying `data-island`, `data-props`, `data-pub`, and `data-sub`.
2. **The browser runtime mounts and wires from it.** It reads those attributes to mount the right adapter and connect it to the bus.
3. **A static analyzer graphs it.** Because the pub/sub topics are declared as data on the mount point, the wiring between islands is recoverable from the HTML alone, without executing anything. The packaged analyzer (`switchboard_ui.analyze`, see [the wiring analyzer](../reference/analyzer.md)) does exactly this: it reads a rendered page back into islands, edges, and dangling topics. The dependency diagram is a property of the page, not of a running session.

The third consumer is why the topics are declared rather than discovered at runtime. Static analyzability is a requirement, and declaring the wiring as data is what satisfies it.

## Core properties

**Zero runtime dependencies.** The package imports only the Python standard library. This is a defining property. It governs the decisions below it: the renderer is a hand-written HTML builder, and the browser runtime is hand-written vanilla JavaScript with no build step.

**Pure-Python page model.** A page is built from immutable dataclasses (`Island`, `Frame`, `Document`) and turned into HTML by pure functions. State lives in the browser bus at runtime, not in the Python layer; rendering is a pure function of the page model.

**Framework-agnostic islands.** The mount contract lets island internals be anything while the surrounding layout, the descriptor, and the renderer stay constant.

**Declarative wiring.** Island pub/sub is declared on the descriptor, which is what makes the dependency graph drawable by static analysis.

**Distributed as separable packages.** The project is one workspace of three distributions: the core mechanism (zero dependencies, ships only the structural `layout.css`), the theme you opt into (`import switchboard_theme`, which itself depends on the core), and the unpublished development and showcase server. The core declares no dependency on the theme, so the rule that the mechanism never reaches into the theme is a property of the package graph itself, not a test watching for a stray import: the core wheel has no path to the theme's code.

## Deliberate boundaries

Five properties of the design are boundaries rather than omissions. Each is a fact a host can build against.

**The bus is ephemeral.** It stores nothing: no replay, no last value handed to a late subscriber. A message reaches whoever is subscribed at the instant it is published and is gone. An island that needs persistence owns it (for example, writing to localStorage in its own adapter), and a publisher that must reach late subscribers re-announces on a sync topic.

**There is no request/reply.** The bus has one verb: publish. A round trip is composed from two ordinary topics (a `thing:requested`, a `thing:changed`), with both parties as plain publishers and subscribers, so no primitive exists that couples two islands into a call.

**Mounting is eager.** The runtime mounts every island in one scan. There are no hydration directives: no mount-when-visible, mount-when-idle, or media-query deferral.

**The topic namespace is flat and global.** Any island can publish or subscribe to any topic. The `subject:event` naming convention is the collision defense, and the analyzer makes the resulting graph visible; there is no scoping or permission layer.

**Props are a serialization boundary.** They are JSON: validated at construction, embedded in the rendered page, handed to the adapter at mount. Large or live data is never a prop; an island fetches it after mounting. The descriptor carries identity and configuration, not payload.

## See also

- [Backend independence](backend-independence.md): why rendering returns a string.
- [Layout](layout.md): the frame primitive, explicit overflow, and the two nine-region presets.
