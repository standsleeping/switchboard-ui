# switchboard-theme

The opt-in visual theme for [switchboard-ui](https://github.com/standsleeping/switchboard-ui).

`switchboard-ui` ships structure-only layout CSS plus unpainted hooks and zero
visual style. This distribution *paints* those hooks with its own `--sb-*` token
namespace, delivered through the renderer's `extra_head` injection seam. The
dependency is one-directional: `switchboard-theme` depends on `switchboard-ui`;
the mechanism never depends on the theme.

```python
from switchboard_ui import render_document, three_column
import switchboard_theme

html = render_document(
    three_column(title="hello"),
    extra_head=switchboard_theme.head("default"),
)
```
