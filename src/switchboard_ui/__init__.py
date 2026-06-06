"""switchboard-ui: server-rendered HTML shells that host interactive islands.

Render a :class:`Shell` (a nine-region three-column frame) full of
:class:`Island` mount descriptors to a backend-free HTML string with
:func:`render_shell`. Each island is a self-contained mini-app that mounts into
a pre-sized region and talks to others over a declarative event bus.
"""

import logging
from importlib.metadata import PackageNotFoundError, version

from switchboard_ui.model import (
    REGIONS,
    Direction,
    Document,
    Frame,
    Island,
    Region,
    Shell,
    Slot,
)
from switchboard_ui.render import (
    RuntimeMode,
    render_document,
    render_frame,
    render_island,
    render_shell,
)

try:
    # The argument is the distribution name, not the import name.
    __version__ = version("switchboard-ui")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"

# A library must not impose logging configuration on the applications that
# import it. Attaching a NullHandler keeps it silent unless the application
# opts in.
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "REGIONS",
    "Direction",
    "Document",
    "Frame",
    "Island",
    "Region",
    "RuntimeMode",
    "Shell",
    "Slot",
    "__version__",
    "render_document",
    "render_frame",
    "render_island",
    "render_shell",
]
