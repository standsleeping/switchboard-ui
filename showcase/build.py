"""Build the showcase document(s) through the public API.

Mirrors the package's own ``demo.py`` build / ``cli.py`` serve split: this module
returns what to render; :mod:`showcase.server` serves and hot-reloads it. Phase 0
renders the bundled demo so there is a real live surface on day one;
:func:`build_showcase` is the seam Phase 1's component gallery grows into.
"""

from switchboard_ui import Document
from switchboard_ui.demo import build_demo, demo_scripts


def build_showcase() -> Document:
    """The showcase page. Phase 0: the bundled demo; Phase 1 grows a gallery here."""
    return build_demo()


def showcase_scripts() -> tuple[str, ...]:
    """The island adapters the showcase page registers."""
    return demo_scripts()
