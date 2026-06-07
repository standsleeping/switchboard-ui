# React example

This example keeps the switchboard page in Python and lets Vite bundle only the React island adapter.

```bash
cd examples/react
npm install
npm run dev
```

Open the URL printed by Vite, normally <http://127.0.0.1:5173>.

The `predev` and `prebuild` scripts run `build.py`, which writes `index.html` from a `three_column` document. Vite then resolves `src/main.jsx` and bundles React.

Build and preview the production output:

```bash
npm run build
npm run serve
```

For a quick render check without Node:

```bash
uv run python build.py --out /tmp/switchboard-react-example.html
```

