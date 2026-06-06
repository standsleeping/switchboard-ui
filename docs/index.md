# switchboard-ui documentation

switchboard-ui renders server-side HTML pages that host self-contained, interactive JavaScript **islands**, coordinated through a shared **event bus**. It is pure Python with zero runtime dependencies. The output is a string, so any backend (or none) can serve it.

This documentation follows the [Diátaxis](https://diataxis.fr/) framework, which separates four kinds of material by the need each one serves.

## Tutorials

Learning-oriented lessons that take you through a working example step by step.

- [Getting started](tutorials/getting-started.md): render your first shell, place an island, and watch two islands talk over the bus.

## How-to guides

Task-oriented recipes for a specific job.

- [Serve rendered HTML](how-to/serve-rendered-html.md): hand the output to a backend, write a static file, or serve the two assets in linked mode.
- [Write an island adapter](how-to/write-an-island-adapter.md): implement the mount contract and register an adapter.
- [Render the demo and docs](how-to/render-demo-and-docs.md): use the CLI to build static HTML, including the package documenting itself.

## Reference

Information-oriented description of every surface.

- [Page model](reference/page-model.md): `Island`, `Shell`, `Frame`, `Slot`, `Document`, `Region`, `REGIONS`.
- [Rendering](reference/rendering.md): `render_shell`, `render_document`, `render_frame`, `render_island`, `RuntimeMode`.
- [The shell layout](reference/shell-layout.md): the nine regions, the flex CSS contract, the tokens.
- [The browser runtime](reference/browser-runtime.md): `window.switchboard`, the bus, the registry, the mount loop.
- [The CLI](reference/cli.md): the `switchboard-ui` command.
- [Glossary](reference/glossary.md): the vocabulary in one table.

## Explanation

Understanding-oriented background on why the package is shaped the way it is.

- [Architecture](explanation/architecture.md): islands, the event bus, and the one-descriptor-three-consumers spine.
- [Backend independence](explanation/backend-independence.md): why the output is a string, and what that buys.
- [Layout](explanation/layout.md): the shell as invariant, the islands as variable.
- [Design decisions](explanation/design-decisions.md): the choices made, the alternatives weighed, and the corrections.

## Where to start

New to the package: read [Getting started](tutorials/getting-started.md), then [Architecture](explanation/architecture.md).

Integrating it into an app: read [Serve rendered HTML](how-to/serve-rendered-html.md) and the [Rendering](reference/rendering.md) reference.

Building interactive islands: read [Write an island adapter](how-to/write-an-island-adapter.md) and the [Browser runtime](reference/browser-runtime.md) reference.
