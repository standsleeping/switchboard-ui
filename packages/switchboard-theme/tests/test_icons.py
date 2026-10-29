"""The icon set: one closed vocabulary, one file per glyph, one decorative renderer.

The name type, the curated metadata, and the files on disk must describe the same set, so a glyph added in one place and forgotten in another fails here. Each shipped file must also keep the contract both renderers rely on: a ``viewBox`` and no intrinsic size (the CSS sizes the glyph) and ``currentColor`` paint (the text colors it).
"""

from importlib.resources import files

import pytest

from switchboard_theme.icons import (
    CATEGORY_GUIDANCE,
    ICON_CATEGORIES,
    ICON_NAMES,
    ICONS,
    icon,
    icon_styles,
)
from switchboard_ui import ownership
from switchboard_ui.assets import read_asset

from .htmlprobe import elements
from .ownership_policy import is_forbidden


def test_names_metadata_and_files_describe_the_same_set() -> None:
    """Every name has exactly one metadata entry and one SVG file, and nothing else does."""
    entries = [entry.name for entry in ICONS]
    assert len(entries) == len(set(entries)), "a glyph has two metadata entries"
    assert set(entries) == set(ICON_NAMES)
    shipped = {
        item.name.removesuffix(".svg")
        for item in (files("switchboard_theme") / "static" / "icons").iterdir()
        if item.name.endswith(".svg")
    }
    assert shipped == set(ICON_NAMES)


def test_names_are_alphabetical() -> None:
    """The name type lists the glyphs in the order of the files on disk."""
    assert list(ICON_NAMES) == sorted(ICON_NAMES)


def test_entries_are_grouped_in_category_order() -> None:
    """The curated entries run category by category in grouping order, none empty."""
    order = [ICON_CATEGORIES.index(entry.category) for entry in ICONS]
    assert order == sorted(order)
    assert set(order) == set(range(len(ICON_CATEGORIES)))


def test_every_category_has_guidance_in_grouping_order() -> None:
    """The guidance mapping covers each category once, keyed in grouping order."""
    assert tuple(CATEGORY_GUIDANCE) == ICON_CATEGORIES
    assert all(CATEGORY_GUIDANCE.values())
    assert all(entry.guidance for entry in ICONS)


def test_every_shipped_glyph_is_unsized_and_paints_in_current_color() -> None:
    """Each file keeps its viewBox, drops width and height, and paints in currentColor."""
    for name in ICON_NAMES:
        markup = read_asset("switchboard_theme", f"icons/{name}.svg")
        (tag, attrs), *_ = elements(markup)
        assert tag == "svg", name
        assert attrs.get("viewbox") == "0 0 15 15", name
        assert "width" not in attrs and "height" not in attrs, name
        assert 'fill="currentColor"' in markup, name


def test_icon_renders_a_decorative_classed_svg() -> None:
    """The root carries the sizing hook and is hidden from assistive tech and focus."""
    (tag, attrs), *children = elements(icon("check"))
    assert tag == "svg"
    assert attrs["class"] == "sb-icon"
    assert attrs["aria-hidden"] == "true"
    assert attrs["focusable"] == "false"
    assert attrs["viewbox"] == "0 0 15 15"
    assert [child_tag for child_tag, _ in children] == ["path"]


def test_every_glyph_renders() -> None:
    """Each name renders exactly one classed root; the shipped markup carries no class of its own."""
    for name in ICON_NAMES:
        html = icon(name)
        assert html.startswith('<svg class="sb-icon"'), name
        assert html.count("class=") == 1, name


def test_icon_rejects_an_unknown_name_naming_it() -> None:
    """An untyped caller passing a name outside the set fails at the call."""
    with pytest.raises(ValueError, match="unknown icon 'sparkles'"):
        icon("sparkles")  # type: ignore[arg-type]


def test_icon_styles_size_the_glyph_to_the_text() -> None:
    """The glyph is a 1em square that never shrinks in a flex row and paints in the text color."""
    block = icon_styles()
    assert block.startswith("<style>")
    assert block.endswith("</style>")
    css = block.removeprefix("<style>").removesuffix("</style>")
    rules = {
        selectors.strip(): dict(ownership.declarations(body))
        for selectors, body in ownership.rules(css)
    }
    assert rules == {
        ".sb-icon": {
            "inline-size": "1em",
            "block-size": "1em",
            "flex-shrink": "0",
            "fill": "currentColor",
        }
    }


def test_icon_styles_neither_position_nor_space() -> None:
    """The glyph's CSS keeps the theme's rules: no positioning, no transform, no margin."""
    declared = ownership.declared_properties(icon_styles())
    assert not [p for p in declared if is_forbidden(p)]
    assert not ownership.declares(declared, "margin")
