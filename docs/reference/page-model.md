# The page model

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
| `class_` | `str` | `""` | `class` | Extra CSS class(es), appended after `sb-island`. A theming hook the packaged CSS leaves unpainted. |

### Validation

Props are validated at construction. If a value is not JSON-serializable, `Island(...)` raises `ValueError` immediately, naming the island. The failure happens where the bad value was supplied, not deep inside rendering.

```python
Island(name="bad", props={"x": object()})   # raises ValueError: non-JSON-serializable props
```

## `Frame`

A frozen dataclass: a recursive layout node, a one-dimensional flex stack. The general layout primitive; presets such as [`workbench`](workbench.md) arrange frames into ready-made layouts.

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
| `overflow` | [`Overflow`](#overflow) | `"visible"` | What the frame does with content that exceeds it. |
| `class_` | `str` | `""` | Extra CSS class(es), appended after the `sb-frame` classes. A theming hook the packaged CSS leaves unpainted. |

A `Frame` renders (via [`render_frame`](rendering.md#render_frame)) to `<div class="sb-frame sb-frame-{direction} sb-overflow-{overflow}">` (plus any `class_`) with each child rendered in order. Nesting composes to arbitrary depth; the event bus is global, so nesting never affects island coordination.

### `Overflow`

A `Literal` of the three overflow policies. Every frame carries exactly one, emitted from its own value, so scroll ownership is never inherited from an ancestor, assembled from a class string, or won by cascade order.

| Value | Renders | Meaning |
|---|---|---|
| `"visible"` | `overflow: visible` | The browser's own default: content that exceeds the frame is painted outside it, and the page's scrolling reaches it. |
| `"clip"` | `overflow: clip` | Cut off, creating *no* scroll container. Not even the user agent can scroll it to bring a focused descendant into view. |
| `"auto"` | `overflow: auto` plus a stable scrollbar gutter | The frame is a scroll owner: it scrolls its own overflow. |

`clip` rather than `hidden` for containment is deliberate: a `hidden` box is not user-scrollable but stays *programmatically* scrollable, and the user agent uses that to scroll a focused off-screen descendant into view, which surfaces later as an unexplained offset.

`OVERFLOWS` is the tuple of all three, in the order above.

A frame declaring `"clip"` or `"visible"` cannot be scrolled at all, so a viewport-locked page whose descendants are all one of those renders content nothing can reach. Each frame is valid on its own; only the combination is the defect, which is why [`unreachable_content`](analyzer.md#unreachable_content) checks it over the whole tree.

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

The size renders as a `flex` style on the child's own element. A bare child (not wrapped) is content-sized, the browser's default flex item. `Slot` is the sizing mechanism for frames; both presets use it to size their rails.

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
| `body` | `Frame` | required | The root layout, rendered as the page root under the declared root mode. |
| `root` | [`RootMode`](#rootmode) | required | How the root relates to the viewport. |
| `title` | `str` | `"switchboard-ui"` | The document `<title>`. |

### `RootMode`

A `Literal` of the two page shapes. It is **required**, not defaulted: these are different kinds of page rather than a setting with an obvious default, and defaulting one would privilege it while every call site quietly inherited it. Naming it per call site keeps the shape visible in a diff.

| Value | Renders | Meaning |
|---|---|---|
| `"flow"` | `.sb-root-flow`, floored at `100svb` | The browser's normal document. The root is content-sized and the *page* is the primary scroll owner. |
| `"viewport"` | `.sb-root-viewport`, `position: fixed; inset: 0` | The root is locked to the viewport. The page never scrolls; every scroll belongs to a frame that declared `overflow="auto"`. |

The mode is never inferred from content, region names, viewport size, or the presence of a nav.

Choose `"flow"` when the page is something a reader reads top to bottom, and `"viewport"` when it is a tool whose regions hold independent state. [`document_site`](document-site.md) and [`workbench`](workbench.md) each name their own.

`ROOT_MODES` is the tuple of both.

Render with [`render_document`](rendering.md#render_document). Build the document by hand, or from [`document_site`](document-site.md) or [`workbench`](workbench.md).

## `Region` and `REGIONS`

`Region` is a `Literal` of the nine region names.

```python
"head-l", "head-c", "head-r",
"body-l", "body-c", "body-r",
"foot-l", "foot-c", "foot-r"
```

`REGIONS` is the tuple of all nine names in document (row-major) order. They are the placement keys both presets accept.

## `Json`

A type alias for a JSON-serializable value, the shape `props` values must take.

```python
type Json = str | int | float | bool | None | Mapping[str, Json] | Sequence[Json]
```
