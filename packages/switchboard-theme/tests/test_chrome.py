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
    """The chrome owns the column's inset and the island cap."""
    css = content_column_styles()
    assert ".sb-body-c" in css
    assert "padding: var(--sb-space-3xl)" in css
    assert "max-inline-size: var(--sb-fit-content-inline)" in css


def test_content_column_chrome_draws_no_seam() -> None:
    """Seams are not the chrome's: rows own the horizontals, the sheet the columns."""
    css = content_column_styles()
    assert "border-" not in css


def test_the_shipped_sheet_draws_each_column_seam_only_beside_a_rendered_neighbour() -> (
    None
):
    """The centre draws a seam only where a rail renders on its far side.

    A rail holding no island collapses; a seam drawn against it would be a
    perimeter fragment the rails above and below never continue. The guard is
    the same test the structural sheet collapses by — an island within the
    rail — in both shapes, so the seam and the cell it separates from cannot
    disagree.
    """
    for name in themes.THEMES:
        css = read_asset("switchboard_theme", f"{name}.css")
        seams = {
            selectors.strip(): dict(ownership.declarations(body))
            for selectors, body in ownership.rules(css)
            if "border-inline" in body and ".sb-body-c" in selectors
        }
        assert set(seams) == {
            ".sb-body-l:has(.sb-island) + .sb-body-c",
            ".sb-body-c:has(+ .sb-body-r .sb-island)",
        }
        assert "border-inline-start" in seams[".sb-body-l:has(.sb-island) + .sb-body-c"]
        assert "border-inline-end" in seams[".sb-body-c:has(+ .sb-body-r .sb-island)"]


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


def test_anchor_clearance_composes_the_published_chrome_depth() -> None:
    """An anchored element clears the pinned chrome plus the breathing space.

    The chrome depth is the structural sheet's fact, zero at an end whose rail
    does not render; the fallback covers a page outside a flowing root
    entirely, so a workbench's anchors clear only the breathing space.
    """
    css = content_column_styles()
    assert (
        "scroll-margin-block-start: "
        "calc(var(--sb-chrome-block-start, 0px) + var(--sb-space-md))" in css
    )


def test_the_bleed_is_measured_with_the_columns_own_inset() -> None:
    """A bleeding island widens by exactly the inset the column applies.

    The scroll window then ends at the column's end seam, not mid-air and not
    short of it. One token serves both declarations, so changing the column's
    inset moves the bleed with it.
    """
    css = content_column_styles()
    assert "padding: var(--sb-space-3xl)" in css
    assert "inline-size: calc(100% + var(--sb-space-3xl))" in css
    assert "max-inline-size: none" in css
    assert "inline-size: calc(100% - var(--sb-space-3xl))" in css
