"""A self-contained demo page that exercises the whole loop.

Python renders a shell with four mount points pre-sized by the grid; the runtime
mounts the interactive islands; clicking the counter publishes ``count:changed``
and the readout (a different region) reacts. The brand and status islands have
no adapter — they are pure server-rendered content needing no JS. The
``data-pub`` / ``data-sub`` attributes alone describe the wiring
(counter -> count:changed -> readout).
"""

from switchboard_ui.assets import read_static
from switchboard_ui.model import Island, Region, Shell


def demo_scripts() -> tuple[str, ...]:
    """The vanilla island adapters registered on the demo page."""
    return (read_static("demo-counter.js"), read_static("demo-readout.js"))


def build_demo() -> Shell:
    """Build the demo :class:`Shell`."""
    regions: dict[Region, tuple[Island, ...]] = {
        "head-c": (Island(name="brand", initial="switchboard-ui"),),
        "body-c": (
            Island(
                name="counter",
                props={"start": 0},
                publishes=("count:changed",),
                initial='<div class="sb-demo-pad"></div>',
            ),
        ),
        "body-r": (Island(name="readout", subscribes=("count:changed",)),),
        "foot-c": (Island(name="status", initial="ready"),),
    }
    return Shell(title="switchboard-ui demo", regions=regions)
