"""Region chrome ships opt-in, because the theme sheet may not dress a region.

``content_column_styles`` paints the center column as a document surface. That
paint cannot live in the generated theme sheet: a region is the mechanism's
structural vocabulary, and ``test_theme_css.py`` holds the sheet to insetting no
structural hook. These guards check the split holds from both sides — the chrome
carries the column's inset, and the sheet still does not.
"""

import switchboard_theme as themes
from switchboard_theme.chrome import content_column_styles
from switchboard_ui import ownership
from switchboard_ui.assets import read_asset


def test_content_column_chrome_dresses_the_center_column() -> None:
    """The chrome owns both inline seams, the column's inset, and the island cap."""
    css = content_column_styles()
    assert ".sb-body-c" in css
    assert "border-inline-start" in css and "border-inline-end" in css
    assert "padding: var(--sb-space-3xl)" in css
    assert "max-inline-size: var(--sb-fit-content-inline)" in css


def test_content_column_chrome_draws_no_horizontal_seam() -> None:
    """Horizontal seams belong to the rows; the column draws only its side edges."""
    css = content_column_styles()
    assert "border-block-start" not in css
    assert "border-block-end" not in css


def test_the_shipped_sheet_still_insets_no_region() -> None:
    """The chrome exists because the sheet may not carry this rule itself."""
    for name in themes.THEMES:
        css = read_asset("switchboard_theme", f"{name}.css")
        for selectors, body in ownership.rules(css):
            structural = any(
                ownership.subject_classes(s) & ownership.STRUCTURAL_HOOKS
                for s in selectors.split(",")
            )
            if not structural:
                continue
            inset = {
                p for p, _ in ownership.declarations(body) if p.startswith("padding")
            }
            assert not inset, (
                f"theme {name!r} insets a structural hook ({selectors.strip()!r}); "
                "region chrome belongs in chrome.py, opted in by the host"
            )
