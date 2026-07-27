"""switchboard-ui: server-rendered HTML pages that host interactive islands.

Render a layout of :class:`Island` mount descriptors to a backend-free HTML
string. A :class:`Frame` is the general layout primitive and a :class:`Document`
is the page. Two presets arrange islands into a nine-region page:
:func:`document_site` for a flowing document whose page scrolls, and
:func:`workbench` for a viewport-locked shell whose regions scroll. Each island
is a self-contained mini-app that mounts into a region and talks to others over
a declarative event bus.
"""

import logging
from importlib.metadata import PackageNotFoundError, version

from switchboard_ui.analyze import (
    Edge,
    MountPoint,
    Wiring,
    unreachable_content,
    wiring,
)
from switchboard_ui.model import (
    OVERFLOWS,
    REGIONS,
    ROOT_MODES,
    Direction,
    Document,
    Frame,
    Island,
    Overflow,
    Region,
    RootMode,
    Slot,
)
from switchboard_ui.presets import document_site, workbench
from switchboard_ui.render import (
    RuntimeMode,
    render_document,
    render_frame,
    render_island,
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
    "OVERFLOWS",
    "REGIONS",
    "ROOT_MODES",
    "Direction",
    "Document",
    "Edge",
    "Frame",
    "Island",
    "MountPoint",
    "Overflow",
    "Region",
    "RootMode",
    "RuntimeMode",
    "Slot",
    "Wiring",
    "__version__",
    "document_site",
    "render_document",
    "render_frame",
    "render_island",
    "unreachable_content",
    "wiring",
    "workbench",
]
