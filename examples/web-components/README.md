# Web Components example

This example wraps the switchboard mount contract around custom elements. The adapter creates the element, passes in `props` and `bus`, then removes the element during teardown.

```bash
uv run python examples/web-components/server.py
```

Open <http://127.0.0.1:8002>.

For a quick render check without starting the server:

```bash
uv run python examples/web-components/server.py --render
```

