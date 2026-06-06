# Vanilla DOM example

This example uses plain browser APIs to satisfy the switchboard mount contract.
The Python server renders the shell and inlines `adapters.js`.

```bash
uv run python examples/vanilla/server.py
```

Open <http://127.0.0.1:8001>.

For a quick render check without starting the server:

```bash
uv run python examples/vanilla/server.py --render
```

