"""A self-contained demo page that exercises the whole loop.

Python builds a three-column page with four mount points; the runtime mounts the
interactive islands; clicking the counter publishes ``count:changed`` and the
readout (a different region) reacts. The brand and status islands have no
adapter: they are pure server-rendered content needing no JS. The ``data-pub`` /
``data-sub`` attributes alone describe the wiring
(counter -> count:changed -> readout).

The interactive islands carry server-rendered ``initial`` markup, the same
pattern every packaged component follows: the button and the readout are
present and correctly sized at first paint, and the adapters enhance them in
place rather than building DOM at mount time.
"""

from switchboard_ui.assets import read_static
from switchboard_ui.model import Document, Island, Region
from switchboard_ui.presets import three_column


def demo_scripts() -> tuple[str, ...]:
    """The vanilla island adapters registered on the demo page."""
    return (read_static("demo-counter.js"), read_static("demo-readout.js"))


def build_demo() -> Document:
    """Build the demo page from the :func:`three_column` preset."""
    start = 0
    regions: dict[Region, tuple[Island, ...]] = {
        "head-c": (Island(name="brand", initial="switchboard-ui"),),
        "body-c": (
            Island(
                name="counter",
                props={"start": start},
                publishes=("count:changed",),
                initial=f'<button class="sb-demo-btn">count: {start}</button>',
            ),
        ),
        "body-r": (
            Island(
                name="readout",
                subscribes=("count:changed",),
                initial='<div class="sb-demo-readout">waiting for a click...</div>',
            ),
        ),
        "foot-c": (Island(name="status", initial="ready"),),
    }
    return three_column(regions, title="switchboard-ui demo")
