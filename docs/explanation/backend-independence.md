# Explanation: backend independence

Backend independence is a property the package preserves, not a feature it adds. This page explains the rule that produces it and the consequences that follow.

## The rule

`render_shell` returns a `str` and imports no web-framework type. Because the output is a plain string, any host can serve it, and the integration is a one-liner that lives outside the package:

```python
# Starlette   HTMLResponse(render_shell(shell))
# Flask       return render_shell(shell)
# SSG         path.write_text(render_shell(shell))
# CLI         print(render_shell(shell))
```

Nothing in the package knows which of these will run. The framework coupling lives entirely in the one line at the host's edge.

## Two delivery modes

The CSS and JavaScript runtime reach the page in one of two modes.

**Inline.** The renderer embeds the stylesheet and runtime in the document. The output is a single self-contained file that runs with no host at all. This is the mode for generated files, emails, and anything opened directly.

**Linked.** The renderer references the assets by URL for a host to serve and cache. This is the mode when a host serves many pages and should cache the assets across them, or when a strict Content-Security-Policy forbids inline `<style>` and `<script>`.

The two modes are the same string-output rule seen from both sides: the bytes either travel with the document or are fetched alongside it. Neither mode couples the package to a backend.

## How server data enters a page

Application data reaches an island in one of two ways.

Through `props`, serialized into the descriptor at render time. The server computes a value and hands it to the island as JSON.

Through the island fetching at runtime. The adapter calls the network itself once it has mounted.

Either way the package stays pure. Only the application is coupled to a backend, and only through the descriptor boundary.

## The payoff: the package documents itself

Because rendering needs no host, switchboard-ui can render its own sandbox, storybook, and guides to static HTML and host the result anywhere. It demonstrates its own behavior with its own output. The bundled demo is the first instance of this: a page built by the same `Shell` and `render_shell` an application would use, rendered to a self-contained file by the CLI. See [Render the demo and docs](../how-to/render-demo-and-docs.md).
