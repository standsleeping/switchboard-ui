"""The registry's two artifacts are generated; this guards both against drift.

``static/default.css`` and ``docs/reference/tokens.md`` must each equal what the
registry renders, so ``tokens.py`` is the single source of truth and neither file
can be hand-edited out of sync with it. If one of these fails, run ``just
generate`` and commit the result.
"""

from pathlib import Path

from switchboard_theme.reference import render_reference
from switchboard_theme.tokens import render_css
from switchboard_ui.assets import read_asset

# The reference page lives in the repository's docs tree, three directories above
# this one (packages/switchboard-theme/tests). Test files are never installed, so
# the path from this file is stable wherever the suite can run at all.
_REFERENCE = Path(__file__).parents[3] / "docs" / "reference" / "tokens.md"


def test_committed_css_matches_the_registry() -> None:
    """The committed default.css is exactly what the registry renders (no drift)."""
    committed = read_asset("switchboard_theme", "default.css")
    assert committed == render_css(), (
        "default.css has drifted from tokens.py; regenerate it with `just generate` "
        "and commit -- the registry is the source of truth, not the CSS"
    )


def test_committed_reference_matches_the_registry() -> None:
    """The committed token reference page is exactly what the registry renders."""
    committed = _REFERENCE.read_text(encoding="utf-8")
    assert committed == render_reference(), (
        "docs/reference/tokens.md has drifted from tokens.py; regenerate it with "
        "`just generate` and commit -- the registry is the source of truth, not the "
        "page. A token missing from the page means it is missing its registry entry, "
        "not its paragraph"
    )
