"""default.css is generated from the token registry; this guards against drift.

The committed CSS must equal ``render_css()`` output, so ``tokens.py`` is the single
source of truth and the file cannot be hand-edited out of sync. If this fails,
regenerate the CSS (the command is in ``tokens.py``'s docstring) and commit it.
"""

from switchboard_theme.tokens import render_css
from switchboard_ui.assets import read_asset


def test_committed_css_matches_the_registry() -> None:
    """The committed default.css is exactly what the registry renders (no drift)."""
    committed = read_asset("switchboard_theme", "default.css")
    assert committed == render_css(), (
        "default.css has drifted from tokens.py; regenerate it (see tokens.py's "
        "docstring) and commit -- the registry is the source of truth, not the CSS"
    )
