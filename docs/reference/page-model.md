# Reference: the page model

The page model is defined in `switchboard_ui.model`. It is built from immutable dataclasses turned into HTML by pure functions.

## `Island`

A frozen dataclass: the declarative mount descriptor for one interactive island.

```python
from switchboard_ui import Island

Island(
    name="counter",
    props={"start": 0},
    publishes=("count:changed",),
    subscribes=(),
    initial="",
)
```

| Field | Type | Default | Rendered as | Meaning |
|---|---|---|---|---|
| `name` | `str` | required | `data-island` | The adapter key the browser registry mounts. |
| `props` | `Mapping[str, Json]` | `{}` | `data-props` | JSON-serializable values handed to the adapter. |
| `publishes` | `tuple[str, ...]` | `()` | `data-pub` | Topics this island emits onto the bus. |
| `subscribes` | `tuple[str, ...]` | `()` | `data-sub` | Topics this island listens for. |
| `initial` | `str` | `""` | inner HTML | Server-rendered content present at first paint. Trusted raw HTML. |

### Validation

Props are validated at construction. If a value is not JSON-serializable, `Island(...)` raises `ValueError` immediately, naming the island. The failure happens where the bad value was supplied, not deep inside rendering.

```python
Island(name="bad", props={"x": object()})   # raises ValueError: non-JSON-serializable props
```

## `Frame`

A frozen dataclass: a recursive layout node, a one-dimensional flex stack. The general layout primitive; presets such as [`three_column`](three-column.md) arrange frames into ready-made layouts.

```python
from switchboard_ui import Frame, Island

Frame(
    direction="column",
    children=(
        Frame(direction="row", children=(Island(name="nav"), Island(name="main"))),
        Island(name="status"),
    ),
)
```

| Field | Type | Default | Meaning |
|---|---|---|---|
| `direction` | `Direction` (`"row"` \| `"column"`) | required | The stack axis. |
| `children` | `tuple[Island \| Frame \| Slot, ...]` | `()` | Ordered children laid out along the axis; islands and frames are content-sized, a `Slot` sizes its child. |

A `Frame` renders (via [`render_frame`](rendering.md#render_frame)) to `<div class="sb-frame sb-frame-{direction}">` with each child rendered in order. Nesting composes to arbitrary depth; the event bus is global, so nesting never affects island coordination.

## `Slot`

A frozen dataclass: a sized position in a [`Frame`](#frame). Wrap a child in a slot to control its main-axis size; a bare child is content-sized.

```python
from switchboard_ui import Frame, Island, Slot

Frame(direction="row", children=(
    Slot(Island(name="nav"), basis="16rem"),   # fixed rail
    Slot(Island(name="main")),                 # flexible, takes the rest
    Island(name="aside"),                      # content-sized
))
```

| Field | Type | Default | Meaning |
|---|---|---|---|
| `child` | `Island \| Frame` | required | The content placed at this position. |
| `basis` | `str \| None` | `None` | A CSS length or token pins the size (`flex: 0 0 <basis>`); `None` grows to share the remaining space (`flex: 1 1 0`). |

The size renders as a `flex` style on the child's own element. A bare child (not wrapped) is content-sized, the browser's default flex item. `Slot` is the sizing mechanism for frames; the [`three_column`](three-column.md) preset uses it to size its rails.

## `Document`

A frozen dataclass: a full page, a root layout frame plus a title.

```python
from switchboard_ui import Document, Frame, Island

Document(
    body=Frame(direction="row", children=(Island(name="nav"), Island(name="main"))),
    title="My app",
)
```

| Field | Type | Default | Meaning |
|---|---|---|---|
| `body` | `Frame` | required | The root layout; rendered as the viewport-locked page root. |
| `title` | `str` | `"switchboard-ui"` | The document `<title>`. |

Render with [`render_document`](rendering.md#render_document). Build the document by hand, or from a preset such as [`three_column`](three-column.md).

## `Region` and `REGIONS`

`Region` is a `Literal` of the nine region names.

```python
"head-l", "head-c", "head-r",
"body-l", "body-c", "body-r",
"foot-l", "foot-c", "foot-r"
```

`REGIONS` is the tuple of all nine names in document (row-major) order. They are the placement keys the [`three_column`](three-column.md) preset accepts.

## `Json`

A type alias for a JSON-serializable value, the shape `props` values must take.

```python
type Json = str | int | float | bool | None | Mapping[str, Json] | Sequence[Json]
```
