# The wiring analyzer

The analyzer is defined in `switchboard_ui.analyze`. It reads rendered HTML and recovers the declared island wiring: which islands are present, which topics connect them, and which declared topics dangle. It executes nothing; the graph comes entirely from the `data-island`, `data-pub`, and `data-sub` attributes the renderer emitted, so the dependency diagram is a property of the page, not of a running session.

The analyzer recovers the *declared* wiring. Keeping an adapter's actual publishes and subscribes in agreement with its island's declaration is the authoring contract the declarations record; see [Write an island adapter](../how-to/write-an-island-adapter.md#declare-the-wiring-on-the-descriptor).

## `wiring`

```python
def wiring(html: str) -> Wiring
```

Parses any renderer output (a full document, a frame, or a single island's mount point) and returns the declared wiring. Elements without `data-island` are ignored.

```python
from switchboard_ui import wiring
from switchboard_ui.demo import build_demo
from switchboard_ui.render import render_document

graph = wiring(render_document(build_demo()))
graph.edges                # (Edge(topic="count:changed", publisher="counter", subscriber="readout"),)
graph.topics               # ("count:changed",)
graph.dangling_publishes   # ()
```

## `Wiring`

A frozen dataclass: the declared wiring of one rendered page or fragment.

| Member | Type | Meaning |
|---|---|---|
| `islands` | `tuple[MountPoint, ...]` | Every mount point, in document order. |
| `topics` | `tuple[str, ...]` | Every declared topic, sorted. |
| `publishers(topic)` | `tuple[str, ...]` | Island names declaring they publish `topic`, in document order, deduplicated. |
| `subscribers(topic)` | `tuple[str, ...]` | Island names declaring they subscribe to `topic`, likewise. |
| `edges` | `tuple[Edge, ...]` | One edge per (topic, publisher, subscriber), ordered by topic then document order, so the graph is stable across runs of the same page. |
| `dangling_publishes` | `tuple[str, ...]` | Topics some island publishes but none subscribes to, sorted. |
| `dangling_subscribes` | `tuple[str, ...]` | Topics some island subscribes to but none publishes, sorted. |

A dangling topic is not necessarily a bug (a control can broadcast for a host page to pick up later, and a page may deliberately render a publisher before its consumers exist), but it is always worth seeing.

## `MountPoint`

A frozen dataclass: one rendered island mount point.

| Field | Type | Meaning |
|---|---|---|
| `name` | `str` | The adapter key (`data-island`). |
| `publishes` | `tuple[str, ...]` | The declared `data-pub` topics. |
| `subscribes` | `tuple[str, ...]` | The declared `data-sub` topics. |

Two mount points may share a `name` (the same adapter mounted twice); each rendered occurrence is one `MountPoint`. Per-topic name lists deduplicate.

## `Edge`

A frozen dataclass: one directed wiring edge. `publisher` announces `topic`; `subscriber` reacts.

| Field | Type |
|---|---|
| `topic` | `str` |
| `publisher` | `str` |
| `subscriber` | `str` |

## See also

- [Architecture](../explanation/architecture.md): the one-descriptor-three-consumers spine this module completes.
- [The browser runtime](browser-runtime.md): the second consumer, which mounts from the same attributes.
