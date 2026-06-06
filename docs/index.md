# switchboard-ui documentation

switchboard-ui renders server-side HTML pages that host self-contained, interactive JavaScript **islands**, coordinated through a shared **event bus**. It is pure Python with zero runtime dependencies. The output is a string, so any backend (or none) can serve it.

This documentation follows the [Diátaxis](https://diataxis.fr/) framework, which separates four kinds of material by the need each one serves.

## Tutorials

Learning-oriented lessons that take you through a working example step by step.

| Doc | Description |
|---|---|
| [Getting started](tutorials/getting-started.md) | Render your first shell, place an island, and watch two islands talk over the bus. |

## How-to guides

Task-oriented recipes for a specific job.

| Doc | Description |
|---|---|
| [Serve rendered HTML](how-to/serve-rendered-html.md) | Hand the output to a backend, write a static file, or serve the two assets in linked mode. |
| [Write an island adapter](how-to/write-an-island-adapter.md) | Implement the mount contract and register an adapter. |
| [Render the demo and docs](how-to/render-demo-and-docs.md) | Use the CLI to build static HTML, including the package documenting itself. |

## Reference

Information-oriented description of every surface.

| Doc | Description |
|---|---|
| [Page model](reference/page-model.md) | `Island`, `Frame`, `Slot`, `Shell`, `Document`, `Region`, `REGIONS`. |
| [Rendering](reference/rendering.md) | `render_shell`, `render_document`, `render_frame`, `render_island`, `RuntimeMode`. |
| [The shell layout](reference/shell-layout.md) | The nine-region preset: its regions, flex CSS contract, and tokens. |
| [The browser runtime](reference/browser-runtime.md) | `window.switchboard`, the bus, the registry, the mount loop. |
| [The CLI](reference/cli.md) | The `switchboard-ui` command. |
| [Glossary](reference/glossary.md) | The vocabulary in one table. |

## Explanation

Understanding-oriented background on why the package is shaped the way it is.

| Doc | Description |
|---|---|
| [Architecture](explanation/architecture.md) | Islands, the event bus, and the one-descriptor-three-consumers spine. |
| [Backend independence](explanation/backend-independence.md) | Why the output is a string, and what that buys. |
| [Layout](explanation/layout.md) | The frame primitive, and the nine-region shell as an example preset. |
| [Design decisions](explanation/design-decisions.md) | The choices made, the alternatives weighed, and the corrections. |

## Where to start

New to the package? Read [Getting started](tutorials/getting-started.md), then [Architecture](explanation/architecture.md).

Integrating it into an app? Read [Serve rendered HTML](how-to/serve-rendered-html.md) and the [Rendering](reference/rendering.md) reference.

Building interactive islands? Read [Write an island adapter](how-to/write-an-island-adapter.md) and the [Browser runtime](reference/browser-runtime.md) reference.

Runnable examples live in [`../examples/`](../examples/README.md): vanilla DOM, Web Components, and React adapters over the same mount contract.
