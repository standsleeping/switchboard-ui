# switchboard-ui documentation

switchboard-ui renders server-side HTML pages that host self-contained, interactive JavaScript **islands**, coordinated through a shared **event bus**. It is pure Python with zero runtime dependencies. The output is a string, so any backend (or none) can serve it.

This documentation follows the [Diátaxis](https://diataxis.fr/) framework, which separates four kinds of material by the need each one serves.

## Tutorials

Learning-oriented lessons that take you through a working example step by step.

| Doc | Description |
|---|---|
| [Getting started](tutorials/getting-started.md) | Render your first page, place an island, and watch two islands talk over the bus. |

## How-to guides

Task-oriented recipes for a specific job.

| Doc | Description |
|---|---|
| [Build a static documentation site](how-to/build-a-documentation-site.md) | A flowing shell, a nav generated from the filesystem, native anchors, and output you can serve anywhere. |
| [Serve rendered HTML](how-to/serve-rendered-html.md) | Hand the output to a backend, write a static file, or serve the two assets in linked mode. |
| [Write an island adapter](how-to/write-an-island-adapter.md) | Implement the mount contract and register an adapter. |
| [Render the demo and docs](how-to/render-demo-and-docs.md) | Use the CLI to build static HTML, including the package documenting itself. |

## Reference

Information-oriented description of every surface.

| Doc | Description |
|---|---|
| [Page model](reference/page-model.md) | `Island`, `Frame`, `Slot`, `Document`, `Region`, `REGIONS`. |
| [Components](reference/components.md) | The island component set: controls (segmented, slider, popover, modal, color input and picker) and surfaces (table, code block, breadcrumb, collapsible). |
| [Rendering](reference/rendering.md) | `render_document`, `render_frame`, `render_island`, `RuntimeMode`. |
| [The document-site preset](reference/document-site.md) | The flowing nine-region preset: the page scrolls, the rails stick. |
| [The workbench preset](reference/workbench.md) | The viewport-locked nine-region preset: the regions scroll, the page does not. |
| [Browser support](reference/browser-support.md) | The four newer platform features the structural layer uses, and what happens without each. |
| [Theme tokens](reference/tokens.md) | Every `--sb-*` token: color, type, space, radius, border, shadow, the `--sb-fit-*` contract, and density. |
| [The browser runtime](reference/browser-runtime.md) | `window.switchboard`, the bus, the registry, the mount loop. |
| [The wiring analyzer](reference/analyzer.md) | `wiring`: the declared pub/sub graph recovered from rendered HTML. |
| [The CLI](reference/cli.md) | The `switchboard-ui` command. |
| [Glossary](reference/glossary.md) | The vocabulary in one table. |

## Explanation

Understanding-oriented background on why the package is shaped the way it is.

| Doc | Description |
|---|---|
| [Design philosophy](explanation/philosophy.md) | The two founding commitments: align with the browser, and enumerate what leaks. |
| [Architecture](explanation/architecture.md) | Islands, the event bus, and the one-descriptor-three-consumers spine. |
| [Backend independence](explanation/backend-independence.md) | Why the output is a string, and what that buys. |
| [Layout](explanation/layout.md) | The frame primitive, explicit overflow, and the two page shapes. |
| [Scroll ownership and navigation state](explanation/scroll-ownership.md) | What scrolls, why the shape decides who keeps the reader's place, and the one piece of state worth carrying. |
| [Ownership](explanation/ownership.md) | Single ownership across the layers: which layer owns which decision, why that makes a theme replaceable, and how a visual bug traces to one layer. |
| [Seams](explanation/seams.md) | How borders between tiled regions are drawn so each line has a single owner. |
| [Verification](explanation/verification.md) | The four testing rungs, when each one runs, and why a green run cannot be vacuous. |

## Where to start

New to the package? Read [Getting started](tutorials/getting-started.md), then [Architecture](explanation/architecture.md).

Integrating it into an app? Read [Serve rendered HTML](how-to/serve-rendered-html.md) and the [Rendering](reference/rendering.md) reference.

Building interactive islands? Read [Write an island adapter](how-to/write-an-island-adapter.md) and the [Browser runtime](reference/browser-runtime.md) reference.

Runnable examples live in [`../examples/`](../examples/README.md): vanilla DOM, Web Components, and React adapters over the same mount contract.
