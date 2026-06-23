"""Build the showcase document(s) through the public API.

Mirrors the package's own ``demo.py`` build / ``cli.py`` serve split: this module
returns what to render; :mod:`showcase.server` serves and hot-reloads it. Phase 1
grows the component gallery here — each island and preset rendered on a
self-rendered page, the forcing function the theme and components are shaped
against. Its inhabitants so far: the segmented toggle and the color input.

A component ships three parts; the host wires each. :func:`build_showcase` places
the islands, :func:`showcase_scripts` carries the adapters (for ``extra_scripts``),
and :func:`showcase_styles` carries the structural CSS (for ``extra_head``, beside
the theme). That is the same opt-in a real host performs.
"""

from switchboard_ui import Document, Island
from switchboard_ui.components import (
    color_input,
    color_input_scripts,
    color_input_styles,
    segmented,
    segmented_scripts,
    segmented_styles,
)
from switchboard_ui.model import Region
from switchboard_ui.presets import three_column


def build_showcase() -> Document:
    """The showcase page. Phase 1: the component gallery, growing one control at a time."""
    regions: dict[Region, tuple[Island, ...]] = {
        "head-c": (Island(name="brand", initial="switchboard-ui"),),
        "body-c": (
            segmented(
                topic="view:changed",
                options=(
                    ("overview", "Overview"),
                    ("api", "API"),
                    ("examples", "Examples"),
                ),
                value="overview",
                label="View",
            ),
        ),
        "body-r": (color_input(topic="token:accent", value="#5b4bd6", label="Accent"),),
        "foot-c": (Island(name="status", initial="component gallery"),),
    }
    return three_column(regions, title="switchboard-ui showcase")


def showcase_scripts() -> tuple[str, ...]:
    """The island adapters the showcase page registers."""
    return segmented_scripts() + color_input_scripts()


def showcase_styles() -> str:
    """The components' structural CSS, wrapped for ``extra_head`` injection."""
    sheets = "\n".join((segmented_styles(), color_input_styles()))
    return f"<style>{sheets}</style>"
