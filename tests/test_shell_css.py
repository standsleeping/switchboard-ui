"""Bind the CSS region names to the Python region model.

The nine region names live in both ``model.REGIONS`` and ``static/shell.css``
(its ``grid-template-areas`` plus a per-region ``grid-area`` rule). CSS named
grid areas must enumerate the names, so the duplication is intrinsic; the set is
small and stable, so a consistency test is the proportionate guard against drift
rather than a codegen step (GENERATE_INVARIANTS_LINT_VARIATION). Rename, add, or
remove a region in Python and this fails until shell.css agrees.
"""

import re

from switchboard_ui.assets import read_static
from switchboard_ui.model import REGIONS


def test_css_places_every_region() -> None:
    """Each region has a placement class and is placed into its own grid-area."""
    css = read_static("shell.css")
    for region in REGIONS:
        assert f".sb-{region}" in css
        assert f"grid-area: {region}" in css


def test_grid_template_areas_names_exactly_the_regions() -> None:
    """The grid-template-areas block references exactly the nine regions."""
    css = read_static("shell.css")
    block = re.search(r"grid-template-areas:(.*?);", css, re.DOTALL)
    assert block is not None
    assert set(re.findall(r"\b[a-z]+-[a-z]\b", block.group(1))) == set(REGIONS)
