"""Bind the CSS region names to the Python region model.

The nine region names live in both ``model.REGIONS`` and ``static/shell.css``
(a per-region placement class). The duplication is intrinsic and the set is
small and stable, so a consistency test is the proportionate guard against drift
rather than a codegen step (GENERATE_INVARIANTS_LINT_VARIATION). Rename, add, or
remove a region in Python and this fails until shell.css agrees.
"""

import re

from switchboard_ui.assets import read_static
from switchboard_ui.model import REGIONS


def test_css_places_every_region() -> None:
    """Each region has a placement class in the flex shell."""
    css = read_static("shell.css")
    for region in REGIONS:
        assert f".sb-{region}" in css


def test_css_region_classes_are_exactly_the_regions() -> None:
    """The stylesheet's region-cell classes are exactly the nine regions."""
    css = read_static("shell.css")
    found = set(re.findall(r"\.sb-([a-z]+-[a-z])\b", css))
    assert found == set(REGIONS)


def test_shell_is_composed_of_flex_stacks_not_a_grid() -> None:
    """The shell is built from flex frames; no CSS grid template remains."""
    css = read_static("shell.css")
    assert ".sb-frame" in css
    assert "display: flex" in css
    assert "grid-template-areas" not in css
